import time
import serial
import random

# 搜尋可用com port
import serial.tools.list_ports

coms = serial.tools.list_ports.comports()
for a in coms:
    print(a)

ser = serial.Serial('COM27', 115200, timeout=1)
ser.flushInput()
ser.set_buffer_size(rx_size=1000000)
ser.isOpen()

voltageScale = 3.3 / 1024
sampleEveryMicroSecond = 343  # 343.5us
currentResistor = 10  # ohm
currentLevel = 3  # mA
timeOut = 0.3  # second

timeTag = 0
dataCount = 0
count = 0
voltageSum = 0
sampleCount = 1
showCurrent = 0
voltage = 0
tStart = time.time()
currentTable = []
lastlocalTime = ""
newDataFlag = True
zeroCount = 0
timeShow = False
oldTimeTag = 0
tStart0 = time.time()
pEND1 = time.time()
continueTime = 0
state = 0
exeOnlyOneTime = True

filename = "Current_" + time.strftime("%Y%m%d%H%M", time.localtime()) + ".txt"
f = open(filename, 'w')
f.close()

print('===========================================')
print('===========================================')
print('===========================================')

# while( int(time.strftime("%H%M%S"))<174430 ):
#    print("Wait-- " + str(time.strftime("%H:%M:%S", time.localtime())))
#    time.sleep(10)

try:
    while True:
        if state == 0:
            continueTime = 72 * 60 * 60
            pEND = time.time()
            if exeOnlyOneTime:
                exeOnlyOneTime = False
                filename = "Current_" + time.strftime("%Y%m%d%H%M", time.localtime()) + "_T3.txt"
                f = open(filename, 'w')
                f.close()
                print(filename)
            if (pEND - tStart0) > continueTime:
                pEND1 = time.time()
                state = 2
                exeOnlyOneTime = True

        elif state == 1:
            continueTime = (23 * 60 * 60) + (55 * 60)
            # continueTime = 5*60
            while ((pEND1 - pEND) < continueTime):
                pEND1 = time.time()
                print("Wait-- " + str(time.strftime("%H:%M:%S", time.localtime())))
                time.sleep(60)
            pEND1 = time.time()
            state = 2

        elif state == 2:
            continueTime = 48 * 60 * 60
            pEND = time.time()
            if exeOnlyOneTime:
                exeOnlyOneTime = False
                filename = "Current_" + time.strftime("%Y%m%d%H%M", time.localtime()) + "_T1T2.txt"
                f = open(filename, 'w')
                f.close()
                print(filename)
            if (pEND - tStart1) > continueTime:
                pEND1 = time.time()
                state = 3
                exeOnlyOneTime = True

        elif state == 3:
            continueTime = 72 * 60 * 60
            pEND = time.time()
            if exeOnlyOneTime:
                exeOnlyOneTime = False
                filename = "Current_" + time.strftime("%Y%m%d%H%M", time.localtime()) + "_T3.txt"
                f = open(filename, 'w')
                f.close()
                print(filename)
            if (pEND - tStart1) > continueTime:
                pEND1 = time.time()
                state = 4
                exeOnlyOneTime = True
                break
               
        elif state == 4:
            break

        if ser.in_waiting:
            data_raw = ser.readline()
            try:
                adcValue = (data_raw[0] * 256) + data_raw[1]
                voltage = round(adcValue * voltageScale, 6)
            except:
                print('Try again')
                
           

            voltageSum += voltage
            showCurrent = round((voltageSum / sampleCount), 5)
            showCurrent = round(showCurrent * 1000, 5)
            showCurrent = round(showCurrent / currentResistor, 5)

            if showCurrent > currentLevel:
                tStart = time.time()
                timeTag = round(((dataCount * sampleEveryMicroSecond) / 1000), 6)
                timeTag = str(timeTag)

                if newDataFlag == True:
                    localTime = time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime())
                    lastTime = localTime.split(", ")
                    lastTime = lastTime[1]
                    newDataFlag = False
                else:
                    localTime = "-, -"

                if timeShow == True:
                    localTime = time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime())
                    lastTime = localTime.split(", ")
                    lastTime = lastTime[1]
                    timeShow = False
                else:
                    if (float(timeTag) - oldTimeTag) >= 1000:
                        timeShow = True
                        oldTimeTag = float(timeTag)

                showCurrent = str(showCurrent)
                showData = localTime + ", " + timeTag + " mS, " + showCurrent + " mA"
                currentTable.append(showData)

                # print(showData)

                dataCount += 1

                if dataCount > 291550:
                    tatalmAmS = 0
                    f = open(filename, 'a+')
                    for i in currentTable:
                        data = i.split(", ")
                        current = float(data[3].replace(" mA", ""))
                        if current < 330:
                            mAmS = current / (1 / (sampleEveryMicroSecond / 1000))
                            tatalmAmS += mAmS
                            f.write(i + "\n")

                    tatalmAmS = round(tatalmAmS, 6)
                    totalmAH = (tatalmAmS / 1000) / 3600
                    totalmAH = format(totalmAH, '.10f')

                    f.write(data[0] + ", " + lastTime + ", " + timeTag + " mS, 0 mA, " + str(
                        tatalmAmS) + " mA/mS, " + str(totalmAH) + " mAH")
                    f.write("\n")

                    f.close()
                    currentTable.clear()
                    newDataFlag = True
                    ser.flushInput()

                    print("Time= " + time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime()))
                    print("dataCount= " + str(round(((dataCount * sampleEveryMicroSecond) / 1000), 6)) + "ms")
                    dataCount = 0
                    print(str(tatalmAmS) + " mA/mS")
                    print(str(totalmAH) + " mAH")
                    print("Write to File")
                    print("")

                zeroCount = 0
            else:
                tEnd = time.time()
                tatalmAmS = 0
                zeroCount += 1
                # if (tEnd - tStart) > timeOut or zeroCount > int((timeOut * 1000) / (sampleEveryMicroSecond / 1000)):
                if (tEnd - tStart) > timeOut:
                    tStart = time.time()
                    zeroCount = 0
                    if len(currentTable) > 0:
                        f = open(filename, 'a+')
                        for i in currentTable:
                            data = i.split(", ")
                            current = float(data[3].replace(" mA", ""))
                            if current < 330:
                                mAmS = current / (1 / (sampleEveryMicroSecond / 1000))
                                tatalmAmS += mAmS
                                f.write(i + "\n")

                        tatalmAmS = round(tatalmAmS, 6)
                        totalmAH = (tatalmAmS / 1000) / 3600
                        totalmAH = format(totalmAH, '.10f')

                        if timeTag!='0.0':
                             f.write(data[0] + ", " + lastTime + ", " + timeTag + " mS, 0 mA, " + str(
                                 tatalmAmS) + " mA/mS, " + str(totalmAH) + " mAH")
                             f.write("\n")

                        
                             currentTable.clear()
                             newDataFlag = True
                             ser.flushInput()

                             print("Time= " + time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime()))
                             print("dataCount= " + str(round(((dataCount * sampleEveryMicroSecond) / 1000), 6)) + "ms")
                             dataCount = 0
                             print(str(tatalmAmS) + " mA/mS")
                             print(str(totalmAH) + " mAH")
                             print("Write to File X")
                             print("")
                        f.close()
            count = 0
            voltageSum = 0



except KeyboardInterrupt:
    ser.close()  # 清除序列通訊物件
    print('再見！')

ser.close()  # 清除序列通訊物件
print('再見！')
