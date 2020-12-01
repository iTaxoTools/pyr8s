#! /usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QSplitter, QMainWindow, QAction, qApp, QToolBar)
from PyQt5.QtGui import QIcon

class PToolBar(QToolBar):
    """Paired toolbar"""
    resized = pyqtSignal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().height() != event.oldSize().height():
            # print('resized', event.size().height(), event.oldSize().height())
            self.resized.emit()

    def pairHandle(self):
        # print('another', self.sender().height())
        other = self.sender().height()
        if other > self.height():
            self.setFixedHeight(other)

    def pair(self, widget):
        self.resized.connect(widget.pairHandle)

class Main(QDialog):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.draw()

    def draw(self):
        """Draw all widgets"""
        self.createTopRightGroupBox()
        self.leftPane, self.barLabel = self.createEditPane()
        self.rightPane, self.barButton  = self.createCanvasPane()
        self.barLabel.pair(self.barButton)
        self.barButton.pair(self.barLabel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.leftPane)
        splitter.addWidget(self.rightPane)
        splitter.setStretchFactor(0,0)
        splitter.setStretchFactor(1,1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def createCanvasPane(self):
        pane = QWidget()

        toolbar = PToolBar('Tools')
        toolbar.addAction('Open')
        toolbar.addAction('Save')
        toolbar.addAction('Export')

        canvas = QGroupBox()
        canvas.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def createEditPane(self):
        pane = QWidget()

        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)

        label = QLabel("Some tools")
        label.setAlignment(Qt.AlignHCenter)
        labelayout = QHBoxLayout()
        labelayout.addWidget(label, 1)
        labelwidget = QWidget()
        labelwidget.setLayout(labelayout)

        toolbar = PToolBar('Tools')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        # toolbar.addAction(exitAct)
        # toolbar.addAction('exitAct')
        toolbar.addWidget(labelwidget)

        tabWidget = QTabWidget()
        # tabWidget.setSizePolicy(QSizePolicy.Preferred,
        #         QSizePolicy.Ignored)

        tab1 = QWidget()
        tableWidget = QTableWidget(10, 10)

        tab1hbox = QHBoxLayout()
        tab1hbox.setContentsMargins(0, 0, 0, 0)
        tab1hbox.addWidget(tableWidget)
        tab1.setLayout(tab1hbox)

        tab2 = QWidget()
        textEdit = QTextEdit()

        textEdit.setPlainText("Twinkle, twinkle, little star,\n"
                              "How I wonder what you are.\n"
                              "Up above the world so high,\n"
                              "Like a diamond in the sky.\n"
                              "Twinkle, twinkle, little star,\n"
                              "How I wonder what you are!\n")

        tab2hbox = QHBoxLayout()
        # tab2hbox.setContentsMargins(5, 5, 5, 5)
        tab1hbox.setContentsMargins(0, 0, 0, 0)
        tab2hbox.addWidget(textEdit)
        tab2.setLayout(tab2hbox)

        tabWidget.addTab(tab1, "&Table")
        tabWidget.addTab(tab2, "Text &Edit")

        layout = QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(tabWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def advanceProgressBar(self):
        curVal = self.progressBar.value()
        maxVal = self.progressBar.maximum()
        self.progressBar.setValue(curVal + (maxVal - curVal) // 100)

    def createTopLeftGroupBox(self):
        self.topLeftGroupBox = QGroupBox("Group 1")

        radioButton1 = QRadioButton("Radio button 1")
        radioButton2 = QRadioButton("Radio button 2")
        radioButton3 = QRadioButton("Radio button 3")
        radioButton1.setChecked(True)

        checkBox = QCheckBox("Tri-state check box")
        checkBox.setTristate(True)
        checkBox.setCheckState(Qt.PartiallyChecked)

        layout = QVBoxLayout()
        layout.addWidget(radioButton1)
        layout.addWidget(radioButton2)
        layout.addWidget(radioButton3)
        layout.addWidget(checkBox)
        layout.addStretch(1)
        self.topLeftGroupBox.setLayout(layout)

    def createTopRightGroupBox(self):
        self.topRightGroupBox = QGroupBox("Group 2")

        defaultPushButton = QPushButton("Default Push Button")
        defaultPushButton.setDefault(True)

        togglePushButton = QPushButton("Toggle Push Button")
        togglePushButton.setCheckable(True)
        togglePushButton.setChecked(True)

        flatPushButton = QPushButton("Flat Push Button")
        flatPushButton.setFlat(True)

        layout = QVBoxLayout()
        layout.addWidget(defaultPushButton)
        layout.addWidget(togglePushButton)
        layout.addWidget(flatPushButton)
        layout.addStretch(1)
        self.topRightGroupBox.setLayout(layout)

    def createBottomLeftTabWidget(self):
        self.bottomLeftTabWidget = QTabWidget()
        self.bottomLeftTabWidget.setSizePolicy(QSizePolicy.Preferred,
                QSizePolicy.Ignored)

        tab1 = QWidget()
        tableWidget = QTableWidget(10, 10)

        tab1hbox = QHBoxLayout()
        tab1hbox.setContentsMargins(5, 5, 5, 5)
        tab1hbox.addWidget(tableWidget)
        tab1.setLayout(tab1hbox)

        tab2 = QWidget()
        textEdit = QTextEdit()

        textEdit.setPlainText("Twinkle, twinkle, little star,\n"
                              "How I wonder what you are.\n"
                              "Up above the world so high,\n"
                              "Like a diamond in the sky.\n"
                              "Twinkle, twinkle, little star,\n"
                              "How I wonder what you are!\n")

        tab2hbox = QHBoxLayout()
        tab2hbox.setContentsMargins(5, 5, 5, 5)
        tab2hbox.addWidget(textEdit)
        tab2.setLayout(tab2hbox)

        self.bottomLeftTabWidget.addTab(tab1, "&Table")
        self.bottomLeftTabWidget.addTab(tab2, "Text &Edit")

    def createBottomRightGroupBox(self):
        self.bottomRightGroupBox = QGroupBox("Group 3")
        self.bottomRightGroupBox.setCheckable(True)
        self.bottomRightGroupBox.setChecked(True)

        lineEdit = QLineEdit('s3cRe7')
        lineEdit.setEchoMode(QLineEdit.Password)

        spinBox = QSpinBox(self.bottomRightGroupBox)
        spinBox.setValue(50)

        dateTimeEdit = QDateTimeEdit(self.bottomRightGroupBox)
        dateTimeEdit.setDateTime(QDateTime.currentDateTime())

        slider = QSlider(Qt.Horizontal, self.bottomRightGroupBox)
        slider.setValue(40)

        scrollBar = QScrollBar(Qt.Horizontal, self.bottomRightGroupBox)
        scrollBar.setValue(60)

        dial = QDial(self.bottomRightGroupBox)
        dial.setValue(30)
        dial.setNotchesVisible(True)

        layout = QGridLayout()
        layout.addWidget(lineEdit, 0, 0, 1, 2)
        layout.addWidget(spinBox, 1, 0, 1, 2)
        layout.addWidget(dateTimeEdit, 2, 0, 1, 2)
        layout.addWidget(slider, 3, 0)
        layout.addWidget(scrollBar, 4, 0)
        layout.addWidget(dial, 3, 1, 2, 1)
        layout.setRowStretch(5, 1)
        self.bottomRightGroupBox.setLayout(layout)

    def createProgressBar(self):
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 10000)
        self.progressBar.setValue(0)

        timer = QTimer(self)
        timer.timeout.connect(self.advanceProgressBar)
        timer.start(1000)


def show(sys):
    """Entry point"""
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
