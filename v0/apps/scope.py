#!/usr/bin/python
'''
oscilloscope for the vLabtool - version 0. \n

Also Includes XY plotting mode, and fitting against standard Sine/Square functions\n
'''

import os
os.environ['QT_API'] = 'pyqt'
import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)


from PyQt4 import QtCore, QtGui
import time,sys
from v0.templates import analogScope
from v0.analyticsClass import analyticsClass

import sys,os,string
import time
import sys

import pyqtgraph as pg
import pyqtgraph.opengl as gl

import numpy as np
import scipy.optimize as optimize
import scipy.fftpack as fftpack


err_count=0
trial = 0
start_time = time.time()
fps = None
dacval=0
from v0.commands_proto import *

params = {
'image' : 'scope.png',
'name':'Oscilloscope'
}



class AppWindow(QtGui.QMainWindow, analogScope.Ui_MainWindow):
	def __init__(self, parent=None,**kwargs):
		super(AppWindow, self).__init__(parent)
		self.setupUi(self)
		self.I=kwargs.get('I',None)
		self.math = analyticsClass()

		self.setWindowTitle(self.I.generic_name + ' : ' +self.I.H.version_string)
		self.plot=pg.PlotWidget()

		#cross hair
		self.vLine = pg.InfiniteLine(angle=90, movable=True)
		#self.vLine.setPen(color=(135,44,64,150), width=3)
		self.plot.addItem(self.vLine, ignoreBounds=False)

		self.proxy = pg.SignalProxy(self.vLine.scene().sigMouseMoved, rateLimit=60, slot=self.readCursor)
		
		self.fps=0
		self.max_samples_per_channel=[0,self.I.MAX_SAMPLES/4,self.I.MAX_SAMPLES/4,self.I.MAX_SAMPLES/4,self.I.MAX_SAMPLES/4]
		self.liss_win=None
		self.liss_ready=False
		self.liss_animate_arrow1=None
		self.liss_animate_arrow2=None
		self.liss_animate_arrow3=None
		self.liss_anim1=None
		self.liss_anim2=None
		self.liss_anim3=None
		self.samples=self.I.MAX_SAMPLES/4#self.sample_slider.value()
		self.active_channels=1
		self.channel_states=np.array([1,0,0,0])
		self.channels_in_buffer=1
		self.chan1remap='CH1'
		self.ch123sa = 0
		g=1.75
		self.timebase = g
		self.lastTime=time.time()

		self.trace_colors=[(0,255,20),(255,255,0),(255,10,100),(10,255,255)]

		self.plot.setLabel('bottom', 'Time -->>', units='S')
		labelStyle = {'color': 'rgb%s'%(str(self.trace_colors[0])), 'font-size': '11pt'}
		self.plot.setLabel('left','CH1', units='V',**labelStyle)
		self.plot.addLegend(offset=(-10,30))

		self.plot2 = pg.ViewBox()
		self.ax2 = pg.AxisItem('right')
		self.plot.plotItem.layout.addItem(self.ax2, 2, 3)
		self.plot.plotItem.scene().addItem(self.plot2)
		self.ax2.linkToView(self.plot2)
		self.plot2.setXLink(self.plot.plotItem)
		self.ax2.setZValue(-10000)
		labelStyle = {'color': 'rgb%s'%(str(self.trace_colors[1])), 'font-size': '13pt'}
		self.ax2.setLabel('CH2', units='V', **labelStyle)

		self.plot2.setGeometry(self.plot.plotItem.vb.sceneBoundingRect())
		self.plot2.linkedViewChanged(self.plot.plotItem.vb, self.plot2.XAxis)
		## Handle view resizing 
		self.plot.getViewBox().sigStateChanged.connect(self.updateViews)

		self.curve1 = self.plot.plot(name='CH1'); self.curve1.setPen(color=self.trace_colors[0], width=1)
		self.curve2 = self.plot.plot(name='CH2'); self.curve2.setPen(color=self.trace_colors[1], width=1)
		self.curve3 = self.plot.plot(name='CH3'); self.curve3.setPen(color=self.trace_colors[2], width=1)
		self.curve4 = self.plot.plot(name='CH4'); self.curve4.setPen(color=self.trace_colors[3], width=1)
		self.curve_lis = self.plot.plot(); self.curve_lis.setPen(color=(255,255,255), width=1)

		self.curveF=[]
		for a in range(2):
			self.curveF.append( self.plot.plot() ); self.curveF[-1].setPen(color=(255,255,255), width=1)


		self.curveB = pg.PlotDataItem(name='CH2')
		self.plot2.addItem(self.curveB)
		self.curveB.setPen(color=self.trace_colors[1], width=1)

		self.curveFR = pg.PlotDataItem()
		self.plot2.addItem(self.curveFR); self.curveFR.setPen(color=(255,255,255), width=1)

		self.CH1_ENABLE.setStyleSheet('background-color:rgba'+str(self.trace_colors[0])[:-1]+',3);color:(0,0,0);')
		self.CH2_ENABLE.setStyleSheet('background-color:rgba'+str(self.trace_colors[1])[:-1]+',3);color:(0,0,0);')
		for a in range(4):
			self.trigger_select_box.setItemData(a, QtGui.QColor(*self.trace_colors[a]), QtCore.Qt.BackgroundRole);

		self.triggerChannelName='CH1'
		self.arrow = pg.ArrowItem(pos=(0, 0), angle=0)
		self.plot.addItem(self.arrow)
		#markings every 5 Volts
		self.voltsperdiv = ['5V/div','3V/div','2V/div','1V/div','500mV/div','400mV/div','300mV/div','100mV/div']
		self.trigger_channel=0
		self.trigger_level = 0
		self.trigtext = pg.TextItem(html=self.trigger_text('CH1'), anchor=(1.2,0.5), border='w', fill=(0, 0, 255, 100),angle=0)
		self.plot.addItem(self.trigtext)
		self.plot.showGrid(True,False,0.4)
		self.scope_type=0
		self.plot_area.addWidget(self.plot)
		self.CH1_REMAPS.addItems(self.I.allAnalogChannels)
		self.showgrid()
		self.trigtext.setParentItem(self.arrow)
		self.I.configure_trigger(self.trigger_channel,self.triggerChannelName,0)
		
		self.autoRange()
		self.timer = QtCore.QTimer()
		self.finished=False
		self.timer.singleShot(500,self.start_capture)

	def updateViews(self):
			self.plot2.setGeometry(self.plot.getViewBox().sceneBoundingRect())
			self.plot2.linkedViewChanged(self.plot.plotItem.vb, self.plot2.XAxis)
		
	def trigger_text(self,c):
		return '<div style="text-align: center"><span style="color: #FFF; font-size: 8pt;">'+c+'</span></div>'		

	def showgrid(self):
		return
		
	def start_capture(self):
		if self.finished:
			return
		if(self.freezeButton.isChecked()):
			self.timer.singleShot(200,self.start_capture)
			return

		temperature=self.I.get_temperature()
		self.plot.setTitle('%0.2f fps, 	%0.1f ^C' % (self.fps,temperature ) )
		self.channels_in_buffer=self.active_channels

		a = self.CH1_ENABLE.isChecked()
		b = self.CH2_ENABLE.isChecked()
		c = self.FOURCHAN_ENABLE.isChecked()
		if c:
			self.active_channels=4
		elif b:
			self.active_channels=2
		elif a:
			self.active_channels=1
		else:
			self.active_channels=0

		self.channels_in_buffer=self.active_channels
		self.channel_states[0]=a
		self.channel_states[1]=b
		self.channel_states[2]=c
		self.channel_states[3]=c
		
		if self.active_channels:
			self.I.configure_trigger(self.trigger_channel,self.triggerChannelName,self.trigger_level,resolution=10)
			self.I.capture_traces(self.active_channels,self.samples,self.timebase,self.chan1remap,self.ch123sa)

		self.timer.singleShot(self.samples*self.I.timebase*1e-3+10,self.update)

	def update(self):
		n=0
		while(not self.I.oscilloscope_progress()[0]):
			time.sleep(0.1)
			print self.timebase,'correction required',n
			n+=1
			if n>10:
				self.timer.singleShot(100,self.start_capture)
				return
		if(self.channels_in_buffer>=1):self.I.__fetch_channel__(1)
		if(self.channels_in_buffer>=2):self.I.__fetch_channel__(2)
		if(self.channels_in_buffer>=3):self.I.__fetch_channel__(3)
		if(self.channels_in_buffer>=4):self.I.__fetch_channel__(4)

		self.curve1.clear()
		self.curve2.clear()
		self.curve3.clear()
		self.curve4.clear()
		self.curveB.clear()
		self.curveF[0].clear()
		self.curveF[1].clear()
		self.curveFR.clear()

		msg='';pos=0
		for fitsel in [self.fit_select_box,self.fit_select_box_2]:
			if fitsel.currentIndex()<4:
				if len(msg)>0:
					msg+='\n'
				if self.channel_states[fitsel.currentIndex()]:
					if fitsel.currentText()=='CH2':
						msg+='FIT '+chr(pos+65)+': '+self.fitData(self.I.achans[fitsel.currentIndex()].get_xaxis(),\
						self.I.achans[fitsel.currentIndex()].get_yaxis(),self.curveFR)
					else:
						msg+='FIT '+chr(pos+65)+': '+self.fitData(self.I.achans[fitsel.currentIndex()].get_xaxis(),\
						self.I.achans[fitsel.currentIndex()].get_yaxis(),self.curveF[pos])


				else:
					msg+='FIT '+chr(pos+65)+': Channel Unavailable'

			pos+=1
		if len(msg):
			self.message_label.setText(msg)
		pos=0

		if self.Liss_show.isChecked():
			chans = ['CH1','CH2','CH3','CH4']
			lissx = self.Liss_x.currentText()
			lissy = self.Liss_y.currentText()
			self.liss_x = chans.index(lissx)
			self.liss_y = chans.index(lissy)
			la=self.I.achans[self.liss_x].get_yaxis()
			lb=self.I.achans[self.liss_y].get_yaxis()
			if(self.liss_x<self.active_channels and self.liss_y<self.active_channels and len(la)==len(lb)):
				self.curve_lis.setData(self.I.achans[self.liss_x].get_yaxis(),self.I.achans[self.liss_y].get_yaxis())
				self.liss_ready=True
			else:
				self.curve_lis.clear()
				self.liss_ready=False
				self.message_label.setText('Channels for XY display not selected')
				#print self.fps,'not available',self.active_channels,self.liss_x,self.liss_y

		else:
			self.curve_lis.clear()
			for a in [self.curve1,self.curveB,self.curve3,self.curve4]:
				if self.channel_states[pos]: a.setData(self.I.achans[pos].get_xaxis()*1e-6,self.I.achans[pos].get_yaxis(),connect='finite')
				pos+=1

			
		self.readCursor()			


		now = time.time()
		dt = now - self.lastTime
		self.lastTime = now
		if self.fps is None:
			self.fps = 1.0/dt
		else:
			s = np.clip(dt*3., 0, 1)
			self.fps = self.fps * (1-s) + (1.0/dt) * s
		
		self.timer.singleShot(100,self.start_capture)



	def readCursor(self):
		pos=self.vLine.getPos()
		index = int(pos[0]*1e6)/self.I.timebase
		if index > 0 and index < self.I.samples:
			coords="<span style='color: white'>%0.1f uS</span>: "%(self.I.achans[0].xaxis[index])
			for a in range(4):
				if self.channel_states[a]:
					c=self.trace_colors[a]
					coords+="<span style='color: rgb%s'>%0.3fV</span>," %(c, self.I.achans[a].yaxis[index])
			self.coord_label.setText(coords)
		else:
			self.coord_label.setText("")


	def fitData(self,xReal,yReal,curve):
		if self.fit_type_box.currentIndex()==0: #sine wave
			fitres = self.math.sineFit(xReal,yReal)
			if fitres:
				amp=fitres[0]
				freq=fitres[1]
				offset=fitres[2]
				ph=fitres[3]

				frequency = freq/1e6
				period = 1./freq/1e6
				if(self.collapseButton.isChecked()):
					self.collapseButton.setChecked(False)
					self.collapse_win = pg.GraphicsWindow(title="Collapsing plot")
					xNew=[]
					yNew=[]
				
					for a in range(len(xReal)):
						x=(xReal[a]%(period*2))*1e-6
						xNew.append(x)
						yNew.append(yReal[a])
					xNew=np.array(xNew)
					yNew=np.array(yNew)
					s=np.argsort(xNew)
					self.p1 = self.collapse_win.addPlot(title="Collapsing plot: %.1f waveforms collapsed on top of each other"%(xReal[-1]/period), x=xNew[s],y=yNew[s])
					if(self.collapse_win.windowState() & QtCore.Qt.WindowActive):
						print 'opened'
				#------------------------------------------------------
			
				if(self.overlay_fit_button.isChecked()):
					x=np.linspace(0,xReal[-1],50000)
					curve.setData(x*1e-6,self.math.sineFunc(x,amp,frequency,ph*np.pi/180,offset))
				return 'Amp = %0.3fV \tFreq=%0.2fHz \tOffset=%0.3fV \tPhase=%0.1f%c'%(amp, freq, offset,ph,176)
			else:
				return 'fit failed'

		elif self.fit_type_box.currentIndex()==1: #square
			fitres = self.math.squareFit(xReal,yReal)
			if fitres:
				amp=fitres[0]
				freq=fitres[1]
				phase=fitres[2]
				dc=fitres[3]
				offset=fitres[4]

				frequency = freq/1e6
				period = 1./freq/1e6
				if(self.collapseButton.isChecked()):
					self.collapseButton.setChecked(False)
					self.collapse_win = pg.GraphicsWindow(title="Collapsing plot")
					xNew=[]
					yNew=[]
				
					for a in range(len(xReal)):
						x=(xReal[a]%(period*2))*1e-6
						xNew.append(x)
						yNew.append(yReal[a])
					xNew=np.array(xNew)
					yNew=np.array(yNew)
					s=np.argsort(xNew)
					self.p1 = self.collapse_win.addPlot(title="Collapsing plot: %.1f waveforms collapsed on top of each other"%(xReal[-1]/period), x=xNew[s],y=yNew[s])
					if(self.collapse_win.windowState() & QtCore.Qt.WindowActive):
						print 'opened'
				#------------------------------------------------------
			
				if(self.overlay_fit_button.isChecked()):
					x=np.linspace(0,xReal[-1],50000)
					curve.setData(x*1e-6,self.math.squareFunc(x,amp,frequency,phase,dc,offset))
				return 'Amp = %0.3fV \tFreq=%0.2fHz \tDC=%0.3fV \tOffset=%0.3fV'%(amp, freq,dc,offset)
			else:
				return 'fit failed'
		else:
				return 'fit failed'


	def setOffsetAndGainLabels(self):
		self.CH1_LABEL.setText('CH1: ')
		self.CH2_LABEL.setText('CH2: ')
	
	def setGainCH1(self,g):
		self.I.set_gain(self.chan1remap,g)
		self.CH1_LABEL.setText('CH1: ')
		if not self.Liss_show.isChecked():
			chan = self.I.analogInputSources[self.chan1remap]
			R = [chan.calPoly10(0),chan.calPoly10(1023)]
			R[0]=R[0]*.9;R[1]=R[1]*.9
			self.plot.setYRange(min(R),max(R))
			self.setOffsetAndGainLabels()
		
	def setGainCH2(self,g):
		self.I.set_gain('CH2',g)
		self.CH2_LABEL.setText('CH2: ')
		if not self.Liss_show.isChecked():
			chan = self.I.analogInputSources['CH2']
			R = [chan.calPoly10(0),chan.calPoly10(1023)]
			R[0]=R[0]*.9;R[1]=R[1]*.9
			self.plot2.setYRange(min(R),max(R))
			self.setOffsetAndGainLabels()

	def setOffset(self,off):
		chan = self.I.analogInputSources[self.chan1remap]
		print 'no offset on ',chan

	def setOffsetCH1(self,g):
		cnum=0
		self.setOffsetAndGainLabels()

	def setOffsetCH2(self,g):
		cnum=1
		self.setOffsetAndGainLabels()


	def setTimeBase(self,g):
		timebases = [1.75,2,4,8,16,32,128,256,512,1024,1024]
		samplescaling=[1,1,1,1,1,0.5,0.4,0.3,0.2,0.1,0.1]
		#print g,len(timebases),len(samplescaling)
		self.timebase=timebases[g]
		'''
		if(self.active_channels==1 and self.timebase<1.0):
			self.timebase=1.0
		elif(self.active_channels==2 and self.timebase<1.25):
			self.timebase=1.25
		elif((self.active_channels==3 or self.active_channels==4) and self.timebase<1.75):
			self.timebase=1.75
		'''
		self.autoSetSamples()
		self.samples = int(self.samples*samplescaling[g])
		self.autoRange()
		self.showgrid()


	def autoSetSamples(self):
		self.samples = self.max_samples_per_channel[self.active_channels]

	def setTriggerLevel(self,val):
		if self.trigger_channel==0:self.triggerChannelName=self.chan1remap
		else:self.triggerChannelName='CH2'
		
		chan = self.I.analogInputSources[self.triggerChannelName]

		if chan.inverted:val=1000-val
		levelInVolts=chan.calPoly10(val*1023/1000.)
		
		self.trigger_level=levelInVolts
		self.arrow.setPos(0,levelInVolts) #TODO
		self.trigger_level_box.setValue(levelInVolts)

	def setTriggerChannel(self,val):
		self.trigtext.setHtml(self.trigger_text(self.I.achans[val].name))
		self.triggerChannel=val
		self.trigger_channel = val
		c=self.trace_colors[val]
		s='QFrame{background-color:rgba'+str(c)[:-1]+',50);}'
		self.sender().parentWidget().setStyleSheet(s)
		self.arrow.setParentItem(None)
		if val==0:
			self.plot.addItem(self.arrow)
		elif val==1:
			self.plot2.addItem(self.arrow)



	def setActiveChannels(self,val):
		self.active_channels = int(val)
		self.autoSetSamples()
		

	def remap_CH0(self,val):
		val = str(val)
		self.chosa = self.I.__calcCHOSA__(val)
		self.chan1remap=val
		chan = self.I.analogInputSources[self.chan1remap]
		R = [chan.calPoly10(0),chan.calPoly10(1023)]
		self.plot.setYRange(min(R),max(R))
		
	def autoRange(self):
		if self.Liss_show.isChecked():
			X = self.I.analogInputSources[self.chan1remap]
			R1 = [X.calPoly10(0),X.calPoly10(1023)]
			R1[0]=R1[0]*.9;R1[1]=R1[1]*.9
			
			Y = self.I.analogInputSources['CH2']
			R2 = [Y.calPoly10(0),Y.calPoly10(1023)]
			R2[0]=R2[0]*.9;R2[1]=R2[1]*.9

			self.plot.setXRange(min(R1),max(R1))
			self.plot.setYRange(min(R2),max(R2))

		else:
			chan = self.I.analogInputSources[self.chan1remap]
			R = [chan.calPoly10(0),chan.calPoly10(1023)]
			R[0]=R[0]*.9;R[1]=R[1]*.9
			#print R
			self.plot.setYRange(min(R),max(R))
			chan = self.I.analogInputSources['CH2']
			R = [chan.calPoly10(0),chan.calPoly10(1023)]
			R[0]=R[0]*.9;R[1]=R[1]*.9
			self.plot2.setYRange(min(R),max(R))
			self.plot.setXRange(0,self.timebase*self.samples*1e-6)
			#self.plot.setRange(QtCore.QRectF(0, -16.5, self.samples*self.timebase*1e-6, 2*16.5)) 

	def enableXY(self,state):
		self.autoRange()

	def plot_liss(self):
		chans = ['CH1','CH2']
		lissx = self.Liss_x.currentText()
		lissy = self.Liss_y.currentText()
		self.liss_x = chans.index(lissx)
		self.liss_y = chans.index(lissy)
		self.liss_win = pg.GraphicsWindow(title="Basic plotting examples")
		self.liss_win.setWindowTitle('pyqtgraph example: Plotting')
		self.p1 = self.liss_win.addPlot(title="Lissajous: x:%s , y:%s"%(lissx,lissy), x=self.I.achans[self.liss_x].get_yaxis(),y=self.I.achans[self.liss_y].get_yaxis())
		if(self.liss_win.windowState() & QtCore.Qt.WindowActive):
			print 'opened'

	def liss_animate(self,val):
		if val and self.liss_ready and self.Liss_show.isChecked():
			self.freezeButton.setChecked(True)
			self.liss_animate_arrow1=pg.CurveArrow(self.curve_lis)
			if(self.liss_x==0):
				self.liss_animate_arrow2=pg.CurveArrow(self.curve1)
			elif(self.liss_x==1):
				self.liss_animate_arrow2=pg.CurveArrow(self.curve2)
			elif(self.liss_x==2):
				self.liss_animate_arrow2=pg.CurveArrow(self.curve3)
			elif(self.liss_x==3):
				self.liss_animate_arrow2=pg.CurveArrow(self.curve4)
			if(self.liss_y==0):
				self.liss_animate_arrow3=pg.CurveArrow(self.curve1)
			elif(self.liss_y==1):
				self.liss_animate_arrow3=pg.CurveArrow(self.curve2)
			elif(self.liss_y==2):
				self.liss_animate_arrow3=pg.CurveArrow(self.curve3)
			elif(self.liss_y==3):
				self.liss_animate_arrow3=pg.CurveArrow(self.curve4)
			self.plot.addItem(self.liss_animate_arrow1)
			self.plot.addItem(self.liss_animate_arrow2)
			self.plot.addItem(self.liss_animate_arrow3)
			self.liss_anim1 = self.liss_animate_arrow1.makeAnimation(loop=-1)
			self.liss_anim2 = self.liss_animate_arrow2.makeAnimation(loop=-1)
			self.liss_anim3 = self.liss_animate_arrow3.makeAnimation(loop=-1)
			self.liss_anim1.start();self.liss_anim2.start();self.liss_anim3.start()
		else:
			self.freezeButton.setChecked(False)
			try:
				self.liss_anim1.stop();self.liss_anim2.stop();self.liss_anim3.stop()
				self.plot.removeItem(self.liss_animate_arrow1)
				self.plot.removeItem(self.liss_animate_arrow2)
				self.plot.removeItem(self.liss_animate_arrow3)
			except:
				pass


	def closeEvent(self, event):
		self.timer.stop()
		self.finished=True
		

	def __del__(self):
		self.timer.stop()
		print 'bye'

		
