# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'arbitStream.ui'
#
# Created: Tue Dec 15 12:23:38 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(704, 447)
        MainWindow.setMinimumSize(QtCore.QSize(300, 0))
        MainWindow.setMouseTracking(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../../../../usr/share/pixmaps/cubeview48.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setWindowOpacity(1.0)
        MainWindow.setToolTip(_fromUtf8(""))
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet(_fromUtf8("QPushButton {\n"
"color: #333;\n"
"border: 2px solid #555;\n"
"border-radius: 11px;\n"
"padding: 5px;\n"
"background: qradialgradient(cx: 0.3, cy: -0.4,\n"
"fx: 0.3, fy: -0.4,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #888);\n"
"min-width: 80px;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"background: qradialgradient(cx: 0.4, cy: -0.1,\n"
"fx: 0.4, fy: -0.1,\n"
"radius: 1.35, stop: 0 #fff, stop: 1 #ddd);\n"
"}\n"
"\n"
"QFrame{background-color: rgb(21, 107, 113);}\n"
"\n"
"QComboBox{background-color: rgba(255,255,255, 100);color: rgb(0,0,0);}\n"
"\n"
"border-color: rgb(29, 122, 162);\n"
""))
        MainWindow.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        MainWindow.setTabShape(QtGui.QTabWidget.Rounded)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(3)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.frame = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout = QtGui.QGridLayout(self.frame)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.averageCount = QtGui.QSpinBox(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.averageCount.sizePolicy().hasHeightForWidth())
        self.averageCount.setSizePolicy(sizePolicy)
        self.averageCount.setMinimum(1)
        self.averageCount.setMaximum(501)
        self.averageCount.setObjectName(_fromUtf8("averageCount"))
        self.gridLayout.addWidget(self.averageCount, 1, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 0, 1, 1, 1)
        self.pushButton_2 = QtGui.QPushButton(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.gridLayout.addWidget(self.pushButton_2, 1, 1, 1, 1)
        self.cmdlist = QtGui.QComboBox(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmdlist.sizePolicy().hasHeightForWidth())
        self.cmdlist.setSizePolicy(sizePolicy)
        self.cmdlist.setMinimumSize(QtCore.QSize(250, 0))
        self.cmdlist.setStyleSheet(_fromUtf8("background-color: rgb(0, 0, 0);\n"
"color: rgb(255, 255, 255);"))
        self.cmdlist.setEditable(True)
        self.cmdlist.setObjectName(_fromUtf8("cmdlist"))
        self.cmdlist.addItem(_fromUtf8(""))
        self.cmdlist.addItem(_fromUtf8(""))
        self.cmdlist.addItem(_fromUtf8(""))
        self.cmdlist.addItem(_fromUtf8(""))
        self.cmdlist.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmdlist, 0, 0, 1, 1)
        self.msg = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.msg.sizePolicy().hasHeightForWidth())
        self.msg.setSizePolicy(sizePolicy)
        self.msg.setBaseSize(QtCore.QSize(0, 17))
        font = QtGui.QFont()
        font.setPointSize(26)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.msg.setFont(font)
        self.msg.setStyleSheet(_fromUtf8("color: rgb(255, 255, 255);"))
        self.msg.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.msg.setWordWrap(True)
        self.msg.setObjectName(_fromUtf8("msg"))
        self.gridLayout.addWidget(self.msg, 0, 2, 2, 1)
        self.verticalLayout_2.addWidget(self.frame)
        self.plot_area_frame = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plot_area_frame.sizePolicy().hasHeightForWidth())
        self.plot_area_frame.setSizePolicy(sizePolicy)
        self.plot_area_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.plot_area_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.plot_area_frame.setObjectName(_fromUtf8("plot_area_frame"))
        self.plot_area = QtGui.QVBoxLayout(self.plot_area_frame)
        self.plot_area.setSpacing(2)
        self.plot_area.setMargin(0)
        self.plot_area.setObjectName(_fromUtf8("plot_area"))
        self.verticalLayout_2.addWidget(self.plot_area_frame)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 704, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.actionSave_as = QtGui.QAction(MainWindow)
        self.actionSave_as.setObjectName(_fromUtf8("actionSave_as"))

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), MainWindow.stream)
        QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL(_fromUtf8("clicked()")), MainWindow.setAveraging)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Data Streaming Utility", None))
        self.pushButton.setText(_translate("MainWindow", "Stream Now", None))
        self.pushButton_2.setText(_translate("MainWindow", "Set Averaging", None))
        self.cmdlist.setItemText(0, _translate("MainWindow", "get_average_voltage(\'CH1\')", None))
        self.cmdlist.setItemText(1, _translate("MainWindow", "get_freq(\'Fin\')", None))
        self.cmdlist.setItemText(2, _translate("MainWindow", "get_high_freq(\'Fin\')", None))
        self.cmdlist.setItemText(3, _translate("MainWindow", "DutyCycle(\'ID1\')[1]", None))
        self.cmdlist.setItemText(4, _translate("MainWindow", "MeasureInterval(\'ID1\',\'ID2\',\'rising\',\'rising\')", None))
        self.msg.setText(_translate("MainWindow", ">", None))
        self.actionSave_as.setText(_translate("MainWindow", "Save as", None))

