#!/usr/bin/python
'''
Transistor CE characteristics
'''

import os

from PyQt4 import QtCore, QtGui
import time,sys
from v0.templates import transistorCE

import sys

import pyqtgraph as pg
from v0.utilitiesClass import utilitiesClass

import numpy as np

image = 'transistorCE.png'
helpfile = 'transistorCE.html'
class AppWindow(QtGui.QMainWindow, transistorCE.Ui_MainWindow,utilitiesClass):
	def __init__(self, parent=None,**kwargs):
		super(AppWindow, self).__init__(parent)
		self.setupUi(self)
		self.I=kwargs.get('I',None)

		self.setWindowTitle('vLabtool : '+self.I.H.version_string)
		self.plot=self.add2DPlot(self.plot_area)
		labelStyle = {'color': 'rgb(255,255,255)', 'font-size': '11pt'}
		self.plot.setLabel('left','Current -->', units='A',**labelStyle)
		self.plot.setLabel('bottom','Voltage -->', units='V',**labelStyle)

		self.totalpoints=2000
		self.X=[]
		self.Y=[]
		
		self.curves=[]
		self.curveLabels=[]
		self.looptimer = QtCore.QTimer()
		self.looptimer.timeout.connect(self.acquire)


	def run(self):
		self.looptimer.stop()
		self.X=[];self.Y=[]
		self.base_voltage = self.baseV.value()

		self.curves.append( self.addCurve(self.plot ,'%.3f'%(self.base_voltage),[255,255,255])  )

		self.I.set_pvs3(self.base_voltage) # set base current. PVS3+200K resistor

		self.V = self.startV.value()
		self.I.set_pvs2(self.V) 
		time.sleep(0.2)

		P=self.plot.getPlotItem()
		P.enableAutoRange(True,True)
		self.plot.setXRange(self.V,self.stopV.value())

		self.looptimer.start(20)

	def acquire(self):
		V=self.I.set_pvs2(self.V)
		VC =  self.I.get_average_voltage('CH3',samples=20)
		self.X.append(VC)
		self.Y.append((V-VC)/1.e3) # list( ( np.linspace(V,V+self.stepV.value(),1000)-VC)/1.e3)
		self.curves[-1].setData(self.X,self.Y)

		self.V+=self.stepV.value()
		if self.V>self.stopV.value():
			self.looptimer.stop()
			txt='<div style="text-align: center"><span style="color: #FFF;font-size:8pt;">%.3f V</span></div>'%(self.base_voltage)
			text = pg.TextItem(html=txt, anchor=(0,0), border='w', fill=(0, 0, 255, 100))
			self.plot.addItem(text)
			text.setPos(self.X[-1],self.Y[-1])
			self.curveLabels.append(text)
			self.tracesBox.addItem('Vb = %.3f'%(self.base_voltage))

	def delete_curve(self):
		c = self.tracesBox.currentIndex()
		if c>-1:
			self.tracesBox.removeItem(c)
			self.plot.removeItem(self.curves[c]);self.plot.removeItem(self.curveLabels[c]);
			self.curves.pop(c);self.curveLabels.pop(c);


	def __del__(self):
		self.looptimer.stop()
		print 'bye'

	def closeEvent(self, event):
		self.looptimer.stop()
		self.finished=True

