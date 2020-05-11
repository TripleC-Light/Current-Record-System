import time
import serial
import random

# 搜尋可用com port
import serial.tools.list_ports

class CurrentOperate:
    def __init__(self):
        self.refVoltage = 0
        self.ADCresolution = 0
        self.voltageScale = self.refVoltage / (2**self.ADCresolution)
        self.sampleResistor = 0    #ohm
        self.currentTable = []
        self.tatalmAmS = 0
        self.totalmAH = 0
        self.sampleEveryMicroSecond = 0
        self.filename = ''

    def get_mA(self, adcValue):
        _voltage = round(adcValue * self.voltageScale, 6)
        _current = round(_voltage / self.sampleResistor, 6)
        _current = round(_current * 1000, 6)                  #change unit from A to mA
        return _current

    def get_TotalmAmS(self, currentTable):
        self.currentTable = currentTable
        _tatalmAmS = 0
        _mS = (self.sampleEveryMicroSecond/1000) / 1    # 每一個 sample time佔 1ms的多少
        maxCurrent = (self.refVoltage / self.sampleResistor) * 1000     # mA
        for _current in self.currentTable:
            data = _current.split(", ")
            _current = float(data[3].replace(" mA", ""))
            if _current < maxCurrent:
                mAmS = _current * _mS   # 此次 sample current乘上取樣時間在 1ms的佔比, 即為每 1ms的電流
                _tatalmAmS += mAmS
        self.tatalmAmS = round(_tatalmAmS, 6)
        return self.tatalmAmS

    def get_TotalmAH(self, tatalmAmS):
        _totalmAH = (tatalmAmS / 1000) / 3600   # 先將 mA/mS轉換為 mAS, 再轉換為 mAH
        self.totalmAH = format(_totalmAH, '.10f')
        return self.totalmAH

    def writeToFile(self):
        passFirstData = True
        _date = self.currentTable[0].split(', ')[0]
        _time = self.currentTable[0].split(', ')[1]
        f = open(self.filename, 'a+')
        f.write(self.currentTable[0] + "\n")
        for currentData in self.currentTable:
            currentData = currentData.split(", ")
            current = float(currentData[3].replace(" mA", ""))
            if current < 330:
                if passFirstData:
                    passFirstData = False
                else:
                    writeData = '-, -, ' + currentData[2] + ', ' + currentData[3]
                    f.write(writeData + "\n")

        writeData = _date + ", " + _time + ", " + currentData[2] + ", 0, " + str(self.tatalmAmS) + ', ' + str(self.totalmAH)
        f.write(writeData + "\n")
        f.close()
        print("> Write to File")


class TimeCtrl:
    def __init__(self):
        self.sampleEveryMicroSecond = 0
        self.tag = 0
        self.count = 0
        self.timeOut = 0

    def getCount(self):
        _tmp = self.count
        self.count += 1
        return _tmp

    def clrTag(self):
        self.count = 0
        self.tag = 0

    def updateTag(self):
        self.tag = str(round(((self.getCount() * self.sampleEveryMicroSecond) / 1000), 6))
        return self.tag

    def getTime(self):
        return time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime())


class InitialSystem:
    def __init__(self, current, timeCtrl):
        self.createLogFile()
        self.initHWsetting(current)
        self.initTimeCtrl(timeCtrl)
        self.filename = ''

    def createLogFile(self):
        self.filename = "CurrentV4_" + time.strftime("%Y%m%d%H%M", time.localtime()) + ".txt"
        # self.filename = "CurrentV4.txt"
        f = open(self.filename, 'w')
        f.write('Date, Time, Tag, mA, mA/mS, mAH' + "\n")
        f.close()
        print('> Create File:', self.filename)

    def initHWsetting(self, current):
        current.refVoltage = 3.3
        current.ADCresolution = 10
        current.sampleResistor = 10    #ohm
        current.sampleEveryMicroSecond = 343
        current.filename = self.filename

    def initTimeCtrl(self, timeCtrl):
        timeCtrl.sampleEveryMicroSecond = 343
        timeCtrl.timeOut = 0.3

coms = serial.tools.list_ports.comports()
for a in coms:
    print(a)

ser = serial.Serial('COM27', 115200, timeout=1)
ser.flushInput()
ser.set_buffer_size(rx_size=1000000)
ser.isOpen()

adcValue = 0
currentLevel = 3  # mA

tStart = time.time()
tStart0 = tStart
state = 0
exeOnlyOneTime = True
currentTable = []

print('===========================================')
current = CurrentOperate()
timeCtrl = TimeCtrl()
ser.flushInput()

InitialSystem(current, timeCtrl)

try:
    while True:
        if state == 0:
            continueTime = 30 * 60 * 60
            # continueTime = 15
            pEND = time.time()
            if exeOnlyOneTime:
                exeOnlyOneTime = False
            if (pEND - tStart0) > continueTime:
                break

        if ser.in_waiting:
            goodADCvalue = True
            rawData = ser.readline()
            try:
                adcValue = (rawData[0] * 256) + rawData[1]
            except:
                goodADCvalue = False
                print('Try again')

            if goodADCvalue:
                newCurrent = current.get_mA(adcValue)
                localTime = timeCtrl.getTime()
                if newCurrent > currentLevel:
                    tStart = time.time()
                    timeCtrl.updateTag()
                    showData = localTime + ", " + str(timeCtrl.tag) + ", " + str(newCurrent) + ""
                    currentTable.append(showData)
                else:
                    tEnd = time.time()
                    if (tEnd - tStart) > timeCtrl.timeOut and len(currentTable) > 0:
                        tStart = time.time()
                        totalmAmS = current.get_TotalmAmS(currentTable)
                        totalmAH = current.get_TotalmAH(totalmAmS)
                        print("")
                        print("Time= " + localTime)
                        print("Data Length= " + str(timeCtrl.tag) + "ms")
                        print(str(totalmAmS) + " mA/mS")
                        print(str(totalmAH) + " mAH")
                        current.writeToFile()
                        timeCtrl.clrTag()
                        currentTable.clear()

except KeyboardInterrupt:
    ser.close()  # 清除序列通訊物件

ser.close()  # 清除序列通訊物件
print('再見！')
