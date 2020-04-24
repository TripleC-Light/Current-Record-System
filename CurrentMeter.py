# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import os
import webbrowser
import serial
import requests
import time
import serial.tools.list_ports
import random

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        global ser
        _cmd = self.get_argument('cmd', '')

        if _cmd == 'CheckState':
            self.write(self.checkState())

        elif _cmd == 'connectUART':
            _comInd = self.get_argument('serialIndex', '')
            _com = getSerialInfo()
            _com = _com.split(',')
            _com = _com[int(_comInd)].split(' - ')
            try:
                ser = serial.Serial(_com[0], 9600, timeout=1)
                ser.flushInput()
                ser.isOpen()
                print('> ' + _com[0] + ' 開啟')
                self.write('OK')
            except:
                self.write('ERROR')

        elif _cmd == 'disConnectUART':
            try:
                ser.close()  # 清除序列通訊物件
                print('> 串列埠中斷')
                self.write('OK')
            except:
                self.write('ERROR')

        elif _cmd != '':
            print("cmd from web= " + _cmd)
            dataReturn = self.sendCMDfromWEB(_cmd)
            # print("dataReturn= " + str(dataReturn))
            if dataReturn != False:
                dataReturn = dataReturn.split(' ')
                print(dataReturn)
                if len(dataReturn) > 1 and dataReturn[1] != '':
                    self.write('OK ' + dataReturn[1])
                else:
                    dataReturn[0] = dataReturn[0].replace('\n', '')
                    self.write(dataReturn[0])
            ser.flushInput()  # 清除初始化文字

        else:
            self.render('index.html')

    def sendCMDfromWEB(self, _cmd):
        timeOut = 5  # Timeout 5s
        _cmd = _cmd.split('*')
        print("Address= " + _cmd[0])
        ser.write(str.encode(_cmd[0] + '\n'))

        ser.flushInput()  # 清除Buffer
        tStart = time.time()
        while self.getReturn() == '':
            tEnd = time.time()
            if tEnd - tStart > timeOut:
                print("Set Address TimeOut")
                self.write('ERR Set_Address_TimeOut')
                return False

        print("CMD= " + '*' + _cmd[1])
        ser.write(str.encode('*' + _cmd[1] + '\n'))

        ser.flushInput()  # 清除Buffer
        tStart = time.time()
        dataReturn = ''
        while dataReturn == '':
            dataReturn = self.getReturn()
            tEnd = time.time()
            if tEnd - tStart > 30:
                print("Function Execute TimeOut")
                self.write('ERR Function_Execute_TimeOut')
                return False
        return dataReturn

    def getReturn(self):
        if ser.in_waiting:
            dataRev = ser.readline().decode()  # 接收回應訊息並解碼
            print('Master send: ', dataRev)
            return dataRev
        else:
            return ''

    def checkState(self):
        if ser.in_waiting:
            dataRev = ''
            isOKorNOT = ''
            while isOKorNOT != ('OK\r\n'):
                dataRev = ser.readline().decode()  # 接收回應訊息並解碼
                isOKorNOT = dataRev.split(' ')
                isOKorNOT = isOKorNOT[0]
            print('Master send: ', dataRev)
            return 'OK'
        else:
            return 'NOT OK'


class SerialConnectHandler(tornado.web.RequestHandler):
    def get(self):
        _cmd = self.get_argument('cmd', '')
        if _cmd == 'getList':
            self.write(getSerialInfo())

def getSerialInfo():
    _comList = ''
    coms = serial.tools.list_ports.comports()   # 搜尋可用com port
    # print('可用Com port 如下:')
    for com in coms:
        _comList += str(com) + ','
        # print(com)
    # print(_comList)
    return _comList

if __name__ == "__main__":
    global ser

    try:
        handlers = [[r'/index', IndexHandler],
                    [r'/serialconnect', SerialConnectHandler]]

        webApp = tornado.web.Application(
            handlers,
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True
        )
        webApp.listen(8888)
        url = 'http://localhost:8888/index'
        # webbrowser.open(url=url, new=0)
        print('Server open in: ' + url)
        tornado.ioloop.IOLoop.instance().start()

    except KeyboardInterrupt:
        ser.close()  # 清除序列通訊物件
        print('再見！')

