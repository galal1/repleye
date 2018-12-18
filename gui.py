#-------------------------------------------------------------------------------
# Name:        gui
# Purpose:     gui and functioning for eye detect and eye tracking
#
# Author:      galal
#
# Created:     10/12/2018
# Copyright:   (c) galal1_000 2018
# Licence:     GNU Lesser General Public License v3.0
#-------------------------------------------------------------------------------
import os
import sys
import re
import time
import ctypes
import eyeDetect
import coords
from pathlib import Path
from PyQt5.QtCore import pyqtSlot, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QDesktopWidget
from PyQt5.uic import loadUi
from threading import Thread


isRunningTextStarted = False
isReplayingStarted = False

def getIsRunningTextStarted():
    return isRunningTextStarted

def setIsRunningTextStarted(isItStarted):
    global isRunningTextStarted
    isRunningTextStarted = isItStarted

def getIsReplayingStarted():
    return isReplayingStarted

def setIsReplayingStarted(isItStarted):
    global isReplayingStarted
    isReplayingStarted = isItStarted

class Circle(): # object for draw the replaying
    def __init__(self, circle):
        super(Circle, self).__init__()
        self.circle = circle

    def getCircle(self):
        return self.circle

# Worker Objects managing the simulations
class WorkerForMoveText(QObject):
    startTextSignal = pyqtSignal()

    def __init__(self):
        super(WorkerForMoveText, self).__init__()

    @pyqtSlot()
    def moveRunningText(self):
        self.startTextSignal.emit()

class WorkerForChangeSpaceWidth(QObject):
    changeSpaceWidthSignal = pyqtSignal()

    def __init__(self):
        super(WorkerForChangeSpaceWidth, self).__init__()

    @pyqtSlot()
    def changeSpaceWidth(self):
        self.changeSpaceWidthSignal.emit()

