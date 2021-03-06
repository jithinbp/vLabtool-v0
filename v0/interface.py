# interface - software stack to support the vLabtool-v0.
#
# Copyright (C) 2015 by Jithin B.P. <jithinbp@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os

from commands_proto import *

import packet_handler

import I2C_class,SPI_class,NRF24L01_class,MCP4728_class,NRF_NODE

from achan import *
from digital_channel import *
import serial,string
import time
import sys

import numpy as np
import math


def connect(**kwargs):
    '''
    If vLabtool hardware is found, returns an instance of 'Interface', else returns None.
    '''
    obj = Interface(**kwargs)
    if obj.H.fd != None:
        return obj
    else:
        print 'Err'
        return None
    



class Interface():
    """
    **Communications library.**

    This class contains methods that can be used to interact with the vLabtool

    Initialization does the following
    
    * connects to tty device
    * loads calibration values.

    .. tabularcolumns:: |p{3cm}|p{11cm}|
    +----------+-----------------------------------------------------------------+
    |Arguments |Description                                                      |
    +==========+=================================================================+
    |timeout   | serial port read timeout. default = 1s                          |
    +----------+-----------------------------------------------------------------+

    >>> from v0 import interface
    >>> I = interface.connect()
    >>> print I
    <interface.Interface instance at 0xb6c0cac>
    

    Once you have instantiated this class,  its various methods will allow access to all the features built
    into the device.


        
    """
    
    def __init__(self,timeout=1.0,**kwargs):
        self.verbose=kwargs.get('verbose',False)
        self.initialArgs = kwargs
        self.generic_name = 'SEELablet'
        
        self.ADC_SHIFTS_LOCATION1=11
        self.ADC_SHIFTS_LOCATION2=12
        self.ADC_POLYNOMIALS_LOCATION=13

        self.DAC_POLYNOMIALS_LOCATION=1
        self.DAC_SHIFTS_PVS1A=14
        self.DAC_SHIFTS_PVS1B=15
        self.DAC_SHIFTS_PVS2A=16
        self.DAC_SHIFTS_PVS2B=17
        self.DAC_SHIFTS_PVS3A=18
        self.DAC_SHIFTS_PVS3B=19


        self.BAUD = 1000000
        self.timebase = 40
        self.MAX_SAMPLES = 10000
        self.samples=self.MAX_SAMPLES
        self.triggerLevel=550
        self.triggerChannel = 0
        self.error_count=0
        self.channels_in_buffer=0
        self.digital_channels_in_buffer=0
        self.data_splitting = kwargs.get('data_splitting',500)


        #--------------------------Initialize communication handler, and subclasses-----------------
        self.__runInitSequence__(**kwargs)
    
    def __runInitSequence__(self,**kwargs):
        self.H = packet_handler.Handler(**kwargs)
        self.connected = self.H.connected
        if not self.H.connected:
            print 'Check hardware connections. Not connected'
            return          
        self.DAC = MCP4728_class.MCP4728(self.H,3.3,0)
        self.analogInputSources={}
        self.allAnalogChannels=allAnalogChannels
        for a in allAnalogChannels:self.analogInputSources[a]=analogInputSource(a)
        

        #-------Check for calibration data. And process them if found---------------
        if kwargs.get('load_calibration',True):
            polynomials = self.read_bulk_flash(self.ADC_POLYNOMIALS_LOCATION,2048)
            polyDict={}
            if polynomials[:8]=='VLABTOOL':
                self.__print__('ADC calibration found...')
                import struct
                adc_shifts = self.read_bulk_flash(self.ADC_SHIFTS_LOCATION1,2048)+self.read_bulk_flash(self.ADC_SHIFTS_LOCATION2,2048)
                adc_shifts = [ord(a) for a in adc_shifts]
                self.__print__('ADC INL correction table loaded.')
                inl_slope_intercept = polynomials.split('STOP')[2]
                dac_slope_intercept = polynomials.split('STOP')[1]
                slopes_offsets=polynomials.split('STOP')[0]
                for a in slopes_offsets.split('>|')[1:]:
                    S= a.split('|<')
                    self.__print__( '>>>>>>',S[0])
                    cals=S[1]
                    polyDict[S[0]]=[]
                    for b in range(len(cals)/16):
                        poly=struct.unpack('4f',cals[b*16:(b+1)*16])
                        self.__print__( b,poly)
                        polyDict[S[0]].append(poly)

                for a in dac_slope_intercept.split('>|')[1:]:
                    S= a.split('|<')
                    NAME = S[0][:4]
                    self.__print__( '>>>>>>',NAME)
                    fits = struct.unpack('6f',S[1])
                    slope=fits[0];intercept=fits[1]
                    fitvals = fits[2:]
                    if NAME in ['PVS1','PVS2','PVS3']:
                        DACX=np.linspace(self.DAC.CHANS[NAME].range[0],self.DAC.CHANS[NAME].range[1],4096)
                        if NAME=='PVS1':OFF=self.read_bulk_flash(self.DAC_SHIFTS_PVS1A,2048)+self.read_bulk_flash(self.DAC_SHIFTS_PVS1B,2048)
                        elif NAME=='PVS2':OFF=self.read_bulk_flash(self.DAC_SHIFTS_PVS2A,2048)+self.read_bulk_flash(self.DAC_SHIFTS_PVS2B,2048)
                        elif NAME=='PVS3':OFF=self.read_bulk_flash(self.DAC_SHIFTS_PVS3A,2048)+self.read_bulk_flash(self.DAC_SHIFTS_PVS3B,2048)

                        OFF = np.array([ord(data) for data in OFF])
                        fitfn = np.poly1d(fitvals)
                        YDATA = fitfn(DACX) - (OFF*slope+intercept)
                        LOOKBEHIND = 100;LOOKAHEAD=100                      
                        OFF=np.array([np.argmin(np.fabs(YDATA[max(B-LOOKBEHIND,0):min(4095,B+LOOKAHEAD)]-DACX[B]) )- (B-max(B-LOOKBEHIND,0)) for B in range(0,4096)])
                        self.DAC.load_calibration(NAME,OFF)
                
                inl_slope_intercept=struct.unpack('2f',inl_slope_intercept)
                for a in self.analogInputSources:
                    self.analogInputSources[a].loadCalibrationTable(adc_shifts,inl_slope_intercept[0],inl_slope_intercept[1])
                    if a in polyDict:
                        self.analogInputSources[a].loadPolynomials(polyDict[a])
                        self.analogInputSources[a].calibrationReady=True
                        self.analogInputSources[a].regenerateCalibration()
                
                self.__print__( polynomials.split('>|')[0])
                
        
        self.digital_channel_names=['ID1','ID2','ID3','ID4','-','CH1','Fin']
        self.allDigitalChannels = ['ID1','ID2','ID3','ID4','Fin']
        self.dchans=[digital_channel(a) for a in range(4)]
        #This array of four instances of digital_channel is used to store data retrieved from the
        #logic analyzer section of the device.  It also contains methods to generate plottable data
        #from the original timestamp arrays.
        
        self.streaming=False
        self.achans=[analogAcquisitionChannel(a) for a in ['CH1','CH2','CH3','MIC']]
        
        self.gain_values=[1,2,4,5,8,10,16,32]
        self.buff=np.zeros(10000)

        self.I2C = I2C_class.I2C(self.H)
        #self.I2C.pullSCLLow(5000)
        
        self.SPI = SPI_class.SPI(self.H)
        
        self.SPI.set_parameters(1,7,1,0)
        self.NRF = NRF24L01_class.NRF24L01(self.H)

        for a in ['CH1','CH2']: self.set_gain(a,0)
        self.SOCKET_CAPACITANCE = 42e-12
        time.sleep(0.001)


    def __print__(self,*args):
        if self.verbose:
            for a in args:
                print a,
            print

    def __del__(self):
        print 'closing port'
        try:
            self.H.fd.close()
        except:
            pass

    def get_version(self):
        """
        Returns the version string of the device
        format: LTS-......
        """
        return self.H.get_version(self.H.fd)
    
    def getRadioLinks(self):
        return self.NRF.get_nodelist()

    def newRadioLink(self,**args):
        '''

        .. tabularcolumns:: |p{3cm}|p{11cm}|

        ============== ==============================================================================
        **Arguments**  Description   
        ============== ==============================================================================
        \*\*Kwargs     Keyword Arguments 
        address        Address of the node. a 24 bit number. Printed on the nodes.\n
                       can also be retrieved using :py:meth:`~NRF24L01_class.NRF24L01.get_nodelist`
        ============== ==============================================================================


        :return: :py:meth:`~NRF_NODE.RadioLink`

        
        '''
        return NRF_NODE.RadioLink(self.NRF,**args)
    #-------------------------------------------------------------------------------------------------------------------#

    #|================================================ANALOG SECTION====================================================|
    #|This section has commands related to analog measurement and control. These include the oscilloscope routines,     |
    #|voltmeters, ammeters, and Programmable voltage sources.                               |
    #-------------------------------------------------------------------------------------------------------------------#

    def reconnect(self,**kwargs):
        '''
        Attempts to reconnect to the device in case of a commmunication error or accidental disconnect.
        
        '''
        self.H.reconnect(**kwargs)
        
    def capture1(self,ch,ns,tg,*args):
        """
        Blocking call that fetches an oscilloscope trace from the specified input channel
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        ch              Channel to select as input. ['CH1'..'CH3','SEN']
        ns              Number of samples to fetch. Maximum 10000
        tg              Timegap between samples in microseconds
        ==============  ============================================================================================

        .. figure:: ../images/capture1.png
            :width: 11cm
            :align: center
            :alt: alternate text
            :figclass: align-center
            
            A sine wave captured and plotted.
        
        Example
        
        >>> from pylab import *
        >>> from v0 import interface
        >>> I=interface.connect()
        >>> x,y = I.capture1('CH1',3200,1)
        >>> plot(x,y)
        >>> show()
                
        
        :return: Arrays X(timestamps),Y(Corresponding Voltage values)
        
        """
        return self.capture_fullspeed(ch,ns,tg,*args)

    def capture2(self,ns,tg):
        """
        Blocking call that fetches oscilloscope traces from CH1,CH2
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        ns              Number of samples to fetch. Maximum 5000
        tg              Timegap between samples in microseconds
        ==============  ============================================================================================

        .. figure:: ../images/capture2.png
            :width: 11cm
            :align: center
            :alt: alternate text
            :figclass: align-center
            
            Two sine waves captured and plotted.

        Example 
    
        >>> from pylab import *
        >>> from Labtools import interface
        >>> I=interface.Interface()
        >>> x,y1,y2 = I.capture2(1600,1.25)
        >>> plot(x,y1)              
        >>> plot(x,y2)              
        >>> show()              
        
        :return: Arrays X(timestamps),Y1(Voltage at CH1),Y2(Voltage at CH2)
        
        """
        self.capture_traces(2,ns,tg)
        time.sleep(1e-6*self.samples*self.timebase+.01)
        while not self.oscilloscope_progress()[0]:
            pass
        x,y=self.fetch_trace(1)
        x,y2=self.fetch_trace(2)
        return x,y,y2       

    def capture4(self,ns,tg):
        """
        Blocking call that fetches oscilloscope traces from CH1,CH2,CH3,CH4
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        ns              Number of samples to fetch. Maximum 2500
        tg              Timegap between samples in microseconds. Minimum 1.75uS
        ==============  ============================================================================================

        .. figure:: ../images/capture4.png
            :width: 11cm
            :align: center
            :alt: alternate text
            :figclass: align-center
            
            Four traces captured and plotted.
    
        Example
    
        >>> from pylab import *
        >>> I=interface.Interface()
        >>> x,y1,y2,y3,y4 = I.capture4(800,1.75)
        >>> plot(x,y1)              
        >>> plot(x,y2)              
        >>> plot(x,y3)              
        >>> plot(x,y4)              
        >>> show()              
        
        :return: Arrays X(timestamps),Y1(Voltage at CH1),Y2(Voltage at CH2),Y3(Voltage at CH3),Y4(Voltage at CH4)
        
        """
        self.capture_traces(4,ns,tg)
        time.sleep(1e-6*self.samples*self.timebase+.01)
        while not self.oscilloscope_progress()[0]:
            pass
        x,y=self.fetch_trace(1)
        x,y2=self.fetch_trace(2)
        x,y3=self.fetch_trace(3)
        x,y4=self.fetch_trace(4)
        return x,y,y2,y3,y4     



    def capture_multiple(self,samples,tg,*args):
        """
        Blocking call that fetches oscilloscope traces from a set of specified channels
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        samples         Number of samples to fetch. Maximum 10000/(total specified channels)
        tg              Timegap between samples in microseconds.
        \*args          channel names
        ==============  ============================================================================================
    
        Example
    
        >>> from pylab import *
        >>> I=interface.Interface()
        >>> x,y1,y2,y3,y4 = I.capture_multiple(800,1.75,'CH1','CH2','MIC','SEN')
        >>> plot(x,y1)              
        >>> plot(x,y2)              
        >>> plot(x,y3)              
        >>> plot(x,y4)              
        >>> show()              
        
        :return: Arrays X(timestamps),Y1,Y2 ...
    
        """
        if len(args)==0:
            print 'please specify channels to record'
            return
        tg = int(tg*8)/8.  # Round off the timescale to 1/8uS units
        if(tg<1.5):tg=int(1.5*8)/8.
        total_chans = len(args)

        total_samples = samples*total_chans
        if(total_samples>self.MAX_SAMPLES):
            print 'Sample limit exceeded. 10,000 total'
            total_samples = self.MAX_SAMPLES
            samples = self.MAX_SAMPLES/total_chans

        CHANNEL_SELECTION=0
        for chan in args:
            C=self.analogInputSources[chan].CHOSA
            self.__print__( chan,C)
            CHANNEL_SELECTION|=(1<<C)
        self.__print__( 'selection',CHANNEL_SELECTION,len(args),hex(CHANNEL_SELECTION|((total_chans-1)<<12)))

        self.H.__sendByte__(ADC)
        self.H.__sendByte__(CAPTURE_MULTIPLE)       
        self.H.__sendInt__(CHANNEL_SELECTION|((total_chans-1)<<12) )

        self.H.__sendInt__(total_samples)           #total number of samples to record
        self.H.__sendInt__(int(self.timebase*8))        #Timegap between samples.  8MHz timer clock
        self.H.__get_ack__()
        self.__print__( 'wait')
        time.sleep(1e-6*total_samples*tg+.01)
        self.__print__( 'done')
        data=''
        for i in range(int(total_samples/self.data_splitting)):
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_CHANNEL)
            self.H.__sendByte__(0)  #channel number . starts with A0 on PIC
            self.H.__sendInt__(self.data_splitting)
            self.H.__sendInt__(i*self.data_splitting)
            data+= self.H.fd.read(self.data_splitting*2)        #reading int by int sometimes causes a communication error. this works better.
            self.H.__get_ack__()

        if total_samples%self.data_splitting:
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_CHANNEL)
            self.H.__sendByte__(0)  #channel number starts with A0 on PIC
            self.H.__sendInt__(total_samples%self.data_splitting)
            self.H.__sendInt__(total_samples-total_samples%self.data_splitting)
            data += self.H.fd.read(2*(total_samples%self.data_splitting))       #reading int by int may cause packets to be dropped. this works better.
            self.H.__get_ack__()

        for a in range(total_samples): self.buff[a] = ord(data[a*2])|(ord(data[a*2+1])<<8)
        #self.achans[channel_number-1].yaxis = self.achans[channel_number-1].fix_value(self.buff[:samples])
        yield np.linspace(0,tg*(samples-1),samples)
        for a in range(total_chans):
            yield self.buff[a:total_samples][::total_chans]


    def capture_fullspeed(self,chan,samples,tg,*args):
        """
        Blocking call that fetches oscilloscope traces from a single oscilloscope channel at a maximum speed of 2MSPS
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        chan                channel name 'CH1' / 'CH2' ... 'SEN'
        samples             Number of samples to fetch. Maximum 10000/(total specified channels)
        tg                  Timegap between samples in microseconds. minimum 0.5uS
        \*args              specify if SQR1 must be toggled right before capturing. 'SET_LOW' will set it to 0V,
                            'SET_HIGH' will set it to 5V.  if no arguments are specified, a regular capture will 
                            be executed.
        ==============  ============================================================================================
    
        Example
    
        >>> from pylab import *
        >>> I=interface.Interface()
        >>> x,y = I.capture_fullspeed('CH1',2000,1)
        >>> plot(x,y)               
        >>> show()              
        
        :return: timestamp array ,voltage_value array
    
        """
        tg = int(tg*8)/8.  # Round off the timescale to 1/8uS units
        if(tg<0.5):tg=int(0.5*8)/8.
        if(samples>self.MAX_SAMPLES):
            print 'Sample limit exceeded. 10,000 max'
            samples = self.MAX_SAMPLES

        CHOSA=self.analogInputSources[chan].CHOSA

        self.H.__sendByte__(ADC)
        if 'SET_LOW' in args:
            self.H.__sendByte__(SET_LO_CAPTURE)     
        elif 'SET_HIGH' in args:
            self.H.__sendByte__(SET_HI_CAPTURE)     
        else:
            self.H.__sendByte__(CAPTURE_DMASPEED)       
            
        
        self.H.__sendByte__(CHOSA)

        self.H.__sendInt__(samples)         #total number of samples to record
        self.H.__sendInt__(int(tg*8))       #Timegap between samples.  8MHz timer clock
        self.H.__get_ack__()
        self.__print__( 'wait')
        time.sleep(1e-6*samples*tg+.01)
        self.__print__( 'done')
        return self.__retrieveBufferData__(chan,samples,tg)

    def __retrieveBufferData__(self,chan,samples,tg):
        '''
        ''' 
        data=''
        for i in range(int(samples/self.data_splitting)):
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_CHANNEL)
            self.H.__sendByte__(0)  #channel number . starts with A0 on PIC
            self.H.__sendInt__(self.data_splitting)
            self.H.__sendInt__(i*self.data_splitting)
            data+= self.H.fd.read(self.data_splitting*2)        #reading int by int sometimes causes a communication error. this works better.
            self.H.__get_ack__()

        if samples%self.data_splitting:
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_CHANNEL)
            self.H.__sendByte__(0)  #channel number starts with A0 on PIC
            self.H.__sendInt__(samples%self.data_splitting)
            self.H.__sendInt__(samples-samples%self.data_splitting)
            data += self.H.fd.read(2*(samples%self.data_splitting))         #reading int by int may cause packets to be dropped. this works better.
            self.H.__get_ack__()

        for a in range(samples): self.buff[a] = ord(data[a*2])|(ord(data[a*2+1])<<8)
        #self.achans[channel_number-1].yaxis = self.achans[channel_number-1].fix_value(self.buff[:samples])
        return np.linspace(0,tg*(samples-1),samples),self.analogInputSources[chan].calPoly10(self.buff[:samples])



    def capture_traces(self,num,samples,tg,channel_one_input='CH1',CH123SA=0,**kwargs):
        """
        Instruct the ADC to start sampling. use fetch_trace to retrieve the data

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        =================== ============================================================================================
        **Arguments** 
        =================== ============================================================================================
        num                 Channels to acquire. 1/2/4
        samples             Total points to store per channel. Maximum 3200 total.
        tg                  Timegap between two successive samples (in uSec)
        channel_one_input   map channel 1 to 'CH1' ... 'CH9'
        \*\*kwargs        
        
        \*trigger           Whether or not to trigger the oscilloscope based on the voltage level set by :func:`configure_trigger`
        =================== ============================================================================================


        see :ref:`capture_video`
    
        .. _adc_example:

            .. figure:: ../images/transient.png
                :width: 11cm
                :align: center
                :alt: alternate text
                :figclass: align-center
            
                Transient response of an Inductor and Capacitor in series

            The following example demonstrates how to use this function to record active events.

                * Connect a capacitor and an Inductor in series.
                * Connect CH1 to the spare leg of the inductor. Also Connect OD1 to this point
                * Connect CH2 to the junction between the capacitor and the inductor
                * connect the spare leg of the capacitor to GND( ground )
                * set OD1 initially high using set_state(OD1=1)

            ::

                >>> I.set_state(OD1=1)  #Turn on OD1
                #Arbitrary delay to wait for stabilization
                >>> time.sleep(0.5)                
                #Start acquiring data (2 channels,800 samples, 2microsecond intervals)
                >>> I.capture_traces(2,800,2,trigger=False)
                #Turn off OD1. This must occur immediately after the previous line was executed.
                >>> I.set_state(OD1=0)
                #Minimum interval to wait for completion of data acquisition.
                #samples*timegap*(convert to Seconds)
                >>> time.sleep(800*2*1e-6)
                >>> x,CH1=I.fetch_trace(1)
                >>> x,CH2=I.fetch_trace(2)
                >>> plot(x,CH1-CH2) #Voltage across the inductor                
                >>> plot(x,CH2)     ##Voltage across the capacitor      
                >>> show()              
    
            The following events take place when the above snippet runs
    
            #. The oscilloscope starts storing voltages present at CH1 and CH2 every 2 microseconds
            #. The output OD1 was enabled, and this causes the voltage between the L and C to approach OD1 voltage.
               (It may or may not oscillate)
            #. The data from CH1 and CH2 was read into x,CH1,CH2
            #. Both traces were plotted in order to visualize the Transient response of series LC
        
        :return: nothing
        
        .. seealso::            
            :func:`fetch_trace` , :func:`oscilloscope_progress` , :func:`capture1` , :func:`capture2` , :func:`capture4`
    
        """
        triggerornot=0x80 if kwargs.get('trigger',True) else 0
        self.timebase=tg
        self.timebase = int(self.timebase*8)/8.  # Round off the timescale to 1/8uS units
        CHOSA = self.analogInputSources[channel_one_input].CHOSA
        self.H.__sendByte__(ADC)
        if(num==1):
            if(self.timebase<1.5):self.timebase=int(1.5*8)/8.
            if(samples>self.MAX_SAMPLES):samples=self.MAX_SAMPLES

            self.achans[0].set_params(channel=channel_one_input,length=samples,timebase=self.timebase,resolution=TEN_BIT,source=self.analogInputSources[channel_one_input])
            self.H.__sendByte__(CAPTURE_ONE)        #read 1 channel
            self.H.__sendByte__(CHOSA|triggerornot)     #channelk number

        elif(num==2):
            if(self.timebase<1.75):self.timebase=int(1.75*8)/8.
            if(samples>self.MAX_SAMPLES/2):samples=self.MAX_SAMPLES/2

            self.achans[0].set_params(channel=channel_one_input,length=samples,timebase=self.timebase,resolution=TEN_BIT,source=self.analogInputSources[channel_one_input])
            self.achans[1].set_params(channel='CH2',length=samples,timebase=self.timebase,resolution=TEN_BIT,source=self.analogInputSources['CH2'])
            
            self.H.__sendByte__(CAPTURE_TWO)            #capture 2 channels
            self.H.__sendByte__(CHOSA|triggerornot)             #channel 0 number

        elif(num==3 or num==4):
            if(self.timebase<1.75):self.timebase=int(1.75*8)/8.
            if(samples>self.MAX_SAMPLES/4):samples=self.MAX_SAMPLES/4

            self.achans[0].set_params(channel=channel_one_input,length=samples,timebase=self.timebase,\
            resolution=TEN_BIT,source=self.analogInputSources[channel_one_input])

            for a in range(1,4):
                chans=['NONE','CH2','CH3','MIC']
                self.achans[a].set_params(channel=chans[a],length=samples,timebase=self.timebase,\
                resolution=TEN_BIT,source=self.analogInputSources[chans[a]])
            
            self.H.__sendByte__(CAPTURE_FOUR)           #read 4 channels
            self.H.__sendByte__(CHOSA|(CH123SA<<4)|triggerornot)        #channel number


        self.samples=samples
        self.H.__sendInt__(samples)         #number of samples per channel to record
        self.H.__sendInt__(int(self.timebase*8))        #Timegap between samples.  8MHz timer clock
        self.H.__get_ack__()
        self.channels_in_buffer=num

    def capture_highres_traces(self,channel,samples,tg,**kwargs):
        """
        Instruct the ADC to start sampling. use fetch_trace to retrieve the data

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        =================== ============================================================================================
        **Arguments** 
        =================== ============================================================================================
        channel             channel to acquire data from 'CH1' ... 'CH9'
        samples             Total points to store per channel. Maximum 3200 total.
        tg                  Timegap between two successive samples (in uSec)
        \*\*kwargs        
        
        \*trigger           Whether or not to trigger the oscilloscope based on the voltage level set by :func:`configure_trigger`
        =================== ============================================================================================

        
        :return: nothing
        
        .. seealso::
            
            :func:`fetch_trace` , :func:`oscilloscope_progress` , :func:`capture1` , :func:`capture2` , :func:`capture4`
    
        """
        triggerornot=0x80 if kwargs.get('trigger',True) else 0
        self.timebase=tg
        self.H.__sendByte__(ADC)

        CHOSA = self.analogInputSources[channel].CHOSA
        if(self.timebase<2.8):self.timebase=2.8
        if(samples>self.MAX_SAMPLES):samples=self.MAX_SAMPLES
        self.achans[0].set_params(channel=channel,length=samples,timebase=self.timebase,resolution=TWELVE_BIT,source=self.analogInputSources[channel])

        self.H.__sendByte__(CAPTURE_12BIT)          #read 1 channel
        self.H.__sendByte__(CHOSA|triggerornot)     #channelk number

        self.samples=samples
        self.H.__sendInt__(samples)         #number of samples to read
        self.H.__sendInt__(int(self.timebase*8))        #Timegap between samples.  8MHz timer clock
        self.H.__get_ack__()
        self.channels_in_buffer=1


    
    def fetch_trace(self,channel_number):
        """
        fetches a channel(1-4) captured by :func:`capture_traces` called prior to this, and returns xaxis,yaxis

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel_number  Any of the maximum of four channels that the oscilloscope captured. 1/2/3/4
        ==============  ============================================================================================

        :return: time array,voltage array

        .. seealso::
            
            :func:`capture_traces` , :func:`oscilloscope_progress`

        """
        self.__fetch_channel__(channel_number)
        return self.achans[channel_number-1].get_xaxis(),self.achans[channel_number-1].get_yaxis()
        
    def oscilloscope_progress(self):
        """
        returns the number of samples acquired by the capture routines, and the conversion_done status
        
        :return: conversion done(bool) ,samples acquired (number)

        >>> I.start_capture(1,3200,2)
        >>> print I.oscilloscope_progress()
        (0,46)
        >>> time.sleep(3200*2e-6)
        >>> print I.oscilloscope_progress()
        (1,3200)
        
        .. seealso::
            
            :func:`fetch_trace` , :func:`capture_traces`

        """
        conversion_done=0
        samples=0
        try:
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_STATUS)
            conversion_done = self.H.__getByte__()
            samples = self.H.__getInt__()
            self.H.__get_ack__()
        except:
            print 'disconnected!!'
            #sys.exit(1)
        return conversion_done,samples

    def __fetch_channel__(self,channel_number):
        """
        Fetches a section of data from any channel and stores it in the relevant instance of achan()
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel_number  channel number (1,2,3,4)
        ==============  ============================================================================================
        
        :return: True if successful
        """
        samples = self.achans[channel_number-1].length
        if(channel_number>self.channels_in_buffer):
            print 'Channel unavailable'
            return False
        data=''
        for i in range(int(samples/self.data_splitting)):
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_CHANNEL)
            self.H.__sendByte__(channel_number-1)   #starts with A0 on PIC
            self.H.__sendInt__(self.data_splitting)
            self.H.__sendInt__(i*self.data_splitting)
            data+= self.H.fd.read(self.data_splitting*2)        #reading int by int sometimes causes a communication error. this works better.
            self.H.__get_ack__()

        if samples%self.data_splitting:
            self.H.__sendByte__(ADC)
            self.H.__sendByte__(GET_CAPTURE_CHANNEL)
            self.H.__sendByte__(channel_number-1)   #starts with A0 on PIC
            self.H.__sendInt__(samples%self.data_splitting)
            self.H.__sendInt__(samples-samples%self.data_splitting)
            data += self.H.fd.read(2*(samples%self.data_splitting))         #reading int by int may cause packets to be dropped. this works better.
            self.H.__get_ack__()

        for a in range(samples): self.buff[a] = ord(data[a*2])|(ord(data[a*2+1])<<8)
        self.achans[channel_number-1].yaxis = self.achans[channel_number-1].fix_value(self.buff[:samples])
        return True



    def __fetch_channel_oneshot__(self,channel_number):
        """
        Fetches all data from given channel and stores it in the relevant instance of achan()
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel_number  channel number (1,2,3,4)
        ==============  ============================================================================================
        
        """
        offset=0 
        samples = self.achans[channel_number-1].length
        if(channel_number>self.channels_in_buffer):
            print 'Channel unavailable'
            return False
        self.H.__sendByte__(ADC)
        self.H.__sendByte__(GET_CAPTURE_CHANNEL)
        self.H.__sendByte__(channel_number-1)   #starts with A0 on PIC
        self.H.__sendInt__(samples)
        self.H.__sendInt__(offset)
        data = self.H.fd.read(samples*2)        #reading int by int sometimes causes a communication error. this works better.
        self.H.__get_ack__()
        for a in range(samples): self.buff[a] = ord(data[a*2])|(ord(data[a*2+1])<<8)
        self.achans[channel_number-1].yaxis = self.achans[channel_number-1].fix_value(self.buff[:samples])
        return True


        
    def configure_trigger(self,chan,name,voltage,resolution=10):
        """
        configure trigger parameters for 10-bit capture commands
        The capture routines will wait till a rising edge of the input signal crosses the specified level.
        The trigger will timeout within 8mS, and capture routines will start regardless.
        
        These settings will not be used if the trigger option in the capture routines are set to False
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  =====================================================================================================================
        **Arguments** 
        ==============  =====================================================================================================================
        chan            channel . 0 or 1. corresponding to the channels being recorded by the capture routine(not the analog inputs)
        name            the name of the channel. 'CH1'... 'V+'
        voltage         The voltage level that should trigger the capture sequence(in Volts)
        ==============  =====================================================================================================================

        **Example**
        
        >>> I.configure_trigger(0,1.1)
        >>> I.capture_traces(4,800,2)
        #Unless a timeout occured, the first point of this channel will be close to 1.1Volts
        >>> I.fetch_trace(1)
        #This channel was acquired simultaneously with channel 1, 
        #so it's triggered along with the first
        >>> I.fetch_trace(2)
        
        .. seealso::
            
            :func:`capture_traces` , adc_example_

        """
        self.H.__sendByte__(ADC)
        self.H.__sendByte__(CONFIGURE_TRIGGER)
        self.H.__sendByte__(1<<chan)    #Trigger channel
        
        if resolution==12:
            level = self.analogInputSources[name].voltToCode10(voltage)
            level = np.clip(level,0,4095)
        else:
            level = self.analogInputSources[name].voltToCode10(voltage)
            level = np.clip(level,0,1023)

        if level>(2**resolution - 1):level=(2**resolution - 1)
        elif level<0:level=0

        self.H.__sendInt__(int(level))  #Trigger
        self.H.__get_ack__()

    
                
    def set_gain(self,channel,gain):
        """
        set the gain of the selected PGA
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel         'CH1','CH2'
        gain            (0-7) -> (1x,2x,4x,5x,8x,10x,16x,32x)
        ==============  ============================================================================================
        
        .. note::
            The gain value applied to a channel will result in better resolution for small amplitude signals.
            
            However, values read using functions like :func:`get_average_voltage` or    :func:`capture_traces` 
            will not be 2x, or 4x times the input signal. These are calibrated to return accurate values of the original input signal.
        
        >>> I.set_gain('CH1',7)  #gain set to 32x on CH1

        """
        if self.analogInputSources[channel].gainPGA==None:
            print 'No amplifier exists on this channel :',channel
            return
        
        self.analogInputSources[channel].setGain(self.gain_values[gain])
            
        self.H.__sendByte__(ADC)
        self.H.__sendByte__(SET_PGA_GAIN)
        self.H.__sendByte__(self.analogInputSources[channel].gainPGA) #send the channel
        self.H.__sendByte__(gain) #send the gain
        self.H.__get_ack__()
        return self.gain_values[gain]



    def __calcCHOSA__(self,name):
        name=name.upper()
        source = self.analogInputSources[name]

        if name not in self.allAnalogChannels:
            print 'not a valid channel name. selecting CH1'
            return self.__calcCHOSA__('CH1')

        return source.CHOSA


    def get_average_voltage(self,channel_name,**kwargs):
        """ 
        Return the voltage on the selected channel
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        +------------+-----------------------------------------------------------------------------------------+
        |Arguments   |Description                                                                              |
        +============+=========================================================================================+
        |channel_name| 'CH1','CH2','CH3', 'MIC','IN1','SEN','V+'                                               |
        +------------+-----------------------------------------------------------------------------------------+
        |sleep       | read voltage in CPU sleep mode. not particularly useful. Also, Buggy.                   |
        +------------+-----------------------------------------------------------------------------------------+
        |\*\*kwargs  | Samples to average can be specified. eg. samples=100 will average a hundred readings    |
        +------------+-----------------------------------------------------------------------------------------+


        see :ref:`stream_video`

        Example:
        
        >>> print I.get_average_voltage('CH4')
        1.002
        
        """
        poly = self.analogInputSources[channel_name].calPoly12
        val = np.average([poly(self.__get_raw_average_voltage__(channel_name,**kwargs)) for a in range(kwargs.get('samples',1))])       
        return  val



    def __get_raw_average_voltage__(self,channel_name,**kwargs):
        """ 
        Return the average of 16 raw 10-bit ADC values of the voltage on the selected channel
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================================
        **Arguments** 
        ==============  ============================================================================================================
        channel_name    'CH1', 'CH2', 'CH3', 'MIC', '5V', 'IN1','SEN'
        sleep           read voltage in CPU sleep mode
        ==============  ============================================================================================================

        """
        chosa = self.__calcCHOSA__(channel_name)
        self.H.__sendByte__(ADC)
        self.H.__sendByte__(GET_VOLTAGE_SUMMED)
        if(kwargs.get('sleep',False)):self.H.__sendByte__(chosa|0x80)#sleep mode conversion. buggy
        else:self.H.__sendByte__(chosa) 
        self.H.__getInt__() #2 Zeroes sent by UART. sleep or no sleep :p
        V_sum = self.H.__getInt__()
        self.H.__get_ack__()
        return  V_sum/16. #sum(V)/16.0  #



    #-------------------------------------------------------------------------------------------------------------------#

    #|===============================================DIGITAL SECTION====================================================|   
    #|This section has commands related to digital measurement and control. These include the Logic Analyzer, frequency |
    #|measurement calls, timing routines, digital outputs etc                               |
    #-------------------------------------------------------------------------------------------------------------------#
    def __calcDChan__(self,name):
        """
        accepts a string represention of a digital input ( 'ID1','ID2','ID3','ID4','CH1','Fin' )
        and returns a corresponding number
        """
        
        if name in self.digital_channel_names:
            return self.digital_channel_names.index(name)
        else:
            print ' invalid channel',name,' , selecting ID1 instead '
            return 0
        
    def __get_high_freq__backup__(self,pin):
        """ 
        retrieves the frequency of the signal connected to ID1. >10MHz
        also good for lower frequencies, but avoid using it since
        the ADC cannot be used simultaneously. It shares a TIMER with the ADC.
        
        The input frequency is fed to a 32 bit counter for a period of 100mS.
        The value of the counter at the end of 100mS is used to calculate the frequency.
        

        see :ref:`freq_video`


        .. seealso:: :func:`get_freq`
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments**
        ==============  ============================================================================================
        pin             The input pin to measure frequency from : 'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        ==============  ============================================================================================

        :return: frequency
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(GET_HIGH_FREQUENCY)
        self.H.__sendByte__(self.__calcDChan__(pin))
        scale=self.H.__getByte__()
        val = self.H.__getLong__()
        self.H.__get_ack__()
        return scale*(val)/1.0e-1 #100mS sampling

    def get_high_freq(self,pin):
        """ 
        experimental feature. Attempt to use fewer timers
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(20)
        self.H.__sendByte__(self.__calcDChan__(pin))
        scale=self.H.__getByte__()
        val = self.H.__getLong__()
        self.H.__get_ack__()
        #print hex(val)
        return scale*(val)/1.0e-1 #100mS sampling



    def get_freq(self,channel='Fin',timeout=0.1):
        """
        Frequency measurement on IDx.
        Measures time taken for 16 rising edges of input signal.
        returns the frequency in Hertz

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel         The input to measure frequency from. 'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        timeout         This is a blocking call which will wait for one full wavelength before returning the
                        calculated frequency.
                        Use the timeout option if you're unsure of the input signal.
                        returns 0 if timed out
        ==============  ============================================================================================

        :return float: frequency
        
        
        .. _timing_example:
        
            * connect SQR1 to ID1
            
            >>> I.sqr1(4000,25)
            >>> print I.get_freq('ID1')
            4000.0
            >>> print I.r2r_time('ID1')
            #time between successive rising edges
            0.00025
            >>> print I.f2f_time('ID1')
            #time between successive falling edges
            0.00025
            >>> print I.pulse_time('ID1')
            #may detect a low pulse, or a high pulse. Whichever comes first
            6.25e-05
            >>> I.duty_cycle('ID1')
            #returns wavelength, high time
            (0.00025,6.25e-05)          
        
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(GET_FREQUENCY)
        timeout_msb = int((timeout*64e6))>>16
        self.H.__sendInt__(timeout_msb)
        self.H.__sendByte__(self.__calcDChan__(channel))
        tmt = self.H.__getByte__()
        x=[self.H.__getLong__() for a in range(2)]
        self.H.__get_ack__()
        freq = lambda t: 16*64e6/t if(t) else 0
        #print x,tmt,timeout_msb
        if(tmt):return 0
        return freq(x[1]-x[0])

    def r2r_time(self,channel='ID1',timeout=0.1):
        """ 
        Returns the time interval between two rising edges
        of input signal on ID1

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel         The input to measure time between two rising edges.'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        timeout         Use the timeout option if you're unsure of the input signal time period.
                        returns 0 if timed out
        ==============  ============================================================================================

        :return float: time between two rising edges of input signal
        
        .. seealso:: timing_example_

        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(GET_TIMING)
        timeout_msb = int((timeout*64e6))>>16
        self.H.__sendInt__(timeout_msb)
        self.H.__sendByte__( EVERY_RISING_EDGE<<2 | 2)
        self.H.__sendByte__(self.__calcDChan__(channel))
        tmt = self.H.__getInt__()
        x=[self.H.__getLong__() for a in range(2)]
        self.H.__get_ack__()
        if(tmt >= timeout_msb):return -1
        rtime = lambda t: t/64e6
        y=x[1]-x[0]
        return rtime(y)

    def f2f_time(self,channel='ID1',timeout=0.1):
        """ 
        Returns the time interval between two falling edges
        of input signal on ID1

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel         The input to measure time between two falling edges. 'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        timeout         Use the timeout option if you're unsure of the input signal time period.
                        returns 0 if timed out
        ==============  ============================================================================================

        :return float: time between two falling edges of input signal

        .. seealso:: timing_example_

        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(GET_TIMING)
        timeout_msb = int((timeout*64e6))>>16
        self.H.__sendInt__(timeout_msb)
        self.H.__sendByte__( EVERY_FALLING_EDGE<<2 | 2)
        self.H.__sendByte__(self.__calcDChan__(channel))

        tmt = self.H.__getInt__()
        x=[self.H.__getLong__() for a in range(2)]
        self.H.__get_ack__()
        if(tmt >= timeout_msb):return -1
        rtime = lambda t: t/64e6
        y=x[1]-x[0]
        return rtime(y)

    def DutyCycle(self,channel='ID1',timeout=0.1):
        """ 
        duty cycle measurement on channel
        
        returns wavelength(seconds), and length of first half of pulse(high time)
        
        low time = (wavelength - high time)

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel         The input pin to measure wavelength and high time. 'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        timeout         Use the timeout option if you're unsure of the input signal time period.
                        returns 0 if timed out
        ==============  ============================================================================================

        :return : wavelength,duty cycle

        .. seealso:: timing_example_

        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(GET_DUTY_CYCLE)
        timeout_msb = int((timeout*64e6))>>16
        self.H.__sendInt__(timeout_msb)
        self.H.__sendByte__(self.__calcDChan__(channel)|(self.__calcDChan__(channel)<<4))
        x=[self.H.__getLong__() for a in range(3)]
        edge = self.H.__getByte__()
        tmt = self.H.__getInt__()
        self.H.__get_ack__()
        if edge:   #rising edge has occurred
            y = [x[1]-x[0],x[2]-x[0]]
        else:       #falling edge
            y = [x[2]-x[1],x[2]-x[0]]
        print x,y,edge
        if(tmt >= timeout_msb):return -1,-1
        rtime = lambda t: t/64e6
        params = rtime(y[1]),rtime(y[0])/rtime(y[1])
        return params

    def MeasureInterval(self,channel1,channel2,edge1,edge2,timeout=0.1):
        """ 
        Measures time intervals between two logic level changes on any two digital inputs(both can be the same)

        For example, one can measure the time interval between the occurence of a rising edge on ID1, and a falling edge on ID3.
        If the returned time is negative, it simply means that the event corresponding to channel2 occurred first.
        
        returns the calculated time
        
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel1        The input pin to measure first logic level change
        channel2        The input pin to measure second logic level change
                         -'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        edge1           The type of level change to detect in order to start the timer
                            * 'rising'
                            * 'falling'
                            * 'four rising edges'
        edge2           The type of level change to detect in order to stop the timer
                            * 'rising'
                            * 'falling'
                            * 'four rising edges'
        timeout         Use the timeout option if you're unsure of the input signal time period.
                        returns -1 if timed out
        ==============  ============================================================================================

        :return : time

        .. seealso:: timing_example_
        
        
        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(INTERVAL_MEASUREMENTS)
        timeout_msb = int((timeout*64e6))>>16
        self.H.__sendInt__(timeout_msb)

        self.H.__sendByte__(self.__calcDChan__(channel1)|(self.__calcDChan__(channel2)<<4))

        params =0
        if edge1  == 'rising': params |= 3 
        elif edge1=='falling': params |= 2
        else:              params |= 4

        if edge2  == 'rising': params |= 3<<3 
        elif edge2=='falling': params |= 2<<3
        else:              params |= 4<<3

        self.H.__sendByte__(params)
        A=self.H.__getLong__()
        B=self.H.__getLong__()
        tmt = self.H.__getInt__()
        self.H.__get_ack__()
        #print A,B
        if(tmt >= timeout_msb or B==0):return -1
        rtime = lambda t: t/64e6
        return rtime(B-A+20)

    def pulse_time(self,channel='CH1',timeout=0.1):
        """ 
        pulse time measurement on ID1
        returns pulse length(s) of high pulse or low pulse. whichever occurs first

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        channel         The input pin to measure pulse width from.
                            * 'ID1' , 'ID2', 'ID3', 'ID4', 'Fin'
        timeout         Use the timeout option if you're unsure of the input signal time period.
                        returns 0 if timed out
        ==============  ============================================================================================

        :return float: pulse width in seconds

        .. seealso:: timing_example_

        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(GET_PULSE_TIME)
        timeout_msb = int((timeout*64e6))>>16
        self.H.__sendInt__(timeout_msb)
        self.H.__sendByte__(self.__calcDChan__(channel))
        x=[self.H.__getLong__() for a in range(2)]
        tmt = self.H.__getInt__()
        self.H.__get_ack__()
        if(tmt >= timeout_msb):return -1
        rtime = lambda t: t/64e6
        #print params[0]*1e6,params[1]*1e6
        return rtime(x[1]-x[0])


    def capture_edges1(self,waiting_time=1.,**args):
        """ 
        log timestamps of rising/falling edges on one digital input

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        =================   ======================================================================================================
        **Arguments** 
        =================   ======================================================================================================
        waiting_time          Total time to allow the logic analyzer to collect data.
                            This is implemented using a simple sleep routine, so if large delays will be involved,
                            refer to :func:`start_one_channel_LA` to start the acquisition, and :func:`fetch_LA_channels` to
                            retrieve data from the hardware after adequate time. The retrieved data is stored
                            in the array self.dchans[0].timestamps.
        keyword arguments
        channel             'ID1',...,'ID4'
        trigger_channel     'ID1',...,'ID4'
        channel_mode        acquisition mode\n
                            default value: 3

                            - EVERY_SIXTEENTH_RISING_EDGE = 5
                            - EVERY_FOURTH_RISING_EDGE    = 4
                            - EVERY_RISING_EDGE           = 3
                            - EVERY_FALLING_EDGE          = 2
                            - EVERY_EDGE                  = 1
                            - DISABLED                    = 0
        
        trigger_mode        same as channel_mode.
                                default_value : 3

        =================   ======================================================================================================
        
        :return:  timestamp array in Seconds

        >>> I.capture_edges(0.2,channel='ID1',trigger_channel='ID1',channel_mode=3,trigger_mode = 3)
        #captures rising edges only. with rising edge trigger on ID1
                    
        """
        aqchan = args.get('channel','ID1')
        trchan = args.get('trigger_channel',aqchan)

        aqmode = args.get('channel_mode',3)
        trmode = args.get('trigger_mode',3)

        self.start_one_channel_LA(channel=aqchan,channel_mode=aqmode,trigger_channel=trchan,trigger_mode=trmode)

        time.sleep(waiting_time)

        data=self.get_LA_initial_states()
        tmp = self.fetch_long_data_from_LA(data[0],1)
        #data[4][0] -> initial state
        return tmp/64e6     



    def __start_one_channel_LA_backup__(self,trigger=1,channel='ID1',maximum_time=67,**args):
        """ 
        start logging timestamps of rising/falling edges on ID1

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================== ======================================================================================================
        **Arguments** 
        ================== ======================================================================================================
        trigger            Bool . Enable edge trigger on ID1. use keyword argument edge='rising' or 'falling'
        channel            'ID1',...'LMETER','CH1'
        maximum_time       Total time to sample. If total time exceeds 67 seconds, a prescaler will be used in the reference clock
        kwargs
        triggger_channels  array of digital input names that can trigger the acquisition.eg. trigger= ['ID1','ID2','ID3']
                           will triggger when a logic change specified by the keyword argument 'edge' occurs
                           on either or the three specified trigger inputs.
        edge               'rising' or 'falling' . trigger edge type for trigger_channels.
        ================== ======================================================================================================
        
        :return: Nothing

        """
        self.clear_buffer(0,self.MAX_SAMPLES/2);
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(START_ONE_CHAN_LA)
        self.H.__sendInt__(self.MAX_SAMPLES/4)
        #trigchan bit functions
            # b0 - trigger or not
            # b1 - trigger edge . 1 => rising. 0 => falling
            # b2, b3 - channel to acquire data from. ID1,ID2,ID3,ID4,COMPARATOR
            # b4 - trigger channel ID1
            # b5 - trigger channel ID2
            # b6 - trigger channel ID3

        if ('trigger_channels' in args) and trigger&1:
            trigchans = args.get('trigger_channels',0)
            if 'ID1' in trigchans : trigger|= (1<<4)
            if 'ID2' in trigchans : trigger|= (1<<5)
            if 'ID3' in trigchans : trigger|= (1<<6)
        else:
            trigger |= 1<<(self.__calcDChan__(channel)+4) #trigger on specified input channel if not trigger_channel argument provided

        trigger |= 2 if args.get('edge',0)=='rising' else 0
        trigger |= self.__calcDChan__(channel)<<2

        self.H.__sendByte__(trigger)
        self.H.__get_ack__()
        self.digital_channels_in_buffer = 1
        for a in self.dchans:
            a.prescaler = 0
            a.datatype='long'
            a.length = self.MAX_SAMPLES/4
            a.maximum_time = maximum_time*1e6 #conversion to uS
            a.mode = EVERY_EDGE

        #def start_one_channel_LA(self,**args):
            """ 
            start logging timestamps of rising/falling edges on ID1

            .. tabularcolumns:: |p{3cm}|p{11cm}|
            ================== ======================================================================================================
            **Arguments** 
            ================== ======================================================================================================
            args
            channel             'ID1',...'LMETER','CH1'
            trigger_channel     'ID1',...'LMETER','CH1'

            channel_mode        acquisition mode\n
                                default value: 1(EVERY_EDGE)

                                - EVERY_SIXTEENTH_RISING_EDGE = 5
                                - EVERY_FOURTH_RISING_EDGE    = 4
                                - EVERY_RISING_EDGE           = 3
                                - EVERY_FALLING_EDGE          = 2
                                - EVERY_EDGE                  = 1
                                - DISABLED                    = 0
        
            trigger_edge        1=Falling edge
                                0=Rising Edge
                                -1=Disable Trigger

            ================== ======================================================================================================
        
            :return: Nothing

            """
            self.clear_buffer(0,self.MAX_SAMPLES/2);
            self.H.__sendByte__(TIMING)
            self.H.__sendByte__(START_ONE_CHAN_LA)
            self.H.__sendInt__(self.MAX_SAMPLES/4)
            aqchan = self.__calcDChan__(args.get('channel','ID1'))
            aqmode = args.get('channel_mode',1)
        
            if 'trigger_channel' in args:
                trchan = self.__calcDChan__(args.get('trigger_channel','ID1'))
                tredge = args.get('trigger_edge',0)
                print 'trigger chan',trchan,' trigger edge ',tredge
                if tredge!=-1:
                    self.H.__sendByte__((trchan<<4)|(tredge<<1)|1)
                else:
                    self.H.__sendByte__(0)  #no triggering
            elif 'trigger_edge' in args:
                tredge = args.get('trigger_edge',0)
                if tredge!=-1:
                    self.H.__sendByte__((aqchan<<4)|(tredge<<1)|1)  #trigger on acquisition channel
                else:
                    self.H.__sendByte__(0)  #no triggering
            else:
                self.H.__sendByte__(0)  #no triggering

            self.H.__sendByte__((aqchan<<4)|aqmode)
        
            
            self.H.__get_ack__()
            self.digital_channels_in_buffer = 1

            a = self.dchans[0]
            a.prescaler = 0
            a.datatype='long'
            a.length = self.MAX_SAMPLES/4
            a.maximum_time = 67*1e6 #conversion to uS
            a.mode = args.get('channel_mode',1)
            a.initial_state_override=False
            '''
            if trmode in [3,4,5]:
                a.initial_state_override = 2
            elif trmode == 2:
                a.initial_state_override = 1
            '''




    def start_one_channel_LA(self,**args):
        """ 
        start logging timestamps of rising/falling edges on ID1

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================== ======================================================================================================
        **Arguments** 
        ================== ======================================================================================================
        args
        channel            'ID1',...'LMETER','CH1'
        trigger_channel    'ID1',...'LMETER','CH1'

        channel_mode       acquisition mode.
                           default value: 1

                            - EVERY_SIXTEENTH_RISING_EDGE = 5
                            - EVERY_FOURTH_RISING_EDGE    = 4
                            - EVERY_RISING_EDGE           = 3
                            - EVERY_FALLING_EDGE          = 2
                            - EVERY_EDGE                  = 1
                            - DISABLED                    = 0
        
        trigger_mode       same as channel_mode.
                           default_value : 3

        ================== ======================================================================================================
        
        :return: Nothing

        see :ref:`LA_video`

        """
        self.clear_buffer(0,self.MAX_SAMPLES/2);
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(START_ALTERNATE_ONE_CHAN_LA)
        self.H.__sendInt__(self.MAX_SAMPLES/4)
        aqchan = self.__calcDChan__(args.get('channel','ID1'))
        aqmode = args.get('channel_mode',1)
        trchan = self.__calcDChan__(args.get('trigger_channel','ID1'))
        trmode = args.get('trigger_mode',3)
        
        self.H.__sendByte__((aqchan<<4)|aqmode)
        self.H.__sendByte__((trchan<<4)|trmode)
        
        self.H.__get_ack__()
        self.digital_channels_in_buffer = 1

        a = self.dchans[0]
        a.prescaler = 0
        a.datatype='long'
        a.length = self.MAX_SAMPLES/4
        a.maximum_time = 67*1e6 #conversion to uS
        a.mode = args.get('channel_mode',1)
        if trmode in [3,4,5]:
            a.initial_state_override = 2
        elif trmode == 2:
            a.initial_state_override = 1



    def start_two_channel_LA(self,trigger=1,maximum_time=67):
        """ 
        start logging timestamps of rising/falling edges on ID1,AD2     
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        trigger         Bool . Enable rising edge trigger on ID1
        maximum_time    Total time to sample. If total time exceeds 67 seconds, a prescaler will be used in the reference clock
        ==============  ============================================================================================

        ::

            "fetch_long_data_from_dma(samples,1)" to get data acquired from channel 1
            "fetch_long_data_from_dma(samples,2)" to get data acquired from channel 2
            The read data can be accessed from self.dchans[0 or 1]
        """
        chans=[0,1]
        modes=[1,1]

        self.clear_buffer(0,self.MAX_SAMPLES);
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(START_TWO_CHAN_LA)
        self.H.__sendInt__(self.MAX_SAMPLES/4)
        self.H.__sendByte__(trigger|chans[0])

        self.H.__sendByte__((modes[1]<<4)|modes[0]) #Modes. four bits each
        self.H.__sendByte__((chans[1]<<4)|chans[0]) #Channels. four bits each
        self.H.__get_ack__()
        n=0;
        for a in self.dchans[:2]:
            a.prescaler = 0;a.length = self.MAX_SAMPLES/4;  a.datatype='long';a.maximum_time = maximum_time*1e6 #conversion to uS
            a.mode = modes[n];a.channel_number=chans[n]
            n+=1
        self.digital_channels_in_buffer = 2

    def start_three_channel_LA(self,**args):
        """ 
        start logging timestamps of rising/falling edges on ID1,ID2,ID3

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================== ======================================================================================================
        **Arguments** 
        ================== ======================================================================================================
        args
        trigger_channel     'ID1',...'LMETER','CH1'

        modes               modes for each channel. Array .\n
                            default value: [1,1,1]

                            - EVERY_SIXTEENTH_RISING_EDGE = 5
                            - EVERY_FOURTH_RISING_EDGE    = 4
                            - EVERY_RISING_EDGE           = 3
                            - EVERY_FALLING_EDGE          = 2
                            - EVERY_EDGE                  = 1
                            - DISABLED                    = 0
        
        trigger_mode        same as modes(previously documented keyword argument)
                            default_value : 3

        ================== ======================================================================================================
        
        :return: Nothing

        """
        self.clear_buffer(0,self.MAX_SAMPLES);
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(START_THREE_CHAN_LA)
        self.H.__sendInt__(self.MAX_SAMPLES/4)
        modes = args.get('modes',[1,1,1,1])
        trchan = self.__calcDChan__(args.get('trigger_channel','ID1'))
        trmode = args.get('trigger_mode',3)
        
        self.H.__sendInt__(modes[0]|(modes[1]<<4)|(modes[2]<<8))
        self.H.__sendByte__((trchan<<4)|trmode)
        
        self.H.__get_ack__()
        self.digital_channels_in_buffer = 3

        n=0
        for a in self.dchans[:3]:
            a.prescaler = 0
            a.length = self.MAX_SAMPLES/4
            a.datatype='int'
            a.maximum_time = 1e3 #< 1 mS between each consecutive level changes in the input signal must be ensured to prevent rollover
            a.mode=modes[n]
            if trmode in [3,4,5]:
                a.initial_state_override = 2
            elif trmode == 2:
                a.initial_state_override = 1
            n+=1



    def start_four_channel_LA(self,trigger=1,maximum_time=0.001,mode=[1,1,1,1],**args):
        """ 
        Four channel Logic Analyzer.
        start logging timestamps from a 64MHz counter to record level changes on ID1,ID2,ID3,ID4.
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        trigger         Bool . Enable rising edge trigger on ID1

        maximum_time    Maximum delay expected between two logic level changes.\n
                        If total time exceeds 1 mS, a prescaler will be used in the reference clock
                        However, this only refers to the maximum time between two successive level changes. If a delay larger
                        than .26 S occurs, it will be truncated by modulo .26 S.\n
                        If you need to record large intervals, try single channel/two channel modes which use 32 bit counters
                        capable of time interval up to 67 seconds.

        mode            modes for each channel. List with four elements\n
                        default values: [1,1,1,1]

                        - EVERY_SIXTEENTH_RISING_EDGE = 5
                        - EVERY_FOURTH_RISING_EDGE    = 4
                        - EVERY_RISING_EDGE           = 3
                        - EVERY_FALLING_EDGE          = 2
                        - EVERY_EDGE                  = 1
                        - DISABLED                    = 0

        ==============  ============================================================================================

        :return: Nothing

        .. seealso::

            Use :func:`fetch_long_data_from_LA` (points to read,x) to get data acquired from channel x.
            The read data can be accessed from :class:`~Interface.dchans` [x-1]
        """
        self.clear_buffer(0,self.MAX_SAMPLES);
        prescale = 0
        """
        if(maximum_time > 0.26):
            #print 'too long for 4 channel. try 2/1 channels'
            prescale = 3
        elif(maximum_time > 0.0655):
            prescale = 3
        elif(maximum_time > 0.008191):
            prescale = 2
        elif(maximum_time > 0.0010239):
            prescale = 1
        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(START_FOUR_CHAN_LA)
        self.H.__sendInt__(self.MAX_SAMPLES/4)
        self.H.__sendInt__(mode[0]|(mode[1]<<4)|(mode[2]<<8)|(mode[3]<<12))
        self.H.__sendByte__(prescale) #prescaler
        trigopts=0
        trigopts |= 4 if args.get('trigger_ID1',0) else 0
        trigopts |= 8 if args.get('trigger_ID2',0) else 0
        trigopts |= 16 if args.get('trigger_ID3',0) else 0
        if (trigopts==0): trigger|=4    #select one trigger channel(ID1) if none selected
        trigopts |= 2 if args.get('edge',0)=='rising' else 0
        trigger|=trigopts
        self.H.__sendByte__(trigger)
        self.H.__get_ack__()
        self.digital_channels_in_buffer = 4
        n=0
        for a in self.dchans:
            a.prescaler = prescale
            a.length = self.MAX_SAMPLES/4
            a.datatype='int'
            a.maximum_time = maximum_time*1e6 #conversion to uS
            a.mode=mode[n]
            n+=1



    def get_LA_initial_states(self):
        """ 
        fetches the initial states before the logic analyser started

        :return: chan1 progress,chan2 progress,chan3 progress,chan4 progress,[ID1,ID2,ID3,ID4]. eg. [1,0,1,1]
        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(GET_INITIAL_DIGITAL_STATES)
        initial=self.H.__getInt__()
        A=(self.H.__getInt__()-initial)/2
        B=(self.H.__getInt__()-initial)/2-self.MAX_SAMPLES/4
        C=(self.H.__getInt__()-initial)/2-2*self.MAX_SAMPLES/4
        D=(self.H.__getInt__()-initial)/2-3*self.MAX_SAMPLES/4
        s=self.H.__getByte__()
        s_err=self.H.__getByte__()
        self.H.__get_ack__()
        
        if A==0: A=self.MAX_SAMPLES/4
        if B==0: B=self.MAX_SAMPLES/4
        if C==0: C=self.MAX_SAMPLES/4
        if D==0: D=self.MAX_SAMPLES/4
        
        if A<0: A=0
        if B<0: B=0
        if C<0: C=0
        if D<0: D=0

        #print [(s&1!=0),(s&2!=0),(s&4!=0),(s&8!=0)],[(s_err&1!=0),(s_err&2!=0),(s_err&4!=0),(s&8!=0)]
        return A,B,C,D,[(s&1!=0),(s&2!=0),(s&4!=0),(s&8!=0)]

        
    def fetch_int_data_from_LA(self,bytes,chan=1):
        """ 
        fetches the data stored by DMA. integer address increments

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        bytes:          number of readings(integers) to fetch
        chan:           channel number (1-4)
        ==============  ============================================================================================
        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(FETCH_INT_DMA_DATA)
        self.H.__sendInt__(bytes)
        self.H.__sendByte__(chan-1)

        ss = self.H.fd.read(bytes*2)
        t = np.zeros(bytes*2)
        for a in range(bytes):
            t[a] = ord(ss[0+a*2]) |(ord(ss[1+a*2])<<8)

        self.H.__get_ack__()
        t=np.trim_zeros(t)
        b=1;rollovers=0
        while b<len(t):
            if(t[b]<t[b-1] and t[b]!=0):
                rollovers+=1
                t[b:]+=65535
            b+=1
        return  t

    def fetch_long_data_from_LA(self,bytes,chan=1):
        """ 
        fetches the data stored by DMA. long address increments

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        bytes:          number of readings(long integers) to fetch
        chan:           channel number (1,2)
        ==============  ============================================================================================
        """
        self.H.__sendByte__(TIMING)
        self.H.__sendByte__(FETCH_LONG_DMA_DATA)
        self.H.__sendInt__(bytes)
        self.H.__sendByte__(chan-1)
        ss = self.H.fd.read(bytes*4)
        tmp = np.zeros(bytes)
        for a in range(bytes):
            tmp[a] = ord(ss[0+a*4])|(ord(ss[1+a*4])<<8)|(ord(ss[2+a*4])<<16)|(ord(ss[3+a*4])<<24)
        self.H.__get_ack__()
        tmp = np.trim_zeros(tmp) 
        return tmp


    def fetch_LA_channels(self,trigchan=1):
        """
        reads and stores the channels in self.dchans.

        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        trigchan:       channel number which should be treated as a trigger. (1,2,3,4). Its first timestamp
                        is subtracted from the rest of the channels.
        ==============  ============================================================================================
        """
        data=self.get_LA_initial_states()
        for a in range(4):
            if(self.dchans[a].channel_number<self.digital_channels_in_buffer):self.__fetch_LA_channel__(a,data)
        return True

    def __fetch_LA_channel__(self,channel_number,initial_states):
        s=initial_states[4]
        a=self.dchans[channel_number]
        if a.channel_number>=self.digital_channels_in_buffer:
            print 'channel unavailable'
            return False

        samples = a.length
        if a.datatype=='int':
            tmp = self.fetch_int_data_from_LA(initial_states[a.channel_number],a.channel_number+1)
            a.load_data(s,tmp)
        else:
            tmp = self.fetch_long_data_from_LA(initial_states[a.channel_number*2],a.channel_number+1)
            a.load_data(s,tmp)
        
        #offset=0
        #a.timestamps -= offset
        a.generate_axes()
        return True



    def get_states(self):
        """
        gets the state of the digital inputs. returns dictionary with keys 'ID1','ID2','ID3','ID4'

        >>> print get_states()
        {'ID1': True, 'ID2': True, 'ID3': True, 'ID4': False}
        
        """
        self.H.__sendByte__(DIN)
        self.H.__sendByte__(GET_STATES)
        s=self.H.__getByte__()
        self.H.__get_ack__()
        return {'ID1':(s&1!=0),'ID2':(s&2!=0),'ID3':(s&4!=0),'ID4':(s&8!=0)}

    def get_state(self,input_id):
        """
        returns the logic level on the specified input (ID1,ID2,ID3, or ID4)

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments**    Description
        ==============  ============================================================================================
        input_id        the input channel
                            'ID1' -> state of ID1
                            'ID4' -> state of ID4
        ==============  ============================================================================================

        >>> print I.get_state(I.ID1)
        False
        
        """
        return self.get_states()[input_id]

    def set_state(self,**kwargs):
        """
        
        set the logic level on digital outputs SQR1,SQR2,SQR3,SQR4
        On older units, SQR3,SQR4 were called OD1,OD2. Both mnemonics will work.

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        \*\*kwargs      SQR1,SQR2,SQR3,SQR4
                        states(0 or 1)
        ==============  ============================================================================================

        >>> I.set_state(SQR1=1,SQR2=0)
        sets SQR1 HIGH, SQR2 LOw, but leave SQR3,SQR4 untouched.

        """
        data=0
        if kwargs.has_key('OD1'):
            data|= 0x40|(kwargs.get('OD1')<<2)
        if kwargs.has_key('OD2'):
            data|= 0x80|(kwargs.get('OD2')<<3)
        if kwargs.has_key('SQR1'):
            data|= 0x10|(kwargs.get('SQR1'))
        if kwargs.has_key('SQR2'):
            data|= 0x20|(kwargs.get('SQR2')<<1)
        if kwargs.has_key('SQR3'):
            data|= 0x40|(kwargs.get('SQR3')<<2)
        if kwargs.has_key('SQR4'):
            data|= 0x80|(kwargs.get('SQR4')<<3)
        self.H.__sendByte__(DOUT)
        self.H.__sendByte__(SET_STATE)
        self.H.__sendByte__(data)
        self.H.__get_ack__()



    def __get_capacitor_range__(self,ctime):
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(GET_CAP_RANGE)
        self.H.__sendInt__(ctime) 
        V_sum = self.H.__getInt__()
        self.H.__get_ack__()
        V=V_sum*3.3/16/4095
        C = -ctime*1e-6/1e4/np.log(1-V/3.3)
        return  V,C

    def get_capacitor_range(self):
        """ 
        Charges a capacitor connected to IN1 via a 20K resistor from a 3.3V source for a fixed interval
        Returns the capacitance calculated using the formula Vc = Vs(1-exp(-t/RC))
        This function allows an estimation of the parameters to be used with the :func:`get_capacitance` function.

        """
        t=10
        P=[1.5,50e-12]
        for a in range(4):
            P=list(self.__get_capacitor_range__(50*(10**a)))
            if(P[0]>1.5):
                if a==0 and P[0]>3.28: #pico farads range. Values will be incorrect using this method
                    P[1]=50e-12
                break
        return  P


    def get_capacitance(self):  #time in uS
        """
        measures capacitance of component connected between IN1 and ground

        
        :return: Capacitance (F)

        Constant Current Charging
        
        .. math::

            Q_{stored} = C*V
            
            I_{constant}*time = C*V
            
            C = I_{constant}*time/V_{measured}

        Also uses Constant Voltage Charging via 20K resistor if required.

        """
        GOOD_VOLTS=[2.5,2.8]
        CT=100
        CR=1
        iterations = 0
        while 1:
            V,C = self.__get_capacitance__(CR,0,CT)
            if CT>30000 and V<0.1:
                print 'Capacitance too high for this method'
                return 0
            elif V>GOOD_VOLTS[0] and V<GOOD_VOLTS[1]:
                return C
            elif V<GOOD_VOLTS[0] and V>0.1 and CT<40000:
                if GOOD_VOLTS[0]/V >1.1 and iterations<10:
                    CT=int(CT*GOOD_VOLTS[0]/V)
                    iterations+=1
                    print 'increased CT ',CT
                elif iterations==10:
                    return 0
                else:
                    return C
            elif V<=0.1 and CR<3:
                CR+=1
            elif CR==3:
                return self.get_capacitor_range()[1]

    def __get_capacitance__(self,current_range,trim, Charge_Time):  #time in uS
        self.H.__sendByte__(COMMON)
        currents=[0.55e-3,0.55e-6,0.55e-5,0.55e-4]
        self.H.__sendByte__(GET_CAPACITANCE)
        self.H.__sendByte__(current_range)
        if(trim<0):
            self.H.__sendByte__( int(31-abs(trim)/2)|32)
        else:
            self.H.__sendByte__(int(trim/2))
        self.H.__sendInt__(Charge_Time)
        time.sleep(Charge_Time*1e-6+.02)
        V = 3.3*self.H.__getInt__()/4095
        self.H.__get_ack__()
        Charge_Current = currents[current_range]*(100+trim)/100.0
        if V:C = Charge_Current*Charge_Time*1e-6/V - self.SOCKET_CAPACITANCE
        else: C = 0
        #print 'Current if C=470pF :',V*(470e-12+self.SOCKET_CAPACITANCE)/(Charge_Time*1e-6)
        return V,C


    def get_ctmu_voltage(self,channel,Crange,tgen=1):
        """
        get_ctmu_voltage(5,2)  will activate a constant current source of 5.5uA on IN1 and then measure the voltage at the output.
        If a diode is used to connect IN1 to ground, the forward voltage drop of the diode will be returned. e.g. .6V for a 4148diode.
        
        If a resistor is connected, ohm's law will be followed within reasonable limits
        
        channel=5 for IN1
        
        CRange=0   implies 550uA
        CRange=1   implies 0.55uA
        CRange=2   implies 5.5uA
        CRange=3   implies 55uA
        
        :return: Voltage
        """ 
        if channel=='CAP':channel=5
        
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(GET_CTMU_VOLTAGE)
        self.H.__sendByte__((channel)|(Crange<<5)|(tgen<<7))
        time.sleep(0.001)
        self.H.__getByte__()    #junk byte '0' sent since UART was in IDLE mode and needs to recover.
        #V = [self.H.__getInt__() for a in range(16)]
        #print V
        #v=sum(V)
        v=self.H.__getInt__() #16*voltage across the current source
        self.H.__get_ack__()
        V=3.3*v/15./4096
        return V
            

    def restoreStandalone(self):
        """
        Resets the device, and standalone mode will be enabled if an OLED is connected to the I2C port
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(RESTORE_STANDALONE)

    def resetHardware(self):
        """
        Resets the device, and standalone mode will be enabled if an OLED is connected to the I2C port
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(RESTORE_STANDALONE)

    def read_flash(self,page,location):
        """
        Reads 16 BYTES from the specified location

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================    ============================================================================================
        **Arguments** 
        ================    ============================================================================================
        page                page number. 20 pages with 2KBytes each
        location            The flash location(0 to 63) to read from .
        ================    ============================================================================================

        :return: a string of 16 characters read from the location
        """
        self.H.__sendByte__(FLASH)
        self.H.__sendByte__(READ_FLASH)
        self.H.__sendByte__(page)   #send the page number. 20 pages with 2K bytes each
        self.H.__sendByte__(location)   #send the location
        ss=self.H.fd.read(16)
        self.H.__get_ack__()
        return ss

    def read_bulk_flash(self,page,bytes):
        """
        Reads BYTES from the specified location

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================    ============================================================================================
        **Arguments** 
        ================    ============================================================================================
        page                Block number. 0-20. each block is 2kB.
        bytes               Total bytes to read
        ================    ============================================================================================

        :return: a string of 16 characters read from the location
        """
        self.H.__sendByte__(FLASH)
        self.H.__sendByte__(READ_BULK_FLASH)
        self.H.__sendInt__(bytes)   #send the location
        self.H.__sendByte__(page)
        ss=self.H.fd.read(bytes)
        self.H.__get_ack__()
        return ss


    def write_flash(self,page,location,string_to_write):
        """
        write a 16 BYTE string to the selected location (0-63)

        DO NOT USE THIS UNLESS YOU'RE ABSOLUTELY SURE KNOW THIS!
        YOU MAY END UP OVERWRITING THE CALIBRATION DATA, AND WILL HAVE
        TO GO THROUGH THE TROUBLE OF GETTING IT FROM THE MANUFACTURER AND
        REFLASHING IT.
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================    ============================================================================================
        **Arguments** 
        ================    ============================================================================================
        page                page number. 20 pages with 2KBytes each
        location            The flash location(0 to 63) to write to.
        string_to_write     a string of 16 characters can be written to each location
        ================    ============================================================================================

        """
        while(len(string_to_write)<16):string_to_write+='.'
        self.H.__sendByte__(FLASH)
        self.H.__sendByte__(WRITE_FLASH)    #indicate a flash write coming through
        self.H.__sendByte__(page)   #send the page number. 20 pages with 2K bytes each
        self.H.__sendByte__(location)   #send the location
        self.H.fd.write(string_to_write)
        time.sleep(0.1)
        self.H.__get_ack__()

    def write_bulk_flash(self,location,bytearray):
        """
        write a byte array to the entire flash page. Erases any other data

        DO NOT USE THIS UNLESS YOU'RE ABSOLUTELY SURE KNOW THIS!
        YOU MAY END UP OVERWRITING THE CALIBRATION DATA, AND WILL HAVE
        TO GO THROUGH THE TROUBLE OF GETTING IT FROM THE MANUFACTURER AND
        REFLASHING IT.
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ================    ============================================================================================
        **Arguments** 
        ================    ============================================================================================
        location            Block number. 0-20. each block is 2kB.
        bytearray           Array to dump onto flash. Max size 2048 bytes
        ================    ============================================================================================

        """
        print 'Dumping ',len(bytearray),' bytes into flash'
        self.H.__sendByte__(FLASH)
        self.H.__sendByte__(WRITE_BULK_FLASH)   #indicate a flash write coming through
        self.H.__sendInt__(len(bytearray))  #send the length
        self.H.__sendByte__(location)
        for n in range(len(bytearray)):
            self.H.__sendByte__(bytearray[n])
            #Printer('Bytes written: %d'%(n+1))
        time.sleep(0.2)
        self.H.__get_ack__()




    def get_temperature(self):
        """
        return the processor's temperature
        
        :return: Chip Temperature in degree Celcius
        """ 
        V=self.get_ctmu_voltage(0b11110,3,0)
        return (783.24-V*1000)/1.87
        


    def set_sine1(self,freq):
        """
        Set the frequency of wavegen
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        frequency       Frequency to set on wave generator 1. 
        ==============  ============================================================================================
        
        
        :return: frequency
        """
        if freq<5:
            print 'freq too low'
            return 0        
        elif freq<1100:
            HIGHRES=1
            table_size = 512
        else:
            HIGHRES=0
            table_size = 32

        wavelength = int(round(64e6/freq/table_size))
        freq = (64e6/wavelength/table_size)

        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SET_SINE1)
        self.H.__sendByte__(HIGHRES)    #use larger table for low frequencies
        self.H.__sendInt__(wavelength-1)        
        self.H.__get_ack__()
        return freq



    def set_sine2(self,freq):
        """
        Set the frequency of wavegen
                
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        frequency       Frequency to set on wave generator 1. 
        ==============  ============================================================================================
        
        :return: frequency
        """
        if freq<5:
            print 'freq too low'
            return 0        
        elif freq<1100:
            HIGHRES=1
            table_size = 512
        else:
            HIGHRES=0
            table_size = 32

        wavelength = int(round(64.e6/freq/table_size))
        freq = 64.e6/wavelength/table_size

        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SET_SINE2)
        self.H.__sendByte__(HIGHRES)    #use larger table for low frequencies
        self.H.__sendInt__(wavelength-1)        
        self.H.__get_ack__()

        return freq

    def set_sine_phase(self,freq,phase):
        """
        Set the frequency of wavegen
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        frequency       Frequency to set on both wave generators
        phase           Phase difference between the two. 0-360 degrees
        ==============  ============================================================================================
        
        :return: frequency
        """
        if freq<5:
            print 'freq too low'
            return 0        
        elif freq<1100:
            HIGHRES=1
            table_size = 512
        else:
            HIGHRES=0
            table_size = 32

        wavelength = int(round(64e6/freq/table_size))
        retfreq = 64.e6/wavelength/table_size
        
        phase_coarse = int(table_size*( phase)/360.  )
        phase_fine = int(wavelength*(phase - (phase_coarse)*360./table_size)/(360./table_size))

        phase_coarse += int(table_size*( freq/100.)/360.  ) # PHASE CORRECTION. 

        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SET_BOTH_WG)

        self.H.__sendInt__(wavelength-1)        #not really wavelength. time between each datapoint
        self.H.__sendInt__(wavelength-1)        #not really wavelength. time between each datapoint
        self.H.__sendInt__(phase_coarse)    #table position for phase adjust
        self.H.__sendInt__(phase_fine)      #timer delay / fine phase adjust

        self.H.__sendByte__((HIGHRES<<1)|(HIGHRES))     #use larger table for low frequencies
        self.H.__get_ack__()

        return retfreq


    def load_waveform(self,num,function,span):
        '''
        Load an arbitrary waveform to the waveform generators
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        num             The waveform generator to alter. 1 or 2
        function            A function that will be used to generate the datapoints
        span                the range of values in which to evaluate the given function
        ==============  ============================================================================================
        
        example::
          
          >>> fn = lambda x:abs(x-50)  #Triangular waveform 
          >>> self.I.load_waveform(fn,[0,100])
          #Load triangular wave to wavegen 1
          
          #Load sinusoidal wave to wavegen 2
          >>> self.I.load_waveform(2,np.sin,[0,2*np.pi])

        '''

        x1=np.linspace(span[0],span[1],512+1)[:-1]
        y1=function(x1)
        y1-=min(y1)
        y1/=max(y1)
        y1 = list(np.int16(np.round( 512 - 512*y1 )))

        x2=np.linspace(span[0],span[1],32+1)[:-1]
        y2=function(x2)
        y2-=min(y2)
        y2/=max(y2)

        y2 = list(np.int16(np.round( 64 - 64*y2 )))

        print len(y1),len(y2),min(y1),max(y1)

        self.H.__sendByte__(WAVEGEN)
        if(num==1):self.H.__sendByte__(LOAD_WAVEFORM1)
        elif(num==2):self.H.__sendByte__(LOAD_WAVEFORM2)

        for a in y1:
            self.H.__sendInt__(a)
            time.sleep(0.001)
        for a in y2:
            self.H.__sendByte__(chr(a))
            time.sleep(0.001)
        time.sleep(0.1)
        self.H.__get_ack__()
        
        


    def set_pvs1(self,val):
        """
        Set the voltage on PVS1
        12-bit DAC...  -5V to 5V
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        val             Output voltage on PVS1. -5V to 5V
        ==============  ============================================================================================

        """
        return self.DAC.setVoltage('PVS1',val)

    def set_pvs2(self,val):
        """
        Set the voltage on PVS2.
        12-bit DAC...  0-3.3V
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        val             Output voltage on PVS2. 0-3.3V
        ==============  ============================================================================================
        """
        return self.DAC.setVoltage('PVS2',val)

    def set_pvs3(self,val):
        """
        Set the voltage on PVS3

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        val             Output voltage on PVS3. 0V to 3.3V
        ==============  ============================================================================================

        :return: Actual value set on pvs3
        """
        return self.DAC.setVoltage('PVS3',val)
        
    def set_pcs(self,val):
        """
        Set programmable current source

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        val             Output current on PCS. 0 to 3.3mA. Subject to load resistance. Read voltage on PCS to check.
        ==============  ============================================================================================

        :return: value attempted to set on pcs
        """
        return self.DAC.setVoltage('PCS',val)
        
    def setOnboardLED(self,R,G,B):
        """
        set shade of WS2182 LED on PIC1572 1 RA2
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        R               brightness of red colour 0-255
        G               brightness of green colour 0-255
        B               brightness of blue colour 0-255
        ==============  ============================================================================================
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(SET_ONBOARD_RGB)
        #G=reverse_bits(G);R=reverse_bits(R);B=reverse_bits(B)
        self.H.__sendByte__(B)
        self.H.__sendByte__(R)
        self.H.__sendByte__(G)
        print B,R,G
        time.sleep(0.001)
        self.H.__get_ack__()
        return B,R,G    

    def WS2812B(self,cols):
        """
        set shade of WS2182 LED on SQR1
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        cols                2Darray [[R,G,B],[R2,G2,B2],[R3,G3,B3]...]
                            brightness of R,G,B ( 0-255  )
        ==============  ============================================================================================

        example::
        
            >>> I.WS2812B([[10,0,0],[0,10,10],[10,0,10]])
            #sets red, cyan, magenta to three daisy chained LEDs

        see :ref:`rgb_video`


        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(SET_RGB)
        self.H.__sendByte__(len(cols)*3)
        for col in cols:
            #R=reverse_bits(int(col[0]));G=reverse_bits(int(col[1]));B=reverse_bits(int(col[2]))
            R=col[0];G=col[1];B=col[2];
            self.H.__sendByte__(G); self.H.__sendByte__(R);self.H.__sendByte__(B)
        self.H.__get_ack__()



    def fetch_buffer(self,starting_position=0,total_points=100):
        """
        fetches a section of the ADC hardware buffer
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(RETRIEVE_BUFFER)
        self.H.__sendInt__(starting_position)
        self.H.__sendInt__(total_points)
        for a in range(total_points): self.buff[a]=self.H.__getInt__()
        self.H.__get_ack__()

    def clear_buffer(self,starting_position,total_points):
        """
        clears a section of the ADC hardware buffer
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(CLEAR_BUFFER)
        self.H.__sendInt__(starting_position)
        self.H.__sendInt__(total_points)
        self.H.__get_ack__()

    def start_streaming(self,tg,channel='CH1'):
        """
        Instruct the ADC to start streaming 8-bit data.  use stop_streaming to stop.

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        tg              timegap. 250KHz clock
        channel         channel 'CH1'... 'CH9','IN1','SEN'
        ==============  ============================================================================================

        """
        if(self.streaming):self.stop_streaming()
        
        self.H.__sendByte__(ADC)
        self.H.__sendByte__(START_ADC_STREAMING)
        self.H.__sendByte__(self.__calcCHOSA__(channel))
        self.H.__sendInt__(tg)      #Timegap between samples.  8MHz timer clock
        self.streaming=True

    def stop_streaming(self):
        """
        Instruct the ADC to stop streaming data
        """
        if(self.streaming):
            self.H.__sendByte__(STOP_STREAMING)
            self.H.fd.read(20000)
            self.H.fd.flush()
        else:
            print 'not streaming'
        self.streaming=False

    def sqr1(self,freq,duty_cycle=50,echo=False):
        """
        Set the frequency of sqr1

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        frequency       Frequency
        duty_cycle      Percentage of high time
        ==============  ============================================================================================
        """
        p=[1,8,64,256]
        prescaler=0
        while prescaler<=3:
            wavelength = 64e6/freq/p[prescaler]
            if wavelength<65525: break
            prescaler+=1
        if prescaler==4:
            print 'out of range'
            return 0
        high_time = wavelength*duty_cycle/100.
        if echo:print wavelength,high_time,prescaler
        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SET_SQR1)
        self.H.__sendInt__(int(round(wavelength)))
        self.H.__sendInt__(int(round(high_time)))
        self.H.__sendByte__(prescaler)
        self.H.__get_ack__()

        return 64e6/wavelength/p[prescaler]



    def sqr2(self,freq,duty_cycle):
        """
        Set the frequency of sqr2

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        frequency       Frequency
        duty_cycle      Percentage of high time
        ==============  ============================================================================================
        """
        p=[1,8,64,256]
        prescaler=0
        while prescaler<=3:
            wavelength = 64e6/freq/p[prescaler]
            if wavelength<65525: break
            prescaler+=1
        if prescaler==4:
            print 'out of range'
            return
        high_time = wavelength*duty_cycle/100.
        print wavelength,high_time,prescaler
        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SET_SQR2)
        self.H.__sendInt__(int(round(wavelength)))
        self.H.__sendInt__(int(round(high_time)))
        self.H.__sendByte__(prescaler)
        self.H.__get_ack__()


    def set_sqrs(self,wavelength,phase,high_time1,high_time2,prescaler=1):
        """
        Set the frequency of sqr1,sqr2, with phase shift

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        wavelength      Number of 64Mhz/prescaler clock cycles per wave
        phase           Clock cycles between rising edges of SQR1 and SQR2
        high time1      Clock cycles for which SQR1 must be HIGH
        high time2      Clock cycles for which SQR2 must be HIGH
        prescaler       0,1,2. Divides the 64Mhz clock by 8,64, or 256
        ==============  ============================================================================================
        
        """
        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SET_SQRS)
        self.H.__sendInt__(wavelength)
        self.H.__sendInt__(phase)
        self.H.__sendInt__(high_time1)
        self.H.__sendInt__(high_time2)
        self.H.__sendByte__(prescaler)
        self.H.__get_ack__()

    def sqr4_pulse(self,freq,h0,p1,h1,p2,h2,p3,h3):
        """
        Output one set of phase correlated square pulses on SQR1,SQR2,OD1,OD2 .
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        freq            Frequency in Hertz
        h0              Duty Cycle for SQR1 (0-1)
        p1              Phase shift for SQR2 (0-1)
        h1              Duty Cycle for SQR2 (0-1)
        p2              Phase shift for OD1  (0-1)
        h2              Duty Cycle for OD1  (0-1)
        p3              Phase shift for OD2  (0-1)
        h3              Duty Cycle for OD2  (0-1)
        ==============  ============================================================================================
        
        """
        wavelength = int(64e6/freq)
        wavelength = int(64e6/freq)
        params=0
        if wavelength>0xFFFF00:
            print 'frequency too low.'
            return
        elif wavelength>0x3FFFC0:
            wavelength = int(64e6/freq/256)
            params=3
        elif wavelength>0x7FFF8:
            params=2
            wavelength = int(64e6/freq/64)
        elif wavelength>0xFFFF:
            params=1
            wavelength = int(64e6/freq/8)


        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SQR4)
        self.H.__sendInt__(wavelength)
        self.H.__sendInt__(int(wavelength*h0))

        A1 = int(p1%1*wavelength)
        B1 = int((h1+p1)%1*wavelength)
        A2 = int(p2%1*wavelength)
        B2 = int((h2+p2)%1*wavelength)
        A3 = int(p3%1*wavelength)
        B3 = int((h3+p3)%1*wavelength)

        #print p1,h1,p2,h2,p3,h3
        #print wavelength,int(wavelength*h0),A1,B1,A2,B2,A3,B3
        self.H.__sendInt__(A1)
        self.H.__sendInt__(B1)
        self.H.__sendInt__(A2)
        self.H.__sendInt__(B2)
        self.H.__sendInt__(A3)
        self.H.__sendInt__(B3)
        self.H.__sendByte__(params)
        self.H.__get_ack__()

    def sqr4_continuous(self,freq,h0,p1,h1,p2,h2,p3,h3):
        """
        Initialize continuously running phase correlated square waves on SQR1,SQR2,OD1,OD2
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        freq            Frequency in Hertz
        h0              Duty Cycle for SQR1 (0-1)
        p1              Phase shift for SQR2 (0-1)
        h1              Duty Cycle for SQR2 (0-1)
        p2              Phase shift for OD1  (0-1)
        h2              Duty Cycle for OD1  (0-1)
        p3              Phase shift for OD2  (0-1)
        h3              Duty Cycle for OD2  (0-1)
        ==============  ============================================================================================
        
        """
        wavelength = int(64e6/freq)
        params=0
        if wavelength>0xFFFF00:
            print 'frequency too low.'
            return
        elif wavelength>0x3FFFC0:
            wavelength = int(64e6/freq/256)
            params=3
        elif wavelength>0x7FFF8:
            params=2
            wavelength = int(64e6/freq/64)
        elif wavelength>0xFFFF:
            params=1
            wavelength = int(64e6/freq/8)
        params|= (1<<5)
        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SQR4)
        self.H.__sendInt__(wavelength)
        self.H.__sendInt__(int(wavelength*h0))

        A1 = int(p1%1*wavelength)
        B1 = int((h1+p1)%1*wavelength)
        A2 = int(p2%1*wavelength)
        B2 = int((h2+p2)%1*wavelength)
        A3 = int(p3%1*wavelength)
        B3 = int((h3+p3)%1*wavelength)

        #print p1,h1,p2,h2,p3,h3
        #print wavelength,int(wavelength*h0),A1,B1,A2,B2,A3,B3
        self.H.__sendInt__(A1)
        self.H.__sendInt__(B1)
        self.H.__sendInt__(A2)
        self.H.__sendInt__(B2)
        self.H.__sendInt__(A3)
        self.H.__sendInt__(B3)
        self.H.__sendByte__(params)
        self.H.__get_ack__()



    def map_reference_clock(self,scaler,*args):
        """
        Map the internal oscillator output  to SQR1,SQR2,SQR3,SQR4 or WAVEGEN
        The output frequency is 128/(1<<scaler) MHz
        
        scaler [0-15]
            
            * 0 -> 128MHz
            * 1 -> 64MHz
            * 2 -> 32MHz
            * 3 -> 16MHz
            * .
            * .
            * 15 ->128./32768 MHz

        example::
        
        >>> I.map_reference_clock(2,'SQR1','SQR2')
        
        outputs 32 MHz on SQR1, SQR2 pins
        
        .. note::
            if you change the reference clock for 'wavegen' , the waveform generator resolution and range will also change.
            default frequency for 'wavegen' is 16MHz. Setting to 1MHz will give you 16 times better resolution, but a usable range of
            0Hz to about 100KHz instead of the original 2MHz.
        
        """
        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(MAP_REFERENCE)
        chan=0
        if 'SQR1' in args:chan|=1
        if 'SQR2' in args:chan|=2
        if 'SQR3' in args:chan|=4
        if 'SQR4' in args:chan|=8
        if 'WAVEGEN' in args:chan|=16
        self.H.__sendByte__(chan)
        self.H.__sendByte__(scaler)
        if 'WAVEGEN' in args: self.DDS_CLOCK = 128e6/(1<<scaler)
        self.H.__get_ack__()


    def read_program_address(self,address):
        """
        Reads and returns the value stored at the specified address in program memory

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        address         Address to read from. Refer to PIC24EP64GP204 programming manual
        ==============  ============================================================================================
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(READ_PROGRAM_ADDRESS)
        self.H.__sendInt__(address&0xFFFF)
        self.H.__sendInt__((address>>16)&0xFFFF)
        v=self.H.__getInt__()
        self.H.__get_ack__()
        return v
        
    def __write_program_address__(self,address,value):
        """
        Writes a value to the specified address in program memory. Disabled in firmware.

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        address         Address to write to. Refer to PIC24EP64GP204 programming manual
                        Do Not Screw around with this. It won't work anyway.            
        ==============  ============================================================================================
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(WRITE_PROGRAM_ADDRESS)
        self.H.__sendInt__(address&0xFFFF)
        self.H.__sendInt__((address>>16)&0xFFFF)
        self.H.__sendInt__(value)
        self.H.__get_ack__()

    def read_data_address(self,address):
        """
        Reads and returns the value stored at the specified address in RAM

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        address         Address to read from.  Refer to PIC24EP64GP204 programming manual|
        ==============  ============================================================================================
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(READ_DATA_ADDRESS)
        self.H.__sendInt__(address&0xFFFF)
        v=self.H.__getInt__()
        self.H.__get_ack__()
        return v
        
    def write_data_address(self,address,value):
        """
        Writes a value to the specified address in RAM

        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        address         Address to write to.  Refer to PIC24EP64GP204 programming manual|
        ==============  ============================================================================================
        """
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(WRITE_DATA_ADDRESS)
        self.H.__sendInt__(address&0xFFFF)
        self.H.__sendInt__(value)
        self.H.__get_ack__()


    def servo(self,chan,angle):
        '''
        Output A PWM waveform on SQR1/SQR2 corresponding to the angle specified in the arguments.
        This is used to operate servo motors.  Tested with 9G SG-90 Servo motor.
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        chan            1 or 2. Whether to use SQ1 or SQ2 to output the PWM waveform used by the servo 
        angle           0-180. Angle corresponding to which the PWM waveform is generated.
        ==============  ============================================================================================
        '''
        self.H.__sendByte__(WAVEGEN)
        if chan==1:self.H.__sendByte__(SET_SQR1)
        else:self.H.__sendByte__(SET_SQR2)
        self.H.__sendInt__(10000)
        self.H.__sendInt__(int(angle*1900/180))
        self.H.__sendByte__(2)
        self.H.__get_ack__()


    def __stepperMotor__(self,steps,delay,direction):
        self.H.__sendByte__(NONSTANDARD_IO)
        self.H.__sendByte__(STEPPER_MOTOR)
        self.H.__sendInt__((steps<<1)|direction)
        self.H.__sendInt__(delay)
        t=time.time()
        time.sleep(steps*delay*1e-3) #convert mS to S

    def stepForward(self,steps,delay):
        """
        Control stepper motors using SQR1-4
        
        take a fixed number of steps in the forward direction with a certain delay( in milliseconds ) between each step.
        
        """
        self.__stepperMotor__(steps,delay,1)

    def stepBackward(self,steps,delay):
        """
        Control stepper motors using SQR1-4
        
        take a fixed number of steps in the backward direction with a certain delay( in milliseconds ) between each step.
        
        """
        self.__stepperMotor__(steps,delay,0)

    def servo4(self,a1,a2,a3,a4):
        """
        Operate Four servo motors independently using SQR1, SQR2, SQR3, SQR4.
        tested with SG-90 9G servos.
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        a1              Angle to set on Servo which uses SQR1 as PWM input. [0-180]
        a2              Angle to set on Servo which uses SQR2 as PWM input. [0-180]
        a3              Angle to set on Servo which uses SQR3 as PWM input. [0-180]
        a4              Angle to set on Servo which uses SQR4 as PWM input. [0-180]
        ==============  ============================================================================================
        
        """
        params = (1<<5)|2       #continuous waveform.  prescaler 2( 1:64)
        self.H.__sendByte__(WAVEGEN)
        self.H.__sendByte__(SQR4)
        self.H.__sendInt__(10000)       #10mS wavelength
        self.H.__sendInt__(750+int(a1*1900/180))
        self.H.__sendInt__(0)
        self.H.__sendInt__(750+int(a2*1900/180))
        self.H.__sendInt__(0)
        self.H.__sendInt__(750+int(a3*1900/180))
        self.H.__sendInt__(0)
        self.H.__sendInt__(750+int(a4*1900/180))
        self.H.__sendByte__(params)
        self.H.__get_ack__()


    def enableUartPassthrough(self,baudrate,persist=False):
        '''
        All data received by the device is relayed to an external port(SCL[TX],SDA[RX]) after this function is called
        
        If a period > .5 seconds elapses between two transmit/receive events, the device resets
        and resumes normal mode. This timeout feature has been implemented in lieu of a hard reset option.
        can be used to load programs into secondary microcontrollers with bootloaders such ATMEGA, and ESP8266
        
        
        .. tabularcolumns:: |p{3cm}|p{11cm}|
        ==============  ============================================================================================
        **Arguments** 
        ==============  ============================================================================================
        baudrate        BAUDRATE to use
        persist         If set to True, the device will stay in passthrough mode until the next power cycle.
                        Otherwise(default scenario), the device will return to normal operation if no data is sent/
                        received for a period greater than one second at a time.
        ==============  ============================================================================================
        '''
        self.H.__sendByte__(PASSTHROUGHS)
        self.H.__sendByte__(PASS_UART)
        self.H.__sendByte__(1 if persist else 0)
        self.H.__sendInt__(int( round(((64e6/baudrate)/4)-1) ))
        print 'BRGVAL:',int( round(((64e6/baudrate)/4)-1) )
        time.sleep(0.1)
        print 'junk bytes read:',len(self.H.fd.read(100))



    def estimateDistance(self):
        '''
        
        Read data from ultrasonic distance sensor HC-SR04/HC-SR05.  Sensors must have separate trigger and output pins.
        First a 10uS pulse is output on SQR3.  SQR3 must be connected to the TRIG pin on the sensor prior to use.

        Upon receiving this pulse, the sensor emits a sequence of sound pulses, and the logic level of its output
        pin(which we will monitor via ID1) is also set high.  The logic level goes LOW when the sound packet
        returns to the sensor, or when a timeout occurs.

        The ultrasound sensor outputs a series of 8 sound pulses at 40KHz which corresponds to a time period
        of 25uS per pulse. These pulses reflect off of the nearest object in front of the sensor, and return to it.
        The time between sending and receiving of the pulse packet is used to estimate the distance.
        If the reflecting object is either too far away or absorbs sound, less than 8 pulses may be received, and this
        can cause a measurement error of 25uS which corresponds to 8mm.
        
        '''
        self.H.__sendByte__(NONSTANDARD_IO)
        self.H.__sendByte__(HCSR04_HEADER)

        timeout_msb = int((0.1*64e6))>>16
        self.H.__sendInt__(timeout_msb)

        A=self.H.__getLong__()
        B=self.H.__getLong__()
        tmt = self.H.__getInt__()
        self.H.__get_ack__()
        #print A,B
        if(tmt >= timeout_msb or B==0):return 0
        rtime = lambda t: t/64e6
        return rtime(B-A+20)


    def TemperatureAndHumidity(self):
        '''
        init  AM2302.  
        This effort was a waste.  There are better humidity and temperature sensors available which use well documented I2C
        '''
        self.H.__sendByte__(NONSTANDARD_IO)
        self.H.__sendByte__(AM2302_HEADER)

        self.H.__get_ack__()
        self.digital_channels_in_buffer=1

    def opticalArray(self,tg,delay,tp):
        '''
        read from 3648 element optical sensor array TCD3648P from Toshiba

        see :ref:`tcd_video`

        '''
        samples=3694
        self.H.__sendByte__(NONSTANDARD_IO)
        self.H.__sendByte__(TCD1304_HEADER)
        self.H.__sendByte__(self.__calcCHOSA__('CH5'))
        self.H.__sendByte__(int(tg*8))
        self.H.__sendInt__(delay)
        self.H.__sendInt__(tp)
        self.achans[0].gain = self.sensor_gain
        self.achans[0].set_params(channel='CH5',length=samples,timebase=1,resolution=TWELVE_BIT)
        self.samples=samples
        self.channels_in_buffer=1
        time.sleep(0.005)
        self.H.__get_ack__()

    def readLog(self):
        '''
        read hardware debug log. 
        
        '''
        self.H.__sendByte__(COMMON)
        self.H.__sendByte__(READ_LOG)
        log  = self.H.fd.readline().strip()
        self.H.__get_ack__()
        return log

if __name__ == "__main__":
    print """this is not an executable file
    from v0 import interface
    I=interface.connect()
    
    You're good to go.
    
    eg.
    
    I.get_average_voltage('CH1')
    """
