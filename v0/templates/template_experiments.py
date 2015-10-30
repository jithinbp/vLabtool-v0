# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'template_experiments.ui'
#
# Created: Thu Oct 29 19:17:03 2015
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
        MainWindow.resize(930, 558)
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
"QFrame.PeripheralCollection{\n"
"border-top-left-radius: 5px;\n"
"border-top-right-radius: 5px;\n"
"border: 1px solid black;\n"
"background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"stop: 0 #6af, stop: 0.1 #689);\n"
"}\n"
"QFrame.PeripheralCollection QLabel {\n"
"color: white;\n"
"font-weight: bold;\n"
"}\n"
"\n"
"QFrame.PeripheralCollectionInner {\n"
"background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"stop: 0 #abe, stop: 0.7 #aba);\n"
"border: none;\n"
"border-top: 1px solid black;\n"
"}\n"
"\n"
"QFrame.PeripheralCollectionInner QLabel{\n"
"color: black;\n"
"}\n"
"\n"
"QScrollArea.PeripheralCollectionInner {\n"
"background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"stop: 0 #abe, stop: 0.7 #aba);\n"
"border: none;\n"
"border-top: 1px solid black;\n"
"}\n"
"\n"
"QScrollArea.PeripheralCollectionInner QLabel{\n"
"color: black;\n"
"}\n"
"\n"
"QWidget.PeripheralCollectionInner {\n"
"background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,\n"
"stop: 0 #abe, stop: 0.7 #aba);\n"
"border: none;\n"
"border-top: 1px solid black;\n"
"}\n"
"\n"
"QWidget.PeripheralCollectionInner QLabel{\n"
"color: black;\n"
"}\n"
"\n"
"\n"
""))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setStyleSheet(_fromUtf8(""))
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(3, 10, 3, 10)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.widgetFrameOuter = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widgetFrameOuter.sizePolicy().hasHeightForWidth())
        self.widgetFrameOuter.setSizePolicy(sizePolicy)
        self.widgetFrameOuter.setStyleSheet(_fromUtf8(""))
        self.widgetFrameOuter.setFrameShape(QtGui.QFrame.StyledPanel)
        self.widgetFrameOuter.setFrameShadow(QtGui.QFrame.Raised)
        self.widgetFrameOuter.setObjectName(_fromUtf8("widgetFrameOuter"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.widgetFrameOuter)
        self.verticalLayout_3.setSpacing(5)
        self.verticalLayout_3.setContentsMargins(0, 5, 0, 0)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label_3 = QtGui.QLabel(self.widgetFrameOuter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_3.addWidget(self.label_3)
        self.WidgetFrame = QtGui.QFrame(self.widgetFrameOuter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.WidgetFrame.sizePolicy().hasHeightForWidth())
        self.WidgetFrame.setSizePolicy(sizePolicy)
        self.WidgetFrame.setObjectName(_fromUtf8("WidgetFrame"))
        self.gridLayout_3 = QtGui.QGridLayout(self.WidgetFrame)
        self.gridLayout_3.setSpacing(5)
        self.gridLayout_3.setContentsMargins(0, 5, 0, 0)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.WidgetLayout = QtGui.QGridLayout()
        self.WidgetLayout.setSpacing(4)
        self.WidgetLayout.setObjectName(_fromUtf8("WidgetLayout"))
        self.gridLayout_3.addLayout(self.WidgetLayout, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.WidgetFrame)
        self.gridLayout.addWidget(self.widgetFrameOuter, 1, 0, 1, 1)
        self.frame = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(450, 0))
        self.frame.setStyleSheet(_fromUtf8(""))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setContentsMargins(0, 5, 0, 0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.helpTitle = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpTitle.sizePolicy().hasHeightForWidth())
        self.helpTitle.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.helpTitle.setFont(font)
        self.helpTitle.setObjectName(_fromUtf8("helpTitle"))
        self.verticalLayout.addWidget(self.helpTitle)
        self.scrollArea = QtGui.QScrollArea(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QtCore.QSize(0, 130))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollFrame = QtGui.QWidget()
        self.scrollFrame.setGeometry(QtCore.QRect(0, 0, 446, 205))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollFrame.sizePolicy().hasHeightForWidth())
        self.scrollFrame.setSizePolicy(sizePolicy)
        self.scrollFrame.setObjectName(_fromUtf8("scrollFrame"))
        self.tmpl = QtGui.QVBoxLayout(self.scrollFrame)
        self.tmpl.setSpacing(0)
        self.tmpl.setMargin(0)
        self.tmpl.setObjectName(_fromUtf8("tmpl"))
        self.experimentFrame = QtGui.QFrame(self.scrollFrame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.experimentFrame.sizePolicy().hasHeightForWidth())
        self.experimentFrame.setSizePolicy(sizePolicy)
        self.experimentFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.experimentFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.experimentFrame.setObjectName(_fromUtf8("experimentFrame"))
        self.gridLayout_2 = QtGui.QGridLayout(self.experimentFrame)
        self.gridLayout_2.setSpacing(5)
        self.gridLayout_2.setContentsMargins(0, 5, 0, 0)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.ExperimentLayout = QtGui.QGridLayout()
        self.ExperimentLayout.setSpacing(4)
        self.ExperimentLayout.setObjectName(_fromUtf8("ExperimentLayout"))
        self.gridLayout_2.addLayout(self.ExperimentLayout, 0, 0, 1, 1)
        self.tmpl.addWidget(self.experimentFrame)
        self.scrollArea.setWidget(self.scrollFrame)
        self.verticalLayout.addWidget(self.scrollArea)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)
        self.frame_2 = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_2.setObjectName(_fromUtf8("frame_2"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.frame_2)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton = QtGui.QPushButton(self.frame_2)
        self.pushButton.setMinimumSize(QtCore.QSize(94, 0))
        self.pushButton.setMaximumSize(QtCore.QSize(50, 25))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout.addWidget(self.pushButton)
        self.deviceCombo = QtGui.QComboBox(self.frame_2)
        self.deviceCombo.setObjectName(_fromUtf8("deviceCombo"))
        self.horizontalLayout.addWidget(self.deviceCombo)
        self.gridLayout.addWidget(self.frame_2, 2, 0, 1, 1)
        self.helpFrameOuter = QtGui.QFrame(self.centralwidget)
        self.helpFrameOuter.setFrameShape(QtGui.QFrame.StyledPanel)
        self.helpFrameOuter.setFrameShadow(QtGui.QFrame.Raised)
        self.helpFrameOuter.setObjectName(_fromUtf8("helpFrameOuter"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.helpFrameOuter)
        self.verticalLayout_2.setSpacing(5)
        self.verticalLayout_2.setContentsMargins(0, 5, 0, 0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label = QtGui.QLabel(self.helpFrameOuter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.helpLayout = QtGui.QVBoxLayout()
        self.helpLayout.setObjectName(_fromUtf8("helpLayout"))
        self.verticalLayout_2.addLayout(self.helpLayout)
        self.gridLayout.addWidget(self.helpFrameOuter, 0, 1, 3, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 930, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), MainWindow.selectDevice)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.widgetFrameOuter.setProperty("class", _translate("MainWindow", "PeripheralCollection", None))
        self.label_3.setText(_translate("MainWindow", "Widgets", None))
        self.WidgetFrame.setProperty("class", _translate("MainWindow", "PeripheralCollectionInner", None))
        self.frame.setProperty("class", _translate("MainWindow", "PeripheralCollection", None))
        self.helpTitle.setText(_translate("MainWindow", "Experiments", None))
        self.experimentFrame.setProperty("class", _translate("MainWindow", "PeripheralCollectionInner", None))
        self.pushButton.setText(_translate("MainWindow", "SET", None))
        self.helpFrameOuter.setProperty("class", _translate("MainWindow", "PeripheralCollection", None))
        self.label.setText(_translate("MainWindow", "Experiment Details", None))