class WorkerForReplayRec(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super(WorkerForReplayRec, self).__init__()

    @pyqtSlot()
    def replayRec(self):
        circle.getCircle().show()
        while 0 < len(coords.getCoords()) and getIsReplayingStarted():
            actCoord = coords.getCoords()[0]
            coords.delCoord(0)
            circle.getCircle().move(actCoord[0], actCoord[1])   # move the circle about 33 times in a sec
            app.processEvents()
            time.sleep(0.03)

        self.finished.emit()    # close the thread

# Threads what doesn't use PyQt gui elements
class ThreadingForEyeDetect(object):    # it uses eyeDetect.py
    def __init__(self):
        thread = Thread(target=self.run, args=())
        thread.daemon = True    # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        if eyeDetect.doTraining:
            print('doTraining')
            eyeDetect.setIsDoTrainingRunning(True)
            eyeDetect.mainForTraining()
        else:
            print('doFaceCheck')
            eyeDetect.main()

class ThreadingForRunRec(object):
    def __init__(self):
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        window.getCoords()


class Window(QMainWindow):  # object for gui and it's settings
    def __init__(self):
        super(Window, self).__init__()
        loadUi(os.path.join(os.getcwd() + '/datas/ui/kiserletezo_gui.ui'), self) # load .ui file (made with Qt Designer)

        self.showMaximized()    # Window setup
        screenShape = QDesktopWidget().screenGeometry()
        self.width, self.height = screenShape.width(), screenShape.height()
        self.changeWindowSize()
        self.setFixedSize(self.width, self.height)  # prevents resizing of the window

        self.runningText.setReadOnly(True)

        self.isRunning = True
        self.isTrackingInProgress = True
        self.isRunRecOn = True
        self.isCalibrationRunning = True
        self.initThreads()

        file = Path(os.path.join(os.getcwd() + "/datas/settings/saved_settings.txt"))
        if file.is_file():  # if we have saved settings load it instead
            self.loadSettings(False)
        else:
            self.changeRunningTextValueFromTextBox()

        self.initRunningTextSetup()
        self.initImportText()
        self.initRecEyeTracking()

    def initRunningTextSetup(self): # runText, scrollBarSpeed, scrollBarSpaceWidth, fontChanger, textSize, saveSetup
        self.runText.clicked.connect(self.startText)
        self.scrollBarSpeed.valueChanged.connect(self.drawScrollBarSpeedValue)
        self.scrollBarSpaceWidth.valueChanged.connect(self.setSpaceWidth)
        self.fontChanger.currentFontChanged.connect(self.changeFont)
        self.textSize.valueChanged.connect(self.changeFont)
        self.saveSetup.clicked.connect(lambda: self.saveSettings(False))
        self.drawScrollBarSpeedValue()

    def initImportText(self):   # addText, textEditEditText, chooseFile, labelChosenFileName
        self.addText.clicked.connect(self.changeRunningTextValueFromTextBox)
        self.chooseFile.clicked.connect(self.changeRunningTextValueFromFile)

    def initRecEyeTracking(self):  # runCalibration, runRec, chooseReplaySettings, replayRec
        self.runCalibration.clicked.connect(self.startCalibration)
        self.runRec.setEnabled(False)
        self.runRec.clicked.connect(self.startRec)
        self.chooseReplaySettings.clicked.connect(self.loadReplaySettings)
        self.replayRec.clicked.connect(self.startReplaying)
        self.replayRec.setEnabled(False)

    def initThreads(self):  # Threads and QThreads setup
        self.workerForMoveText = WorkerForMoveText()
        self.workerForChangeSpaceWidth = WorkerForChangeSpaceWidth()
        self.workerForReplayRec = WorkerForReplayRec()
        self.startTextThread = QThread()
        #self.startTextThread.setObjectName("startTextThread")
        self.setSpaceWidthThread = QThread()
        #self.setSpaceWidthThread.setObjectName("setSpaceWidthThread")
        self.startReplayingThread = QThread()
        #self.startReplayingThread.setObjectName("startReplayingThread")
        self.eyeDetectThread = Thread()
        self.runRecThread = Thread()

        self.workerForChangeSpaceWidth.changeSpaceWidthSignal.connect(self.changeSpaceWidth)
        self.workerForChangeSpaceWidth.moveToThread(self.setSpaceWidthThread)
        self.setSpaceWidthThread.started.connect(self.workerForChangeSpaceWidth.changeSpaceWidth)
        self.workerForMoveText.startTextSignal.connect(self.moveRunningText)
        self.workerForMoveText.moveToThread(self.startTextThread)
        self.startTextThread.started.connect(self.workerForMoveText.moveRunningText)
        self.workerForReplayRec.finished.connect(lambda: self.stopThread(self.startReplayingThread))
        self.workerForReplayRec.moveToThread(self.startReplayingThread)
        self.startReplayingThread.started.connect(self.workerForReplayRec.replayRec)

# functions for QThreads
    def stopThread(self, thread):
        #print("StopThread called for", thread.objectName())
        thread.quit()
        #thread.wait()

    def moveRunningText(self):
        if getIsReplayingStarted() is False:
            self.replayRec.setEnabled(False)    # button can't be pushed
        text = self.runningText.toPlainText()
        i = 0
        while i < len(text) and getIsRunningTextStarted():
            actualCharSize = self.getTextWidth(text[i])/500             # it depends on the size of the character for
            sleepTime = (self.getAdjustedSpeed() + actualCharSize)/4    # more balanced moving
            time.sleep(sleepTime)   # waiting time for delete the first character of the text
            self.changeRunningTextValueFromText(text[i+1:])
            app.processEvents()
            i = i + 1

        if i == len(text):
            if getIsReplayingStarted():
                self.startReplaying()
                self.runText.setEnabled(True)
                time.sleep(0.5)
                circle.getCircle().hide()
                coords.delAllCoord()
            else:
                self.startText()
        self.stopThread(self.startTextThread)

    def changeSpaceWidth(self): # called by one QThread and refresh proper gui elements
        spaces = re.search("^[\ ]+", self.getTextWithOpeningSpaces())
        textWithoutBeginSpaces = re.sub("^[\ ]+", "", self.getTextWithOpeningSpaces())
        text = list(re.sub(" +", " ", textWithoutBeginSpaces))  # delete spaces, only one remains
        spaceWidthSize = self.scrollBarSpaceWidth.value()
        index = 0
        while index < len(text):
            if text[index] == " ":
                for i in range(spaceWidthSize-1):
                    text.insert(index, " ")     # adding spaces
                index = index + spaceWidthSize
            else:
                index = index + 1

        self.changeRunningTextValueFromText(spaces.group(0) + ''.join(str(letter) for letter in text))
        self.stopThread(self.setSpaceWidthThread)

# Screen Setup for proper appearance
    def changeWindowSize(self):
    # Running Text GroupBox Setup
        self.groupBoxRunningText.setFixedSize(self.width-40, (self.height-130)/2)
        self.groupBoxRunningText.move(20, 20)
        self.graphicsViewRunningText.setFixedSize(self.width-40, (self.height-130)/2)
        self.runningText.setFixedWidth(self.width+10000)
        self.lineDown.move(0, (self.height-130)/2-1)
        self.lineDown.setFixedSize(self.width-40-1, 2)
        self.lineUp.move(0, 0)
        self.lineUp.setFixedSize(self.width-40-1, 2)
        self.lineLeft.move(0, 0)
        self.lineLeft.setFixedSize(2, (self.height-130)/2)
        self.lineRight.move(self.width-40-1, 0)
        self.lineRight.setFixedSize(2, (self.height-130)/2)
    # Running Text Setup GroupBox Setup
        self.groupBoxRunningTextSetup.move(20+self.width/3+20, (self.height-130)/2+20*2)
        self.groupBoxRunningTextSetup.setFixedSize(2*self.width/3-20*3, (self.height-((self.height-130)/2)-135)/2-10)
        self.graphicsViewRunningTextSetup.setFixedSize(2*self.width/3-20*3,
                                                       (self.height-((self.height-130)/2)-135)/2-30)
        self.scrollBarSpeed.setFixedSize(self.scrollBarSpeed.width()+10, self.scrollBarSpeed.height())
        self.scrollBarSpaceWidth.setFixedSize(self.scrollBarSpaceWidth.width()+10, self.scrollBarSpaceWidth.height())
        allSettingsSize = self.runText.width() + self.scrollBarSpeed.width() + self.scrollBarSpaceWidth.width() +\
                          self.fontChanger.width() + self.textSize.width() + self.saveSetup.width()
        betweenSpace = (2*self.width/3-20*3-allSettingsSize)/7
        innerHeight = ((self.height-((self.height-130)/2)-135)/2-30)/2+20
        self.runText.move(betweenSpace, innerHeight-15)
        self.scrollBarSpeed.move(self.runText.width() + betweenSpace*2, innerHeight-9)
        self.labelSpeed.move(self.runText.width() + betweenSpace*2, innerHeight-34)
        self.scrollBarSpaceWidth.move(self.scrollBarSpeed.width() +self.runText.width() +betweenSpace*3, innerHeight-9)
        self.labelSpaceWidth.move(self.scrollBarSpeed.width() +self.runText.width() +betweenSpace*3, innerHeight-34)
        self.fontChanger.move(self.scrollBarSpeed.width()*2 + self.runText.width() + betweenSpace*4, innerHeight-11)
        self.labelFont.move(self.scrollBarSpeed.width()*2 + self.runText.width() + betweenSpace*4, innerHeight-36)
        self.textSize.move(self.fontChanger.width() + self.scrollBarSpeed.width()*2 +
                           self.runText.width() + betweenSpace*5, innerHeight-11)
        self.labelTextSize.move(self.fontChanger.width() + self.scrollBarSpeed.width()*2 +
                                self.runText.width() + betweenSpace*5, innerHeight-36)
        self.saveSetup.move(self.textSize.width() + self.fontChanger.width() + self.scrollBarSpeed.width()*2 +
                            self.runText.width() + betweenSpace*6, innerHeight-15)
    # Import Text GroupBox Setup
        self.groupBoxImportText.move(20, (self.height-130)/2+20*2)
        self.groupBoxImportText.setFixedSize(self.width/3, self.height-((self.height-130)/2)-135)
        self.graphicsViewImportText.setFixedSize(self.width/3, self.height-((self.height-130)/2)-135-20)
        self.textEditEditText.setFixedSize(self.width/3-20, (self.height-((self.height-130)/2)-135-20)/2)
        self.labelReadFromFile.move(10, (self.height-((self.height-130)/2)-135-20)/2+80)
        self.graphicsViewImportFromFile.move(10, (self.height-((self.height-130)/2)-135-20)/2+80+20)
        self.graphicsViewImportFromFile.setFixedSize(self.width/3-20, (self.height-((self.height-130)/2)-135-20)/5.2)
        self.chooseFile.move(20,(self.height-((self.height-130)/2)-135-20)/2+80+20+
                             (self.graphicsViewImportFromFile.height()-30)/2)
        self.labelChosenFileName.move(28+self.chooseFile.width(), (self.height-((self.height-130)/2)-135-20)/2+80+20+
                                      (self.graphicsViewImportFromFile.height()-30)/2+7)
        self.labelChosenFileName.setFixedSize(self.width/3-20-self.chooseFile.width()-30, 16)
    # Rec Eye Tracking GroupBox Setup
        self.groupBoxRecEyeTracking.move(20+self.width/3+20,
                                         (self.height-130)/2+self.groupBoxRunningTextSetup.height()+20*3)
        self.groupBoxRecEyeTracking.setFixedSize(2*self.width/3-20*3, (self.height-((self.height-130)/2)-135)/2-10)
        self.graphicsViewRecEyeTracking.setFixedSize((2*self.width/3-20*3)/2,
                                                     (self.height-((self.height-130)/2)-135)/2-10-20)
        self.lineRecEyeTracking.move(50, ((self.height-((self.height-130)/2)-135-20)/2+80+20)/3)
        self.lineRecEyeTracking.setFixedSize((2*self.width/3-20*3)/2-100, 2)
        self.runCalibration.move((self.graphicsViewRecEyeTracking.width()-self.runCalibration.width())/2,
                                 (self.graphicsViewRecEyeTracking.height()+30-
                                  ((self.height-((self.height-130)/2)-135-20)/2+80+20)/3)/2)
        betweenSpaceEyeTracking = (self.graphicsViewRecEyeTracking.width() -
                                   self.runRec.width() - self.chooseReplaySettings.width() - self.replayRec.width())/4
        self.runRec.move(betweenSpaceEyeTracking*1.5, self.graphicsViewRecEyeTracking.height()/2+37)
        self.chooseReplaySettings.move(betweenSpaceEyeTracking*2 + self.runRec.width(),
                                       self.graphicsViewRecEyeTracking.height()/2+37)
        self.replayRec.move(betweenSpaceEyeTracking*2.5 + self.runRec.width() + self.chooseReplaySettings.width(),
                            self.graphicsViewRecEyeTracking.height()/2+37)
        self.graphicsViewUserName.move(20+self.graphicsViewRecEyeTracking.width(), 20)
        self.graphicsViewUserName.setFixedSize((2*self.width/3-20*3)/2-20,
                                               (self.height-((self.height-130)/2)-135)/2-10-20)
        betweenSpaceUserName = (self.graphicsViewUserName.width()-self.labelUserName.width()-self.userName.width())/3
        self.labelUserName.move(betweenSpaceUserName*2 + self.graphicsViewRecEyeTracking.width(),
                                self.graphicsViewUserName.height()/2+20-18/2)
        self.userName.move(betweenSpaceUserName*2+self.graphicsViewRecEyeTracking.width()+self.labelUserName.width(),
                                self.graphicsViewUserName.height()/2+20-30/2)

# Running Text Setup functions
    def drawScrollBarSpeedValue(self):
        self.labelSpeed.setText("Sebesség              " + str(self.scrollBarSpeed.value()))

    def makeFont(self, type, size):
        font = QFont(type, size)
        return font

    def getCurrentFontFromProperties(self):
        return self.makeFont(str(self.fontChanger.currentText()), self.textSize.value())

    def changeRunningTextFont(self, font):
        cursor = self.runningText.textCursor()
        self.runningText.selectAll()
        self.runningText.setCurrentFont(font)
        self.runningText.setTextCursor(cursor)

    def changeRunningTextValueFromText(self, text):
        self.runningText.setPlainText(text)
        self.changeFont()

    def changeFont(self):
        self.changeRunningTextFont(self.getCurrentFontFromProperties())
        self.runningText.setFixedHeight(self.textSize.value()*1.8)
        self.runningText.move(0, (self.graphicsViewRunningText.height() - self.textSize.value()*1.9)/2)

    def getTextWithOpeningSpaces(self):
        numberOfNeededSpaces = round((self.textSize.value() - 50)/1.5)
        spaces = "                                                                              "
        spaces = spaces[numberOfNeededSpaces:]
        print(numberOfNeededSpaces)
        print(len(spaces))
        return spaces + re.sub("^[\ ]+", "", self.runningText.toPlainText())

    def getTextWidth(self, text):   # get width of the characters in moving text (for size 100)
        class SIZE(ctypes.Structure):
            _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

        hdc = ctypes.windll.user32.GetDC(0)
        hfont = ctypes.windll.gdi32.CreateFontA(
            100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, self.fontChanger.currentText())
        hfont_old = ctypes.windll.gdi32.SelectObject(hdc, hfont)

        size = SIZE(0, 0)
        ctypes.windll.gdi32.GetTextExtentPoint32A(hdc, text, len(text), ctypes.byref(size))

        ctypes.windll.gdi32.SelectObject(hdc, hfont_old)
        ctypes.windll.gdi32.DeleteObject(hfont)

        return size.cx

    def getAdjustedSpeed(self):
        return 1-self.scrollBarSpeed.value()/16

    def startText(self):
        if self.isRunning and len(self.runningText.toPlainText()) > 0:
            setIsRunningTextStarted(True)
            self.runText.setText('◼')
            self.startTextThread.start()
            self.isRunning = False
        else:
            setIsRunningTextStarted(False)
            self.runText.setText('⏵')
            self.isRunning = True

    def setSpaceWidth(self):
        self.setSpaceWidthThread.start()
        self.labelSpaceWidth.setText("Szóköz szélesség   " + str(self.scrollBarSpaceWidth.value()))

    def saveSettings(self, forEyeTracking):
        if forEyeTracking:
            whichText = self.runningText.toPlainText().split()
            completeName = os.path.join(os.getcwd() + "/datas/settings", "saved_settings_-_{}_-_{}_{}.txt".format(
                                        self.userName.toPlainText(), whichText[0].lower(), whichText[1].lower()))
            textFile = open(completeName, "w")
        else:
            textFile = open(os.path.join(os.getcwd() + "/datas/settings/saved_settings.txt"), "w")
        textFile.write('{}\n{}\n{}\n{}\n{}'.format(self.scrollBarSpeed.value(),
                        self.scrollBarSpaceWidth.value(),
                        self.textSize.value(),
                        str(self.fontChanger.currentText()),
                        re.sub("^[\ ]+", "", self.runningText.toPlainText())))
        textFile.close()

    def loadSettings(self, forEyeTracking):
        if forEyeTracking:  # load settings for replay recording
            if getIsReplayingStarted(): # before you can choose one file, stop the replaying first
                self.startReplaying()
            filePath = QFileDialog.getOpenFileName(self, 'Single File', "./datas/settings", '*.txt')[0]
            if filePath != "":
                if isReplayingStarted:
                    self.startReplaying()
                textFile = open(filePath, "r")
                coordFilePathEnd = re.search("_-_.+", filePath)
                if coordFilePathEnd is not None:    # texts which not belong to coordinates is not movable
                    coordFilePath = os.path.join(os.getcwd() + "/datas/coords/saved_coords" + coordFilePathEnd.group(0))
                    with open(coordFilePath) as file:
                        circle.getCircle().hide()
                        coords.delAllCoord()
                        for line in file:
                            coordString = (re.findall('[\d.]+', line))
                            coord = [float(coordString[0]), float(coordString[1])]
                            coords.appendCoords(coord)
                    self.replayRec.setEnabled(True)
                    self.runText.setEnabled(False)
            else:
                return
        else:   # load simple setting when the program starts
            textFile = open(os.path.join(os.getcwd() + "/datas/settings/saved_settings.txt"), "r")

        scrollBarSpeed = int(textFile.readline())
        scrollBarSpaceWidth = int(textFile.readline())
        textSize = int(textFile.readline())
        font = self.makeFont(textFile.readline(), textSize)
        self.changeEditTextValue(textFile.readline())
        textFile.close()

        self.changeRunningTextValueFromTextBox()
        self.scrollBarSpeed.setValue(scrollBarSpeed)
        self.scrollBarSpaceWidth.setValue(scrollBarSpaceWidth)
        self.fontChanger.setCurrentFont(font)
        self.textSize.setValue(textSize)

        self.changeRunningTextFont(font)
        self.setSpaceWidth()

# Import Text functions
    def changeRunningTextValueFromTextBox(self):
        text = self.textEditEditText.toPlainText()
        spaces = "                                                                              "   # for not show text for a moment because of the line break replacement
        self.changeRunningTextValueFromText(spaces + re.sub("\n+", " ", text))   # change line breaks to space
        self.setSpaceWidth()

    def changeRunningTextValueFromFile(self):
        filePath = QFileDialog.getOpenFileName(self, 'Single File', "./datas/", '*.txt')[0]

        if filePath != "":
            self.labelChosenFileName.setText("\"" + os.path.split(filePath)[1] + "\"" + " fájl kiválasztva.")
            file = open(filePath, "r")
            lines = file.readlines()
            self.textEditEditText.clear()
            for line in lines:
                self.textEditEditText.insertPlainText(line)
            file.close()
            self.changeRunningTextValueFromTextBox()    # change text in running text too

    def changeEditTextValue(self, text):
        self.textEditEditText.setPlainText(text)
        self.textEditEditText.setFont(self.makeFont('MS Shell Dlg 2', 11))

# Rec Eye Tracking functions
    def startCalibration(self):   # eye detecting
        if self.isCalibrationRunning:
            self.eyeDetectThread = ThreadingForEyeDetect()
            self.runRec.setEnabled(True)
            self.runCalibration.setText("Kalibráció bezárása")
            self.isCalibrationRunning = False
        else:
            print("calibration")
            eyeDetect.setIsDoTrainingRunning(False)
            self.runRec.setEnabled(False)
            self.runCalibration.setText("Kalibráció indítása")
            self.isCalibrationRunning = True

    def startRec(self): # starts one QThread and refresh proper gui elements
        if self.isRunRecOn and len(self.runningText.toPlainText()) > 0: # if there isn't text no run rec
            self.saveSettings(True)
            self.isTrackingInProgress = True
            setIsRunningTextStarted(True)
            self.runRec.setText('◼')
            self.startTextThread.start()
            self.runRecThread = ThreadingForRunRec()
            self.isRunRecOn = False
        else:
            self.isTrackingInProgress = False
            setIsRunningTextStarted(False)
            self.runRec.setText('●')
            self.isRunRecOn = True

    def getCoords(self):    # get coordinates for gaze direction
        whichText = self.runningText.toPlainText().split()
        completeName = os.path.join(os.getcwd() + "/datas/coords",
                                    "saved_coords_-_{}_-_{}_{}.txt".format(self.userName.toPlainText(),
                                    whichText[0].lower(), whichText[1].lower()))
        fileForCoord = open(completeName, "w")
        while self.isTrackingInProgress is True:
            fileForCoord.write('{} {}\n'.format(eyeDetect.getGazeCoords()[0] - circle.getCircle().width()/2,
                                                eyeDetect.getGazeCoords()[1] - circle.getCircle().height()/2))
            time.sleep(0.03)   # write about 33 coordinates in a sec to a file
        fileForCoord.close()

    def loadReplaySettings(self):
        self.loadSettings(True)

    def startReplaying(self):   # starts one QThread and refresh proper gui elements
        if self.isRunning and len(coords.getCoords()) > 0:
            setIsRunningTextStarted(True)
            setIsReplayingStarted(True)
            self.replayRec.setText('◼')
            self.startTextThread.start()
            self.startReplayingThread.start()
            self.isRunning = False
        else:
            setIsRunningTextStarted(False)
            setIsReplayingStarted(False)
            self.replayRec.setText('⏵')
            self.isRunning = True



app = QApplication(sys.argv)
appid = 'mycompany.myproduct.subproduct.version'    # arbitrary string (for taskbar icon)
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

window = Window()
window.setWindowTitle('Kísérletező felhasználói felületet')
window.setWindowIcon(QIcon(os.path.join(os.getcwd() + '/datas/images/logo.png')))
window.show()

coords = coords.Coords()
circle = Circle(window.circle)
circle.getCircle().setPixmap(QPixmap(os.path.join(os.getcwd() + "/datas/images/gaussianBlur.png")))
circle.getCircle().hide()

sys.exit(app.exec_())