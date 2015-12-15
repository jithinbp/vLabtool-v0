#!/usr/bin/python

"""

::

	This experiment is used to study the transient response of circuits
	
	The effect of a level change in the input voltage is monitored using the oscilloscope.

.. raw:: html

	<!-- Include the core jQuery and jQuery UI -->
	<script type='text/javascript' src="http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.js"></script>
	<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js"></script>

	<!-- Include the core media player JavaScript. -->
	<script type="text/javascript" src="js/osmplayer.compressed.js"></script>

	<!-- Include the DarkHive ThemeRoller jQuery UI theme. -->
	<link rel="stylesheet" href="js/jquery-ui.css">

	<!-- Include the Default template CSS and JavaScript. -->
	<link rel="stylesheet" href="js/osmplayer_default.css">
	<script type="text/javascript" src="js/osmplayer.default.js"></script>

	<script type="text/javascript">
	  $(function() {
		$("video").osmplayer({
		  width: '100%',
		  height: '400px'
		});
	  });
	</script>

	<video src="videos/lissajous.ogv" showcontrols="1"></video>



"""

from v0.utilitiesClass import utilitiesClass
from v0.analyticsClass import analyticsClass

from v0.templates import template_transient

import numpy as np
from PyQt4 import QtGui,QtCore
import pyqtgraph as pg

params = {
'image' : 'scope.png',
'helpfile': 'https://en.wikipedia.org/wiki/LC_circuit',
'name':'Transient RLC\nResponse'
}

class AppWindow(QtGui.QMainWindow, template_transient.Ui_MainWindow,utilitiesClass):
	def __init__(self, parent=None,**kwargs):
		super(AppWindow, self).__init__(parent)
		self.setupUi(self)
		self.I=kwargs.get('I',None)
		self.CC = analyticsClass()
		
		self.setWindowTitle(self.I.generic_name + ' : '+self.I.H.version_string)
		self.plot1=self.add2DPlot(self.plot_area)
		self.plot2=self.add2DPlot(self.plot_area)
		labelStyle = {'color': 'rgb(255,255,255)', 'font-size': '11pt'}
		self.plot1.setLabel('left','Voltage -->', units='V',**labelStyle)
		self.plot1.setLabel('bottom','Time -->', units='S',**labelStyle)
		self.plot2.setLabel('left','Voltage -->', units='V',**labelStyle)
		self.plot2.setLabel('bottom','Time -->', units='S',**labelStyle)

		self.plot1.setYRange(-8.5,8.5)
		self.plot2.setYRange(-8.5,8.5)

		self.I.configure_trigger(0,'CH1',0)
		self.tg=1
		self.x=[]

		self.looptimer=QtCore.QTimer()
		self.curveCH1 = self.addCurve(self.plot1,'CH1',(255,255,255))
		self.CH1Fit = self.addCurve(self.plot2,'CH1 Fit',(255,255,255))
		self.region = pg.LinearRegionItem([self.tg*50,self.tg*800])
		self.region.setZValue(-10)
		self.plot1.addItem(self.region)		
		self.lognum=0
		self.ON="background-color: rgb(0,255,0);"
		self.OFF="background-color: rgb(255, 0, 0);"
		self.state=0
		self.I.set_state(OD1=0)
		self.indicator.setStyleSheet(self.OFF)
		self.msg.setText("Fitting fn :\noff+amp*exp(-damp*x)*sin(x*freq+ph)")
		self.Params=[]
		
	def run(self):
		print self.I.get_average_voltage('CH1')
		self.I.H.loadBurst=True
		self.I.capture_traces(1,5000,self.tg,trigger=False)
		self.state = 0 if self.state else 1
		self.I.set_state(OD1=self.state)
		print self.I.H.sendBurst()
		if(self.state):self.indicator.setStyleSheet(self.ON)
		else:self.indicator.setStyleSheet(self.OFF)
		self.CH1Fit.setData([],[])
		self.loop=self.delayedTask(5000*self.I.timebase*1e-6+10,self.plotData)

	def fit(self):
		if(not len(self.x)):return
		start,end=self.region.getRegion()
		if(start>0):start = int(round(start/self.I.timebase))
		else: start=0
		if(end>0):end = int(round(end/self.I.timebase))
		else:end=0
		guess = self.CC.getGuessValues(self.x[start:end]-self.x[start],self.VMID[start:end],func='damped sine')
		Csuccess,Cparams,chisq = self.CC.arbitFit(self.x[start:end]-self.x[start],self.VMID[start:end],self.CC.dampedSine,guess=guess)

		if Csuccess:
			self.CLabel.setText("CH1:\nA:%.2f V\tF:%.1f Hz\tDamp:%.3e"%(Cparams[0],1e6*abs(Cparams[1])/(2*np.pi),Cparams[4]))
			self.CH1Fit.setData(self.x[start:end]-self.x[start],self.CC.dampedSine(self.x[start:end]-self.x[start],*Cparams))
			self.CParams=Cparams
		else:
			self.CLabel.setText("CH1:\nFit Failed. Change selected region.")
			self.CH1Fit.clear()

	def plotData(self):	
		self.x,self.VMID=self.I.fetch_trace(1)
		self.curveCH1.setData(self.x,self.VMID)

	def showData(self):
		self.lognum+=1
		print '------------------------',self.lognum,'------------------'
		b=self.CParams
		print 'FIT:\tAmp:%.1fV\tFreq:%.1fHz\tPhase:%.1f\tOffset:%.2fV\tDamping:%.2e'%(b[0],1e6*abs(b[1])/(2*np.pi),b[2]*180/np.pi,b[3],b[4])
		print '\n'
		

