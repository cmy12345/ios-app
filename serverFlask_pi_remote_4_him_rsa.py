# coding:utf8
import hashlib
from io import BytesIO
import json
import time
# import spidev
import struct
import requests
import time
from json import dumps

from flask import Flask, render_template, Response
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask import request, send_from_directory
from flask_cors import CORS

import pymysql
import json
import pickle
import requests
import csv
import os
import time

import pymysql.cursors
import pandas as pd

import base64
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.Hash import SHA
from urllib.parse import quote, unquote

import base64
import rsa.common
from Crypto.PublicKey import RSA

# from requests.packages import urllib3

# urllib3.disable_warnings()

import tkinter as tk
from tkinter import messagebox

LocalDeviceID = "picharger01"

app = Flask(__name__, template_folder='/home/pi/Longmax/html', static_folder='/home/pi/Longmax/html',
            static_url_path='')
app.debug = True
# def after_request(resp):
#    resp.headers['Access-Control-Allow-Origin'] = '*'
#    return resp

# app.after_request(after_request)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root: @127.0.0.1:3306/longmax"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
_host = "0.0.0.0"
_port = 5000

db = SQLAlchemy(app)

_private_pem_device = None
_public_pem_device = None

####SPI_initialization
# Parameters for SPI
bus = 0  # We only have SPI bus o available to us on Pi
device = 0  # Device is the chip select pin (depending on the connection. CE0 now)
# Enable SPI and open connection:

"""
spi = spidev.SpiDev()
spi.open(bus, device)
spi.max_speed_hz = 3900000 #3.9 MHz
spi.mode = 0b00
t2 = time.time()
cnt = 1
filename1 = '/home/pi/Longmax/LocalSPI_CMD/Local_' + str(t2) + '.txt'
time.sleep(1)
"""

number = [999999999, 999999999]  # Initialization for the Services Panel SPI communication
ACK_kWh = 0
ACK_State = 0


################### RSA Encryption/Decryption and Create/Verify Signature #################
def rsaEncodeDB(remoteDeviceID, text):
    sql1 = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (remoteDeviceID)
    db1 = pymysql.connect('localhost','pi','1234','longmax')
    cursor1 = db1.cursor()
    cursor1.execute(sql1)
    result = cursor1.fetchall()
    public_pem_pre = result[0][2]
    public_pem = bytes(public_pem_pre, encoding="utf8")
    a = bytes(text, encoding="utf8")
    rsakey = RSA.importKey(public_pem)
    cipher = Cipher_pkcs1_v1_5.new(rsakey)
    cipher_text = base64.b64encode(cipher.encrypt(a))
    return cipher_text


def rsaEncode(remoteDeviceID, text):
    with open("public_" + remoteDeviceID + ".pem", "rb+") as f:
        public_pem = f.read()
        a = bytes(text, encoding="utf8")
        rsakey = RSA.importKey(public_pem)
        cipher = Cipher_pkcs1_v1_5.new(rsakey)
        cipher_text = base64.b64encode(cipher.encrypt(a))
    return cipher_text


def rsaDecode(localDeviceID, text):
    # print(type(text))
    with open("private_" + localDeviceID + ".pem", "rb+") as f:
        private_pem = f.read()
        decodeStr = base64.b64decode(text)
        prikey = Cipher_pkcs1_v1_5.new(RSA.importKey(private_pem))
        decry_text = prikey.decrypt(decodeStr, b'rsa')
        decry_value = decry_text.decode('utf8')
    return decry_value


def createSignature(localDeviceID, text):
    with open("private_" + localDeviceID + ".pem", "rb+") as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        signer = Signature_pkcs1_v1_5.new(rsakey)
        digest = SHA.new()
        digest.update(text.encode("utf8"))
        sign = signer.sign(digest)
        signature = base64.b64encode(sign)
    return signature


def verifySignature(remoteDeviceID, signature, text):
    # print(text)
    # print(type(text))
    with open("public_" + remoteDeviceID + ".pem", "rb+") as f:
        key = f.read()
        rsakey = RSA.importKey(key)
        verifier = Signature_pkcs1_v1_5.new(rsakey)
        digest = SHA.new()
        digest.update(text.encode("utf8"))
        is_verify = verifier.verify(digest, base64.b64decode(signature))
    return is_verify


###################### Command Conversion for SPI ##########################
def intConversion(ls):  # The function to convert the shifted binary data sent by TIC2000 to float
    # Shift the binary bits left by 1 digit
    string = ''
    for i in range(len(ls)):
        binary_element = bin(int(ls[i]))
        binary_element = binary_element[2:]
        if len(binary_element) < 8:
            binary_element = '0' * (8 - len(binary_element)) + binary_element
        string += binary_element
    string = string[1:] + '0'
    print(string)
    # Convert the shifted binary bit to the float (32 bit floating point) 
    exponent = 0
    for i in range(1, 9):
        if string[i] == '1':
            exponent += 2 ** (8 - i)
    mantissa = 1
    for i in range(9, 32):
        if string[i] == '1':
            mantissa += 2 ** (8 - i)
    flt = 2 ** (exponent - 127) * mantissa
    flt = round(flt, 3)
    return flt

    ##currently not used


def unsign2hex(ls):  # The function to convert the shifted binary data sent by TIC2000 to hex
    string = ''
    for i in range(len(ls)):
        binary_element = bin(int(ls[i]))
        binary_element = binary_element[2:]
        if len(binary_element) < 8:
            binary_element = '0' * (8 - len(binary_element)) + binary_element
        string += binary_element
    string = string[1:] + '0'
    res = hex(int(string, 2))
    return res


# Python SPI send 8 bit integer per time, TIC2000 buffer size is 32-bit float. Thus to get 32-bit float, each time RPI send 4 * 8-bit integer
# The first two integer are the prefix for the TI to decode
def CMDConversion(Mode, number):  # convert the formating of 32-bit sending data to be the one TI can decode
    Modes = ['M', 'S', 'PF', 'PP', 'PN', 'QP', 'QN', 'OnOff', 'Current', 'kWh']
    prefix = [17, 34, 51, 68, 85, 102, 119, 136, 153,
              18]  # prefix to be converted in to hex number, which can be used as the flag for each mode through SPI communication
    # 17--> 0x11, 43 --> 0x22, 51 --> 0x33, 68 --> 0x44, 85 --> 0x55, 102 --> 0x66, 119 --> 0x77, 139 --> 0x88, 153 --> 0x99, 18 --> 0x12
    a = [0x00, 0x00, 0x00, 0x00]
    i = Modes.index(Mode)
    if i == 0:  # Mode
        number = int(number)
        if number > 4:
            print('[Mode] Invalid Input')
        else:
            a = [prefix[i], prefix[i], 0x00, number]
    elif i == 1:  # State
        if abs(number) > 4:
            print('[State] Invalid Input')
        else:
            number = int(number + 16)
            a = [prefix[i], prefix[i], 0x00, number]
    elif i == 2:  # Power Factor
        number = number * 1000
        number1 = int(number // 256)
        number2 = int(number % 256)
        a = [prefix[i], prefix[i], number1, number2]
    elif i == 3:  # Positive Real Power
        if number > 65535 or number < 0:
            print('[P+] Invalid Input')
        else:
            number1 = int(number // 256)
            number2 = int(number % 256)
            a = [prefix[i], prefix[i], number1, number2]
    elif i == 4:  # Negative Real Power
        if number < -65535 or number > 0:
            print('[P-] Invalid Input')
        else:
            number = abs(number)
            number1 = int(number // 256)
            number2 = int(number % 256)
            a = [prefix[i], prefix[i], number1, number2]
    elif i == 5:  # Positive Reactive Power
        if number > 65535 or number < 0:
            print('[Q+] Invalid Input')
        else:
            number1 = int(number // 256)
            number2 = int(number % 256)
            a = [prefix[i], prefix[i], number1, number2]
    elif i == 6:  # Negative Reactive Power
        if number < -65535 or number > 0:
            print('[Q-] Invalid Input')
        else:
            number = abs(number)
            number1 = int(number // 256)
            number2 = int(number % 256)
            a = [prefix[i], prefix[i], number1, number2]
    elif i == 7:  # OnOff
        if number == 1:
            a = [prefix[i], prefix[i], 0x00, 1]
        elif number == 2:
            a = [prefix[i], prefix[i], 0x00, 2]
        else:
            print('[OnOff] Invalid Input')
    elif i == 8:  # Current (only positive)
        if number > 65535 or number < 0:
            print('[Current] Invalid Input')
        else:
            number = abs(number)
            number1 = int(number // 256)
            number2 = int(number % 256)
            a = [prefix[i], prefix[i], number1, number2]
    elif i == 9:  # kWh (only positive)
        if number > 65535 or number < 0:
            print('[kWh] Invalid Input')
        else:
            number = abs(number)
            number1 = int(number // 256)
            number2 = int(number % 256)
            a = [prefix[i], prefix[i], number1, number2]
    b_list = a * 8
    return b_list, i


# Send the data (command, value) through SPI.
def sendSPI(Mode, number):
    Modes = ['M', 'S', 'PF', 'PP', 'PN', 'QP', 'QN', 'OnOff', 'Current', 'kWh']
    params = [0, 1, 2, 3, 3, 4, 4, 5, 6, 7]
    param = params[Modes.index(Mode)]
    print(Mode, number, param)
    ack = "NA"
    while True:
        global flt
        global flt1
        # global cnt
        t1 = time.time()
        ####### Load 8 Data ######
        line = str(t1)
        line1 = str(t1)
        data = [t1]
        data1 = [t1]
        # convert the command to the format that TI can decode
        b_list, i = CMDConversion(Mode, number)
        print(b_list)
        b = spi.xfer2(b_list)
        spi.close()
        print(len(b))
        # print(b)
        for i in range(8):
            a1 = b[4 * i:(4 * i + 4)]
            flt1 = intConversion(a1)
            data1.append(flt1)
            i += 1
        print(data1)
        print(data1[4], type(data1[4]), param, type(param))
        spi.open(bus, device)
        spi.max_speed_hz = 3900000  # 3.9 MHz
        spi.mode = 0b00
        # resp = spi.xfer2([0x11,0x11,0x11,0x12,0x11,0x13,0x11,0x14,0x11,0x11,0x11,0x12,0x11,0x13,0x11,0x14])
        time.sleep(2)
        t2 = time.time()
        if int(data1[4]) == param:
            print("##########################")
            ack = data1
            return ack
            break
        time.sleep(5)
    return ack


########################################################## Web Visualization  ##########################################################
#######  Route for Data Visualization on Web App ######
@app.route('/PROTOTYPE_V2/getall', methods=['POST', 'GET'])
def get_all():
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'nie',  # mysql database user
        'password': 'nie',
        'db': 'longmax',  # database name
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }
    con = pymysql.connect(**config)
    try:
        with con.cursor() as cursor:
            sql = """SELECT * FROM (SELECT * FROM PROTOTYPE_V3 ORDER BY time DESC LIMIT 30) sub ORDER BY time ASC"""
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)
    finally:
        con.close();
    df = pd.DataFrame(result)

    data = []
    for i in range(30):
        temp = {
            'time': str(round(float(df.iat[i, 0]), 4)),
            'data_1': str(float(df.iat[i, 1])),
            'data_2': str(float(df.iat[i, 2])),
            'data_3': str(float(df.iat[i, 3])),
            'data_4': str(float(df.iat[i, 4])),
            'data_5': str(float(df.iat[i, 5])),
            'data_6': str(float(df.iat[i, 6])),
            'data_7': str(float(df.iat[i, 7])),
            'data_8': str(float(df.iat[i, 8]))
        }
        data.append(temp);
    print(data)
    return jsonify({'result': data})


@app.route('/PROTOTYPE_V2_01/getall', methods=['POST', 'GET'])
def get_all_01():
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'nie',  # mysql database user
        'password': 'nie',
        'db': 'longmax',  # database name
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }
    con = pymysql.connect(**config)
    try:
        with con.cursor() as cursor:
            sql = """SELECT * FROM (SELECT * FROM PROTOTYPE_V3 ORDER BY time DESC LIMIT 30) sub ORDER BY time ASC"""
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)
    finally:
        con.close();
    df = pd.DataFrame(result)

    data = []
    for i in range(30):
        temp = {
            'time': str(round(float(df.iat[i, 0]), 4)),
            'data_1': str(float(df.iat[i, 1])),
            'data_2': str(float(df.iat[i, 2])),
            'data_3': str(float(df.iat[i, 3])),
            'data_4': str(float(df.iat[i, 4])),
            'data_5': str(float(df.iat[i, 5])),
            'data_6': str(float(df.iat[i, 6])),
            'data_7': str(float(df.iat[i, 7])),
            'data_8': str(float(df.iat[i, 8]))
        }
        data.append(temp);
    print(data)
    return jsonify({'result': data})


######################################## Web Pages to Outside Network ######################################################
@app.route('/index', methods=['POST', 'GET'])
def index():
    print("Successfully entered the route")
    return render_template("index.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    print("Successfully entered the route")
    return render_template("login.html")


@app.route('/commandForm', methods=['POST', 'GET'])
def commandForm():
    print("Successfully entered the route")
    return render_template("commandForm_V1.html")


@app.route('/connectLogin', methods=['POST', 'GET'])
def connectLogin():
    print("Successfully entered the route for PHP")
    return render_template("connect_Login.php")


########################################################## Multiple Clients ##########################################################
##############################################################
#################### Client 0 ################################
##############################################################
#######  Route for the Acknowledgement Received from PI ######
@app.route('/ACK/SendACK', methods=['POST', 'GET'])
def send_ACK():
    result = None
    if request.method == 'POST':
        data = request.get_data()

        print(data)

        data_str = data.decode('UTF-8')
        data_json = eval(data_str)
        Time = data_json["Time"]
        Success = data_json["Success"]
        Value = data_json["Value"]
        Parameter = data_json["Parameter"]
        CMD_Time = data_json["CMD_Time"]
        Sender = data_json["Sender"]
        if Sender == LocalDeviceID:
            sql = "UPDATE CMD" + LocalDeviceID + " SET ACK_Time = %s, ACK_Success = %s, ACK_Parameter = %s, ACK_Value = %s WHERE Time = %s"
        else:
            sql = "UPDATE CMD" + Sender + " SET ACK_Time = %s, ACK_Success = %s, ACK_Parameter = %s, ACK_Value = %s WHERE Time = %s"
        val = (str(Time), str(Success), str(Parameter), str(Value), str(CMD_Time))
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql, val)
        db.commit()
        print("####  success  to  MariaDB  ####")

        res = "Charger 01, Insert ACK successfully"
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


#######  Route for Data Logging from PI ######

@app.route('/PROTOTYPE_V2/Logging', methods=['POST', 'GET'])
def Log_data():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        post_data = eval(data_str)
        print(post_data)

        time = post_data['Time']
        data_1 = post_data['Data']['Data_1']
        data_2 = post_data['Data']['Data_2']
        data_3 = post_data['Data']['Data_3']
        data_4 = post_data['Data']['Data_4']
        data_5 = post_data['Data']['Data_5']
        data_6 = post_data['Data']['Data_6']
        data_7 = post_data['Data']['Data_7']
        data_8 = post_data['Data']['Data_8']
        line1 = str(time) + ', ' + str(data_1) + ', ' + str(data_2) + ', ' + str(data_3) + ', ' + str(
            data_4) + ', ' + str(data_5) + ', ' + str(data_6) + ', ' + str(data_7) + ', ' + str(data_8)
        line = line1 + ', ' + '\n'

        ## Write to MariaDB
        sql = "INSERT INTO `PROTOTYPE_V3` (`time`, `data_1`, `data_2`, `data_3`, `data_4`, `data_5`, `data_6`, `data_7`, `data_8`) VALUES (" + line1 + ")"
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        print("####  Charger 01 success  to  MariaDB  ####")

        res = "Charger 01, Successfully the data to the database"
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


# Get the Command from PHP and forward the Command to the Receiver
@app.route('/CMD/ForwardCMD', methods=['POST', 'GET'])
def Forward_CMD():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        data_str = data_str.replace('Time=', '{"Time": ').replace('&deviceID=', ',"deviceID": "').replace('&Sender=',
                                                                                                          '","Sender": "').replace(
            '&Command=', '","Command": "').replace('&Value=', '","Value": ')
        data_str = data_str + '}'
        data_json = eval(data_str)
        resp_time = data_json["Time"]
        resp_cmd = data_json["Command"]
        resp_value = data_json["Value"]
        resp_sender = data_json["Sender"]
        resp_deviceID = data_json["deviceID"]

        ###Check if the sender is the same to the deviceID
        if resp_sender == resp_deviceID:
            print("Sender = deviceID")
            ## Check if the sender is trusted or not.
            sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (resp_sender)
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            print("Send from trusted peer?: ", result)

            if len(result) < 1:
                res = "The sender is not trusted by " + LocalDeviceID

            else:
                line1 = str(resp_time) + ', ' + str(resp_cmd) + ', ' + str(resp_value)

                sql0 = "SELECT * FROM CMDpicharger01 where Time ='%s'" % (resp_time)
                db0 = pymysql.connect('localhost','pi','1234','longmax')
                cursor0 = db0.cursor()
                cursor0.execute(sql0)
                result0 = cursor0.fetchall()
                print('!!! check if already exists', len(result0))

                if len(result0) < 1:
                    print(len(result))
                    print(result, line1, "insert in to the database")
                    # Write to MariaDB
                    sql1 = "INSERT INTO `CMDpicharger01` (Time, Command, Value) VALUES (%s, %s, %s)"
                    data1 = (str(resp_time), str(resp_cmd), str(resp_value))
                    db1 = pymysql.connect('localhost','pi','1234','longmax')
                    cursor1 = db1.cursor()
                    cursor1.execute(sql1, data1)
                    db1.commit()
                    print("####  Charger 01 successfully insert into  MariaDB  ####")

                print("*****CMD Recived from Web App: Time:", resp_time, "Commmand:", resp_cmd, "Value Entered:",
                      resp_value)
                resp_value = float(resp_value)

                # send the data from spi

                print("------------Start Testing SPI-------------")
                b_list, i = CMDConversion(resp_cmd, resp_value)
                print("------------b_list", b_list)
                global flt
                global bus, device, cnt
                count = 1

                for count in range(3):
                    print("------------Count:", count, "----------------")
                    t1 = time.time()
                    data1 = [t1]
                    b = spi.xfer2(b_list)
                    spi.close()

                    for i in range(8):
                        a1 = b[4 * i:(4 * i + 4)]
                        a = [b[4 * i + 2], b[4 * i + 3], b[4 * i], b[4 * i + 1]]
                        # print(type(a))
                        flt1 = intConversion(a1)
                        line1 += ', ' + str(flt1)
                        data1.append(flt1)
                        i += 1
                    spi.open(bus, device)
                    spi.max_speed_hz = 3900000  # 3.9 MHz
                    spi.mode = 0b00
                    cnt += 1
                    count += 1

                Success = 1
                Value = resp_value
                if i == 4:
                    Parameter = 3
                elif i == 5 or i == 6:
                    Parameter = 4
                elif i == 7:
                    Parameter = 5
                else:
                    Parameter = i

                ack_json = {"Time": t1, "Success": Success, "Value": Value, "Parameter": Parameter,
                            "CMD_Time": resp_time, "Sender": LocalDeviceID}

                sql = "UPDATE CMD" + LocalDeviceID + " SET ACK_Time = %s, ACK_Success = %s, ACK_Parameter = %s, ACK_Value = %s WHERE Time = %s"
                val = (str(t1), str(Success), str(Parameter), str(Value), str(resp_time))
                db = pymysql.connect('localhost','pi','1234','longmax')
                cursor = db.cursor()
                cursor.execute(sql, val)
                db.commit()
                print("####  Charger 01 success  update the  MariaDB  ####", resp_sender, LocalDeviceID)

                res = "Charger 01, Successfully update the ACK to the database"
        else:
            print("Sender != deviceID")
            cmd_json = {"T": int(resp_time), "S": resp_sender, "C": resp_cmd, "V": resp_value}
            # cmd_json = '{"Time": resp_time, "Sender": resp_sender, "Command": resp_cmd, "Value": resp_value}'
            print(cmd_json)
            cipher_text = rsaEncode(resp_deviceID,
                                    str(cmd_json))  ### use the receiver's public key to encrypt the original message
            print("The text encrypted by public key:", cipher_text)

            # decry_value = rsaDecode(resp_deviceID, cipher_text)
            # print(resp_deviceID, decry_value)

            signature = createSignature(resp_sender,
                                        str(cmd_json))  ### use the sender's private key to create signature
            print('The signature created with private key:', signature)

            # is_verify = verifySignature(resp_sender, signature, str(cmd_json))
            # print(is_verify)

            rsa_cmd_json = {"cipherText": str(cipher_text), "signature": str(signature)}
            print("The json message that going to be sent via HTTPS:", rsa_cmd_json)

            flask_url = 'https://' + resp_deviceID + '.www.mplabcharger.org:9061/CMD/ReceiveCMD'
            print(flask_url)
            response = requests.post(flask_url, data=json.dumps(rsa_cmd_json), verify=False)
            # response = requests.post(flask_url, data=rsa_cmd_json, verify=False)
            print('--------Response from the remote charger via Flask: ', response.text)

        res = "Receive the data from PHP"

        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp

    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


# Convert and encode the CMD to the SPI packet that is understandable by TI
@app.route('/CMD/ReceiveCMD', methods=['POST', 'GET'])
def Receive_CMD():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        # data_str=data_str.replace('Time=','{"Time": ').replace('&Sender=',',"Sender": "').replace('&Command=','","Command": "').replace('&Value=','","Value": ')
        # data_str=data_str+'}'
        data_json = eval(data_str)
        print(data_json)
        resp_time = data_json["Time"]
        resp_cmd = data_json["Command"]
        resp_value = data_json["Value"]
        sender = data_json["Sender"]

        # Check if the sender is trusted or not.
        sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (sender)
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        print("Send from trusted peer?: ", result)

        if len(result) < 1:
            res = "The sender is not trusted by " + LocalDeviceID

        else:
            line1 = str(resp_time) + ', ' + str(resp_cmd) + ', ' + str(resp_value)

            sql0 = "SELECT * FROM CMDpicharger01 where Time ='%s'" % (resp_time)
            db0 = pymysql.connect('localhost','pi','1234','longmax')
            cursor0 = db0.cursor()
            cursor0.execute(sql0)
            result0 = cursor0.fetchall()
            print('!!! check if already exists', len(result0))

            if len(result0) < 1:
                print(len(result))
                print(result, line1, "insert in to the database")
                ## Write to MariaDB
                sql1 = "INSERT INTO `CMDpicharger01` (Time, Command, Value) VALUES (%s, %s, %s)"
                data1 = (str(resp_time), str(resp_cmd), str(resp_value))
                # sql1 = "INSERT INTO `CMDpicharger02` (Time, Command, Value) VALUES ("+line1+")"
                db1 = pymysql.connect('localhost','pi','1234','longmax')
                cursor1 = db1.cursor()
                cursor1.execute(sql1, data1)
                db1.commit()
                print("####  successfully insert into  MariaDB  ####")

            print("*****CMD Recived from Web App: Time:", resp_time, "Commmand:", resp_cmd, "Value Entered:",
                  resp_value)
            resp_value = float(resp_value)

            # The CMD sent by the
            print("------------Start Testing SPI-------------")
            b_list, i = CMDConversion(resp_cmd, resp_value)
            print("------------b_list", b_list)
            global flt
            global bus, device, cnt
            count = 1

            for count in range(3):
                print("------------Count:", count, "----------------")
                t1 = time.time()
                data1 = [t1]
                b = spi.xfer2(b_list)
                spi.close()

                for i in range(8):
                    a1 = b[4 * i:(4 * i + 4)]
                    a = [b[4 * i + 2], b[4 * i + 3], b[4 * i], b[4 * i + 1]]
                    # print(type(a))
                    flt1 = intConversion(a1)
                    line1 += ', ' + str(flt1)
                    data1.append(flt1)
                    i += 1
                spi.open(bus, device)
                spi.max_speed_hz = 3900000  # 3.9 MHz
                spi.mode = 0b00
                cnt += 1
                count += 1

            # b_list, i=CMDConversion(resp_cmd, resp_value)
            # t1 = time.time()
            Success = 1
            Value = resp_value
            if i == 4:
                Parameter = 3
            elif i == 5 or i == 6:
                Parameter = 4
            elif i == 7:
                Parameter = 5
            else:
                Parameter = i

            ack_json = {"Time": t1, "Success": Success, "Value": Value, "Parameter": Parameter, "CMD_Time": resp_time,
                        "Sender": LocalDeviceID}
            sql = "UPDATE CMD" + LocalDeviceID + " SET ACK_Time = %s, ACK_Success = %s, ACK_Parameter = %s, ACK_Value = %s WHERE Time = %s"
            val = (str(t1), str(Success), str(Parameter), str(Value), str(resp_time))
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql, val)
            db.commit()
            print("####  success  update the  MariaDB  ####", sender, LocalDeviceID)
            # if sender != LocalDeviceID:
            #     print('--------ack_json sent to the server:', ack_json)
            #     flask_url = 'http://'+sender+'.www.mplabcharger.org:9060/ACK/SendACK'
            #     print(flask_url)
            #     response = requests.post(flask_url, data=json.dumps(ack_json))
            # print('--------Response from Server via Flask: ', response.text)

            res = "Charger 01, Successfully the data to the database"
        res = "Received CMD"
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp

    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


########################Update the User Info for new Registration ######################################
########################################################################################################


@app.route('/UserInfo/SendtoPeer', methods=['POST', 'GET'])
def Send_to_Peer():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_json = eval(data_str)
        LastName = data_json["LastName"]
        FirstName = data_json["FirstName"]
        Username = data_json["Username"]
        Password = data_json["Password"]
        Email = data_json["Email"]
        Role = data_json["Role"]

        print("&&&&&&&&&&&&&&&&&&&&&&&& New Registration:", LastName, FirstName, Username, Password, Email, Role)

        sql1 = "SELECT * FROM UserPWD2 WHERE Username = %s"
        val = (str(Username))
        db1 = pymysql.connect('localhost','pi','1234','longmax')
        cursor1 = db1.cursor()
        length = cursor1.execute(sql1, val)

        if length > 0:
            res = "The username you input is already registered"
        else:
            sql0 = "INSERT INTO UserPWD2 (LastName, FirstName, Username, Password, Email, Role) VALUES (%s, %s, %s, password(%s), %s, %s)"
            val0 = (str(LastName), str(FirstName), str(Username), str(Password), str(Email), str(Role))
            db0 = pymysql.connect('localhost','pi','1234','longmax')
            cursor0 = db0.cursor()
            cursor0.execute(sql0, val0)
            db0.commit()
            # #find out all the peers for this charger:
            peer_DeviceID = []
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute("SELECT ChargerID from PeerInfo4")
            fetch_data = cursor.fetchall()
            print(fetch_data)
            for ChargerID in fetch_data:
                peer_DeviceID.append(ChargerID[0])
            print(peer_DeviceID)
            index = 0
            for index in range(len(peer_DeviceID)):
                if peer_DeviceID[index] != LocalDeviceID:
                    flask_url = 'https://' + peer_DeviceID[
                        index] + '.www.mplabcharger.org:9061/UserInfo/ReceivefromPeer'
                    print(flask_url)
                    response = requests.post(flask_url, data=json.dumps(data_json), verify=False)
                    print('Response from the peer', peer_DeviceID[index], ':', response.text)

            res = "Successfully insert into the database and send to peers"

        # res = "Sent the new user information to all peer chargers"
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/UserInfo/ReceivefromPeer', methods=['POST', 'GET'])
def Receive_from_Peer():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        data_json = eval(data_str)
        Sender = data_json["Sender"]
        ## Check if the sender is trusted or not.
        sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (Sender)
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        print("Send from trusted peer?: ", result)

        if len(result) < 1:
            res = "The sender is not trusted by " + LocalDeviceID

        else:
            FirstName = data_json['FirstName']
            LastName = data_json['LastName']
            Username = data_json['Username']
            Password = data_json['Password']
            Email = data_json['Email']
            Role = data_json['Role']

            line1 = "'" + str(LastName) + "','" + str(FirstName) + "','" + str(Username) + "','" + str(
                Password) + "','" + str(Email) + "','" + str(Role) + "'"

            sql = "INSERT INTO `UserPWD2` (`LastName`, `FirstName`, `Username`, `Password`, `Email`, `Role`) VALUES (" + line1 + ")"
            print(sql)
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            db.commit()
            print("Successfully Insert a New UserInfo: ", line1)

        res = "Successfully Insert a New UserInfo to " + LocalDeviceID
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/UserInfo/CheckAuthority', methods=['Post', 'GET'])
def Check_User_Authority():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('Username=', '{"Username": "').replace('&Device=', '","Device": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["Device"]
        Username = data_json["Username"]

        print(deviceID, Username)
        # deviceID='picharger01'
        # Username='Username1'

        # find out all the peers for this charger:
        sql = "SELECT * FROM DeviceInfo where ChargerID = '%s'" % (deviceID)
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result[0])
        Owner = result[0][1]
        Group = result[0][2]
        OwnerRights = result[0][3]
        GroupRights = result[0][4]
        EveryRights = result[0][5]
        print('Owner:', Owner, 'Group:', Group, "Owner Rights:", OwnerRights, "GroupRights:", GroupRights,
              "EveryRights:", EveryRights)
        print(type(OwnerRights))

        if Username == Owner:
            Rights = OwnerRights
        else:
            sql1 = "SELECT * FROM UserGroup where " + str(Group) + " = '%s'" % (Username)
            db1 = pymysql.connect('localhost','pi','1234','longmax')
            cursor1 = db1.cursor()
            cursor1.execute(sql1)
            result1 = cursor1.fetchall()
            print(result1, len(result1))
            if len(result1) > 0:
                Rights = GroupRights
            else:
                Rights = EveryRights

        print("With the Username", Username, "and the deviceID", deviceID, ", the rights you have is:", Rights)
        temp = int(Rights)
        if temp in [2, 3, 6, 7]:
            res = '111'
        else:
            res = '00000'
        print('Success 1, fail 0:', res)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/UserInfo/LoginCheck', methods=['Post', 'GET'])
def Login_Check():
    if request.method == 'POST':
        # Get the data from the PHP (array)
        data = request.get_data()
        data_str = data.decode('UTF-8')
        # mannually convert the array to json style in string
        # data_str=data_str.replace('Username=','{"Username": "').replace('&Password=','","Password": "').replace('&deviceID=','","deviceID": "')
        # data_str=data_str+'"}'
        # Convert the string to json and get the variables
        # 解密参数
        _cipher_text = unquote(eval(data_str)['encodeString'])
        # 请求头里面的deviceId 和 publicPem
        deviceId_ = request.headers['deviceId']
        public_pem_ = request.headers['public_pem']
        data_str = unquote(decrypt_with_private_key_for_device_id(_cipher_text, deviceId_))
        data_json = eval(data_str)
        username = data_json["Username"]
        password = data_json["Password"]
        deviceID = data_json["deviceID"]

        print("------------ New User Login:", username, password, deviceID)

        # Check if the username and password pair is exists in the database
        # sql = "SELECT * FROM UserPWD2 where Username=%s and Password=password(%s)"
        sql = "SELECT * FROM UserPWD2 where Username=%s and Password=password(%s) "
        val = (str(username), str(password))
        # db= pymysql.connect('localhost','nie','nie','longmax')
        # db = pymysql.connect('localhost','pi','1234','longmax')
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        length = cursor.execute(sql, val)
        result = cursor.fetchall()
        db.close()
        # If the username and password is not matched, respond 0
        # if the username and password is correct in the database and charger is not occupied, respond 1
        # If the username and password is correct in the database and charger is occupied by other users, respond2

        # Php will redirect to different webpage according to the response (2/1/0)
        if length > 0:
            sql0 = "SELECT * FROM DeviceInfo where ChargerID=%s"
            val0 = (str(deviceID))
            # db0= pymysql.connect('localhost','nie','nie','longmax')
            # db0 = pymysql.connect('localhost','pi','1234','longmax')
            db0 = pymysql.connect('localhost','pi','1234','longmax')
            cursor0 = db0.cursor()
            cursor0.execute(sql0, val0)
            result0 = cursor0.fetchall()
            LoginUser = result0[0][9]
            print("Login User:", LoginUser)
            if len(LoginUser) > 0:
                print("One user Logged in")
                if LoginUser == username:
                    print("same user")
                    res = "1"
                else:

                    res = "2"
            else:
                print("Not occupied")
                res = "1"
                sql1 = "UPDATE DeviceInfo SET LoginUser = %s WHERE ChargerID=%s"
                val1 = (str(username), str(deviceID))
                db1 = pymysql.connect('localhost','pi','1234','longmax')
                cursor1 = db1.cursor()
                cursor1.execute(sql1, val1)
                db1.commit()

        else:
            res = "0"
        print(">>>>>>>", res)

        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request for /Status/LoginCheck."
        rsp = Response(json.dumps(result), status=200, content_type="application/json")
        return rsp


@app.route('/mobile/UserInfo/Logout', methods=['Post', 'GET'])
def Logout():
    public_pem_ = request.headers['public_pem']
    if request.method == 'POST':
        # Get the data from the PHP (array)
        data = request.get_data()
        print(data)
        data_str = data.decode('UTF-8')
        md5String = eval(data_str)['sign']
        _cipher_text = unquote(eval(data_str)['encodeString'])
        # 请求头里面的deviceId 和 publicPem
        deviceId_ = request.headers['deviceId']
        data_str = unquote(decrypt_with_private_key_for_device_id(_cipher_text, deviceId_))

        this_md5 = get_md5(data_str)

        if md5String != this_md5:
            result = encry("数据不匹配", public_pem_)
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}

        data_json = eval(data_str)
        Username = data_json['Username']
        deviceID = data_json['deviceID']

        # Clear out the username cached in the database
        sql1 = "UPDATE DeviceInfo SET LoginUser = '' WHERE ChargerID=%s"
        val1 = (str(deviceID))
        # db1= pymysql.connect('localhost','nie','nie','longmax')
        # db1 = pymysql.connect('localhost','pi','1234','longmax')
        db1 = pymysql.connect('localhost','pi','1234','longmax')
        cursor1 = db1.cursor()
        effect_rows = cursor1.execute(sql1, val1)
        db1.commit()
        db1.close()

        if effect_rows > 0:
            res = "Successfully delete from the database"
            res = encry(res, public_pem_)
            rsp = Response(json.dumps(res), status=200, content_type="application/json")
        else:
            res = "Successfully delete from the database"
            res = encry(res, public_pem_)
            rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        res = "Invalid request for /UserInfo/Logout"
        res = encry(res, public_pem_)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp


#######################Network of Trust #################################
#########################################################################
@app.route('/NetworkOfTrust/SenderLocal', methods=['Post', 'GET'])  ## 10 --> 1
def NetworkOfTrust_SenderLocal():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('Username=', '{"Username": "').replace('&Device=', '","Device": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["Device"]  ###Receiver's device ID
        Username = data_json["Username"]
        json_data = {"Sender": "picharger01", "Username": Username, "Method": "DeviceID"}  # **********
        flask_url = 'https://' + deviceID + '.www.mplabcharger.org:9061/NetworkOfTrust/Receiver'
        print(flask_url)
        response = requests.post(flask_url, data=json.dumps(json_data), verify=False)
        # print('Response from the peer:', response.text)
        resp = "Send to target device: " + deviceID
        return response.text
    else:
        resp = "Invalid"
        return resp


@app.route('/NetworkOfTrust/SenderLocalIP', methods=['Post', 'GET'])  ## 10 --> 1
def NetworkOfTrust_SenderLocalIP():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('Username=', '{"Username": "').replace('&DeviceIP=', '","DeviceIP": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        DeviceIP = data_json["DeviceIP"]  ###Receiver's device ID
        Username = data_json["Username"]
        json_data = {"Sender": "picharger01", "Username": Username, "Method": "DeviceIP"}  # **********
        flask_url = 'http://' + DeviceIP + ":8090/NetworkOfTrust/Receiver"
        print(flask_url)
        response = requests.post(flask_url, data=json.dumps(json_data), verify=False)
        # print('Response from the peer:', response.text)
        resp = "Send to target device with the IP address of: " + DeviceIP
        return response.text
    else:
        resp = "Invalid"
        return resp


@app.route('/NetworkOfTrust/SenderLocalRemove', methods=['Post', 'GET'])  ## 10 --> 1
def NetworkOfTrust_SenderLocalRemove():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        if "Remove" in data_str:
            print("Yes")
            peer_DeviceID = []
            peer_key = []
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute("SELECT ChargerID,PublicPEM from PeerInfo4")
            fetch_data = cursor.fetchall()
            print(fetch_data)
            for ChargerID in fetch_data:
                peer_DeviceID.append(ChargerID[0])
                peer_key.append(ChargerID[1])
            print(peer_DeviceID)
            print(peer_key)
            for index in range(len(peer_DeviceID)):
                if peer_DeviceID[index] != LocalDeviceID:
                    remove_json = {"cmd": "Remove", "Sender": LocalDeviceID}
                    flask_url = 'https://' + peer_DeviceID[
                        index] + ".www.mplabcharger.org:9061/NetworkOfTrust/ReceiverRemove"
                    sql1 = "DELETE FROM PeerInfo4 WHERE ChargerID = '%s'" % (peer_DeviceID[index])
                    db1 = pymysql.connect('localhost','pi','1234','longmax')
                    cursor1 = db1.cursor()
                    cursor1.execute(sql1)
                    db1.commit()
                    print(sql1)
                    print(flask_url)
                    response = requests.post(flask_url, data=json.dumps(remove_json), verify=False)
                    print("Response from the other charger in the current P2P network: ", response.text)
        resp = "Remove from Current P2P Network"
        return resp
    else:
        resp = "Invalid"
        return resp


@app.route('/NetworkOfTrust/ReceiverRemove', methods=['Post', 'GET'])  ## 10 --> 1
def NetworkOfTrust_ReceiverRemove():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_json = eval(data_str)
        Sender = data_json["Sender"]
        CMD = data_json["cmd"]
        if CMD == "Remove":
            print(LocalDeviceID + " ready to remove: ", Sender)
            sql1 = "DELETE FROM PeerInfo4 WHERE ChargerID = '%s'" % (Sender)
            db1 = pymysql.connect('localhost','pi','1234','longmax')
            cursor1 = db1.cursor()
            cursor1.execute(sql1)
            db1.commit()
            print(sql1)
        resp = "Remove from the DB "
        return resp
    else:
        resp = "Invalid"
        return resp


result_res = None


@app.route('/NetworkOfTrust/Receiver', methods=['Post', 'GET'])
def NetworkOfTrust_Receiver():
    global result_res
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["Sender"]
        Username = data_json["Username"]
        Method = data_json["Method"]

        Sender = deviceID

        if Method == "DeviceIP":
            ## Check if the sender is already in the Peer Network
            sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (Sender)
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            print("Send from trusted peer?: ", result)

            if len(result) > 0:
                res = "The sender is already in the network of " + LocalDeviceID
                result_res = "Refuse"
                print("Sender already in the current P2P network", result_res)

            else:
                root = tk.Tk()

                canvas1 = tk.Canvas(root, width=500, height=500)
                canvas1.pack()

                def ExitApplication():
                    global result_res
                    MsgBox = tk.messagebox.askquestion('New Connection Request',
                                                       'Do you want to accept the connection from ' + deviceID + ' send by user: ' + Username + '.',
                                                       icon='warning')
                    if MsgBox == 'yes':
                        sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (LocalDeviceID)
                        db1 = pymysql.connect('localhost','pi','1234','longmax')
                        cursor1 = db1.cursor()
                        cursor1.execute(sql)
                        result = cursor1.fetchall()
                        print("*******fetched result from db (in str):*******")
                        print(result[0][2])
                        print(type(result[0][2]))
                        public_db = bytes(result[0][2], encoding="utf-8")
                        print("*******encoded result (in bytes):*******")
                        print(public_db)
                        print(type(public_db))

                        json_data = {"Receiver": LocalDeviceID, "PublicKey": result[0][2]}
                        flask_url = 'https://' + deviceID + '.www.mplabcharger.org:9061/NetworkOfTrust/Sender'
                        print(flask_url)
                        response = requests.post(flask_url, data=json.dumps(json_data), verify=False)
                        print('Response from the peer:', response.text)
                        root.destroy()
                        result_res = "AcceptConnection"

                    else:

                        tk.messagebox.showinfo('Decline', 'refuse the connection')
                        root.destroy()

                        result_res = "Refuse"

                button1 = tk.Button(root, text='New Connection Request', command=ExitApplication, bg='black',
                                    fg='white')
                canvas1.create_window(300, 300, window=button1)

                root.mainloop()

        # MsgBox = messagebox.askquestion ('Exit Application','Are you sure you want to exit the application',icon = 'warning')
        # os.system(' chromium-browser "/var/www/html/login.html" &')
        else:
            root = tk.Tk()

            canvas1 = tk.Canvas(root, width=500, height=500)
            canvas1.pack()

            def ExitApplication():
                global result_res
                MsgBox = tk.messagebox.askquestion('New Connection Request',
                                                   'Do you want to accept the connection from ' + deviceID + ' send by user: ' + Username + '.',
                                                   icon='warning')
                if MsgBox == 'yes':
                    sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (LocalDeviceID)
                    db1 = pymysql.connect('localhost','pi','1234','longmax')
                    cursor1 = db1.cursor()
                    cursor1.execute(sql)
                    result = cursor1.fetchall()
                    print("*******fetched result from db (in str):*******")
                    print(result[0][2])
                    print(type(result[0][2]))
                    public_db = bytes(result[0][2], encoding="utf-8")
                    print("*******encoded result (in bytes):*******")
                    print(public_db)
                    print(type(public_db))

                    json_data = {"Receiver": LocalDeviceID, "PublicKey": result[0][2]}
                    flask_url = 'https://' + deviceID + '.www.mplabcharger.org:9061/NetworkOfTrust/Sender'
                    print(flask_url)
                    response = requests.post(flask_url, data=json.dumps(json_data), verify=False)
                    print('Response from the peer:', response.text)
                    root.destroy()
                    result_res = "AcceptConnection"

                else:

                    tk.messagebox.showinfo('Decline', 'refuse the connection')
                    root.destroy()

                    result_res = "Refuse"

            button1 = tk.Button(root, text='New Connection Request', command=ExitApplication, bg='black', fg='white')
            canvas1.create_window(300, 300, window=button1)

            root.mainloop()

        print(result_res)
        return result_res

    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/NetworkOfTrust/Sender', methods=['Post', 'GET'])  # 10
def NetworkOfTrust_Sender():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_json = json.loads(data_str)
        gateDeviceID = data_json["Receiver"]
        gatePublicKey = data_json["PublicKey"]
        print(gateDeviceID)
        print(gatePublicKey)
        print(type(gatePublicKey))
        gateDeviceURL = 'https://' + gateDeviceID + '.www.mplabcharger.org'
        sql = "INSERT INTO PeerInfo4 (ChargerID, ChargerURL, PublicPEM) VALUES ('%s', '%s', '%s')" % (
            gateDeviceID, gateDeviceURL, gatePublicKey)
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()

        sql1 = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (LocalDeviceID)
        db1 = pymysql.connect('localhost','pi','1234','longmax')
        cursor1 = db1.cursor()
        cursor1.execute(sql1)
        result = cursor1.fetchall()
        newPublicKey = result[0][2]
        print(newPublicKey, type(newPublicKey))
        keyLen = len(newPublicKey)
        print(keyLen)
        encryptedNewPublicKey = ""
        part = 3
        for i in range(part):
            if i != part - 1:
                encryptTemp = newPublicKey[i * int(keyLen / part):(i + 1) * int(keyLen / part)]
            else:
                encryptTemp = newPublicKey[(part - 1) * int(keyLen / part):]
            encryptedNewPublicKeyPart = rsaEncodeDB(gateDeviceID, encryptTemp)
            encryptedNewPublicKey += str(encryptedNewPublicKeyPart)
            encryptedNewPublicKey += 'seperate'

        # encryptedNewPublicKey = rsaEncodeDB(gateDeviceID,newPublicKey)
        print(encryptedNewPublicKey, type(encryptedNewPublicKey))
        json_data = {"NewDeviceID": LocalDeviceID, "PublicKey": encryptedNewPublicKey}
        flask_url = 'https://' + gateDeviceID + '.www.mplabcharger.org:9061/NetworkOfTrust/ReceiveNewPublic'
        print(flask_url)
        response = requests.post(flask_url, data=json.dumps(json_data), verify=False)
        print('Response from the peer:', response.text)
        json_response = json.loads(response.text)
        res_response = json_response['res']
        res_all = res_response.split('outerSeparate')
        for i in range(len(res_all) - 1):
            IDandKey = res_all[i]
            tempIDandKey = IDandKey.split('innerSeparate')
            ID = tempIDandKey[0]
            Key = tempIDandKey[1]
            print(ID, Key)
            URL = 'https://' + ID + '.www.mplabcharger.org'
            sql2 = "INSERT INTO PeerInfo4 (ChargerID, ChargerURL, PublicPEM) VALUES ('%s', '%s', '%s')" % (ID, URL, Key)
            db2 = pymysql.connect('localhost','pi','1234','longmax')
            cursor2 = db2.cursor()
            cursor2.execute(sql2)
            db2.commit()

        res = "picharger 10 Success & Send Encrypted Public Key of the New Device"
        return res

    else:
        result = "You are sending a GET request"
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/NetworkOfTrust/ReceiveNewPublic', methods=['Post', 'GET'])  # 1
def NetworkOfTrust_ReceiveNewPublic():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_json = json.loads(data_str)
        newDeviceID = data_json['NewDeviceID']
        publicKeyEncode = data_json['PublicKey']
        tempPublic = publicKeyEncode.split('seperate')
        publicKeyDecode = ""
        for i in range(len(tempPublic) - 1):
            text = tempPublic[i]
            text = text[2:-1]
            print(text)
            publicKeyDecode += rsaDecode(LocalDeviceID, text)
        print(publicKeyDecode)
        print(len(publicKeyDecode))
        ## Forward the new device information to every device in the Peer
        # find out all the peers for this charger:
        keyLen = len(publicKeyDecode)
        peer_DeviceID = []
        peer_key = []
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute("SELECT ChargerID,PublicPEM from PeerInfo4")
        fetch_data = cursor.fetchall()
        print(fetch_data)
        for ChargerID in fetch_data:
            peer_DeviceID.append(ChargerID[0])
            peer_key.append(ChargerID[1])
        print(peer_DeviceID)
        print(peer_key)

        returnAllOtherPeerInfo4 = ""

        for index in range(len(peer_DeviceID)):
            if peer_DeviceID[index] != LocalDeviceID:
                ######
                encryptedNewPublicKey = ""
                newPublicKey = publicKeyDecode
                part = 3
                for i in range(part):
                    if i != part - 1:
                        encryptTemp = newPublicKey[i * int(keyLen / part):(i + 1) * int(keyLen / part)]
                    else:
                        encryptTemp = newPublicKey[(part - 1) * int(keyLen / part):]
                    encryptedNewPublicKeyPart = rsaEncodeDB(peer_DeviceID[index], encryptTemp)
                    encryptedNewPublicKey += str(encryptedNewPublicKeyPart)
                    encryptedNewPublicKey += 'seperate'
                print(encryptedNewPublicKey)
                forward_data_json = {"Sender": LocalDeviceID, "NewDeviceID": newDeviceID,
                                     "PublicKey": encryptedNewPublicKey}

                returnAllOtherPeerInfo4 += peer_DeviceID[index] + 'innerSeparate' + peer_key[index]
                returnAllOtherPeerInfo4 += 'outerSeparate'

                ####
                flask_url = 'https://' + peer_DeviceID[
                    index] + '.www.mplabcharger.org:9061/NetworkOfTrust/PeerReceiveNewPublic'
                print(flask_url)
                response = requests.post(flask_url, data=json.dumps(forward_data_json), verify=False)
                print('Response from the peer', peer_DeviceID[index], ':', response.text)

        print(
            "------------------- Successfully Send the Information of New Device to Everyone ----------------------- ")

        ## Insert the public key of the new device into the DB of the gateway device
        newDeviceURL = 'https://' + newDeviceID + '.www.mplabcharger.org'
        sql = "INSERT INTO PeerInfo4 (ChargerID, ChargerURL, PublicPEM) VALUES ('%s', '%s', '%s')" % (
            newDeviceID, newDeviceURL, publicKeyDecode)
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        print(
            "------------------- Successfully Store the Information of New Device in the Gateway DB ----------------------- ")

        print(returnAllOtherPeerInfo4)

        return jsonify({'res': returnAllOtherPeerInfo4})
        # return "ReceiveNewPublic Success"
    else:
        result = "You are sending a GET request"
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/NetworkOfTrust/PeerReceiveNewPublic', methods=['POST', 'GET'])
def NetworkOfTrust_PeerReceiveNewPublic():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        data_json = eval(data_str)
        Sender = data_json["Sender"]
        newDeviceID = data_json["NewDeviceID"]

        ## Check if the sender is trusted or not.
        sql = "SELECT * FROM PeerInfo4 where ChargerID = '%s'" % (Sender)
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        print("Send from trusted peer?: ", result)

        if len(result) < 1:
            res = "The sender is not trusted by " + LocalDeviceID

        else:
            publicKeyEncode = data_json['PublicKey']
            tempPublic = publicKeyEncode.split('seperate')
            publicKeyDecode = ""
            for i in range(len(tempPublic) - 1):
                text = tempPublic[i]
                text = text[2:-1]
                print(text)
                publicKeyDecode += rsaDecode(LocalDeviceID, text)
            print(publicKeyDecode)
            print(len(publicKeyDecode))

            ## Insert the public key of the new device into the DB of the gateway device
            newDeviceURL = 'https://' + newDeviceID + '.www.mplabcharger.org'
            sql1 = "INSERT INTO PeerInfo4 (ChargerID, ChargerURL, PublicPEM) VALUES ('%s', '%s', '%s')" % (
                newDeviceID, newDeviceURL, publicKeyDecode)
            db1 = pymysql.connect('localhost','pi','1234','longmax')
            cursor1 = db1.cursor()
            cursor1.execute(sql1)
            db1.commit()
            print(
                "------------------- Successfully Store the Information of New Device in the Peer DB ----------------------- ")

        res = "Successfully Insert the Info of the New Peer to " + LocalDeviceID
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


#################Updating Vehicle Status####################################
############################################################################

@app.route('/Status/ShowVehicleStatus', methods=['Post', 'GET'])
def Show_Vehicle_Status():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('deviceID=', '{"deviceID": "').replace('&Parameter=', '","Parameter": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["deviceID"]
        Parameter = data_json["Parameter"]

        print("*******New Vehicle Status Request:", deviceID, Parameter)
        # deviceID='picharger01'
        # Username='Username1'
        if deviceID == LocalDeviceID:
            # find out all the peers for this charger:
            sql = "SELECT * FROM VehicleStatus ORDER BY time DESC LIMIT 1";
            # sql = "SELECT * FROM DeviceInfo where ChargerID = '%s'" %(deviceID)
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            Voltage = result[0][1]
            Current = result[0][2]
            TimeToFull = result[0][3]
            ChargingDischarging = result[0][4]
            EVStatus = result[0][5]

            if Parameter == "Voltage":
                res = str(Voltage)
            elif Parameter == "Current":
                res = str(Current)
            elif Parameter == "TimeToFull":
                res = str(TimeToFull)
            elif Parameter == "ChargingDischarging":
                if ChargingDischarging == 1:
                    res = "Charging"
                else:
                    res = "Discharging"
            elif Parameter == "EVStatus":
                if EVStatus == 1:
                    res = "Plug Disconnected"
                elif EVStatus == 2:
                    res = "Plug Connected"
                elif EVStatus == 3:
                    res = "Plug Locked"
                elif EVStatus == 4:
                    res = "Initializing Communication"
                elif EVStatus == 5:
                    res = "Exchanging Battery Information"
                elif EVStatus == 6:
                    res = "Ready to Charge"
                elif EVStatus == 7:
                    res = "Vehicle not Compatible"
                elif EVStatus == 8:
                    res = "Charging Started"
                elif EVStatus == 9:
                    res = "Charging Completed"
                elif EVStatus == 10:
                    res = "Charging Terminated"
                elif EVStatus == 11:
                    res = "Error"

        else:
            ##request from remote database:
            print("Need to request from the remote database.")
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/Status/ShowChargerStatus', methods=['Post', 'GET'])
def Show_Charger_Status():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('deviceID=', '{"deviceID": "').replace('&Parameter=', '","Parameter": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["deviceID"]
        Parameter = data_json["Parameter"]

        print("*******New Vehicle Status Request:", deviceID, Parameter)
        # deviceID='picharger01'
        # Username='Username1'
        if deviceID == LocalDeviceID:
            # find out all the peers for this charger:
            if Parameter == "Mode":
                sql = "SELECT * FROM CMD" + deviceID + " WHERE Command = 'M' ORDER BY Time DESC LIMIT 1"
            elif Parameter == "State":
                sql = "SELECT * FROM CMD" + deviceID + " WHERE Command = 'S' ORDER BY Time DESC LIMIT 1"
            elif Parameter == "RealPower":
                sql = "SELECT * FROM CMD" + deviceID + " WHERE (Command = 'PN' or Command = 'PP') ORDER BY Time DESC LIMIT 1"
            elif Parameter == "ReactivePower":
                sql = "SELECT * FROM CMD" + deviceID + " WHERE (Command = 'QN' or Command = 'QP') ORDER BY Time DESC LIMIT 1"
            elif Parameter == "PowerFactor":
                sql = "SELECT * FROM CMD" + deviceID + " WHERE Command = 'PF' ORDER BY Time DESC LIMIT 1"
            elif Parameter == "OnOff":
                sql = "SELECT * FROM CMD" + deviceID + " WHERE Command = 'OnOff' ORDER BY Time DESC LIMIT 1"
            # sql = "SELECT * FROM DeviceInfo where ChargerID = '%s'" %(deviceID)
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            value = result[0][2]

            res = str(value)
            print(value)
            if Parameter == "OnOff":
                if value == 1:
                    res = "On"
                else:
                    res = "Off"
        else:
            ##request from remote database:
            print("Need to request from the remote database.")
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/Status/ShowPeerTable', methods=['Post', 'GET'])
def Show_Peer_Table():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('deviceID=', '{"deviceID": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["deviceID"]

        print("------------################### New Vehicle Status Request:", deviceID)
        # deviceID='picharger01'
        # Username='Username1'
        if deviceID == LocalDeviceID:
            # find out all the peers for this charger:
            sql = "SELECT * FROM PeerInfo4"
            # sql = "SELECT * FROM DeviceInfo where ChargerID = '%s'" %(deviceID)
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            res = ""
            for i in range(0, len(result)):
                res += "<tr><td>" + str(result[i][0]) + "</td><td>" + str(result[i][1]) + "</td><td>" + str(
                    result[i][3]) + "</td><td>" + str(result[i][4]) + "</td></tr>"

            print(res)

        else:
            ##request from remote database:
            print("Need to request from the remote database.")
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request for /Status/ShowPeerTable."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/Status/ForgetPassword', methods=['Post', 'GET'])
def Forget_Password():
    result = None
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('deviceID=', '{"deviceID": "').replace('&Parameter=', '","Parameter": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["deviceID"]

        print("------------################### New Forget Password Request:", deviceID)

        sql1 = "SELECT * FROM DeviceInfo WHERE ChargerID = %s"
        val = (str(deviceID))
        db1 = pymysql.connect('localhost','pi','1234','longmax')
        cursor1 = db1.cursor()
        length = cursor1.execute(sql1, val)
        result = cursor1.fetchall()
        if length > 0:
            OwnerName = result[0][1]
            sql2 = "SELECT * FROM UserPWD2 WHERE Username = %s"
            val2 = (str(OwnerName))
            db2 = pymysql.connect('localhost','pi','1234','longmax')
            cursor2 = db2.cursor()
            length = cursor2.execute(sql2, val2)
            result = cursor2.fetchall()
            Email = result[0][5]
            res = "<tr><th> Owner Name: </th><td>" + str(
                OwnerName) + "</td></tr><tr><th> Email Address: </th><td>" + str(Email) + "</td></tr>"

        else:
            res = "Device not registered."
        print(res)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request for /Status/ShowPeerTable."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/mobile/Service/BuyPower',
           methods=['Post', 'GET'])  # route connected with serviceBuy.html and conncet_buy.php
def Buy_Power():
    global number  # the initialization numbers for the SPI communication (for Voltage and Current now)
    res = "success"
    public_pem_ = request.headers['public_pem']
    if request.method == 'POST':
        # decode the array send from connect_buy.php and jsonfy the array
        data = request.get_data()
        data_str = data.decode('UTF-8')
        md5String = eval(data_str)['sign']
        # rsaCiper = RSACipher()
        _cipher_text = unquote(eval(data_str)['encodeString'])

        # 请求头里面的deviceId 和 publicPem
        deviceId_ = request.headers['deviceId']
        data_str = unquote(decrypt_with_private_key_for_device_id(_cipher_text, deviceId_))

        print(data_str)

        this_md5 = get_md5(data_str)

        if md5String != this_md5:
            result = encry("数据不匹配", public_pem_)
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}

        data_json = eval(data_str)
        method = data_json["method"]
        value = data_json["amount"]
        print(type(method), method, type(value), value)

        # method = "1": Full Tank, "2": kWh, "3": dolloars
        if method == "1":  # if the user choose to charge full tank
            # S[2]: Don’t provide grid service, charge the car
            Mode = "S"
            valueS = 2
            # sendSPI(Mode, valueS)
            # Let TI know the user want to charge full tank (might need to get from BMS SOC?)
            Mode = "kWh"
            value = 65535
            # sendSPI(Mode, value)

            # Get the latest Voltage and Current value from the data

            sql = "SELECT * FROM VehicleStatus ORDER BY time DESC LIMIT 1";

            # db = pymysql.connect('localhost','nie','nie','longmax')
            # db = pymysql.connect('localhost','pi','1234','longmax')
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            Voltage = result[0][1]
            Voltage = int(Voltage)
            Current = result[0][2]
            Current = int(Current)
            # print("PP Voltage:", Voltage)
            if Voltage != number[0]:
                number[0] = Voltage
                if Voltage > 0:
                    Mode = "PP"
                else:
                    Mode = "PN"

                    print(Mode, number[0])
                # send Voltage value to TI
                # sendSPI(Mode, number[0])
            if Current != number[1]:
                number[1] = Current
                Mode = "Current"
                print(Mode, number[1])
                # send current value to TI
                # sendSPI(Mode, number[1])
            res = "1"

        elif method == "2":
            # S[2]: Don’t provide grid service, charge the car
            Mode = "S"
            valueS = 2
            # sendSPI(Mode, valueS)
            # Let TI know the user want to charge a specific amount of energy
            Mode = "kWh"
            value1 = int(value)
            # sendSPI(Mode, value1)

            # Get the latest Voltage and Current value from the data

            sql = "SELECT * FROM VehicleStatus ORDER BY time DESC LIMIT 1";

            # db = pymysql.connect('localhost','nie','nie','longmax')
            # db = pymysql.connect('localhost','pi','1234','longmax')
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            Voltage = result[0][1]
            Voltage = int(Voltage)
            Current = result[0][2]
            Current = int(Current)
            # print("PP Voltage:", Voltage)
            if Voltage != number[0]:
                number[0] = Voltage
                if Voltage > 0:
                    Mode = "PP"
                else:
                    Mode = "PN"

                    print(Mode, number[0])
                # send Voltage value to TI
                # sendSPI(Mode, number[0])
            if Current != number[1]:
                number[1] = Current
                Mode = "Current"
                print(Mode, number[1])
                # send current value to TI
                # sendSPI(Mode, number[1])
            res = "2"
        res = encry(res, public_pem_)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request for /Service/BuyPower."
        result = encry(result, public_pem_)
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/mobile/Service/SellPower',
           methods=['Post', 'GET'])  # route connected with serviceSell.html and conncet_buy.php
def Sell_Power():
    global number  # the initialization numbers for the SPI communication (for Voltage and Current now)
    global ACK_kWh
    global ACK_State
    public_pem_ = request.headers['public_pem']
    if request.method == 'POST':
        # decode the array send from connect_sell.php and jsonfy the array
        data = request.get_data()
        data_str = data.decode('UTF-8')
        md5String = eval(data_str)['sign']
        print(data_str)

        _cipher_text = unquote(eval(data_str)['encodeString'])
        # 请求头里面的deviceId 和 publicPem
        deviceId_ = request.headers['deviceId']
        data_str = unquote(decrypt_with_private_key_for_device_id(_cipher_text, deviceId_))

        this_md5 = get_md5(data_str)

        if md5String != this_md5:
            result = encry("数据不匹配", public_pem_)
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}

        data_json = eval(data_str)
        kWh = data_json["value"]
        hours = data_json["hours"]
        print(type(kWh), kWh, type(hours), hours)

        # S[-2]: Don’t provide grid service, discharge the car
        Mode = "S"
        valueS = -2

        # 先注掉
        # acks = sendSPI(Mode, valueS)

        acks = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        # Let TI know the amount the user want to discharge
        kWh = int(kWh)
        Mode = "kWh"
        value = kWh

        # 先注掉
        # ackkWh = sendSPI(Mode, value)
        ackkWh = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        print("ack for state: ", acks)
        print("ack for kWh ", ackkWh)

        # Get the latest Voltage and Current value from the data

        sql = "SELECT * FROM VehicleStatus ORDER BY time DESC LIMIT 1";

        # db = pymysql.connect('localhost','nie','nie','longmax')
        # db = pymysql.connect('localhost','pi','1234','longmax')
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        Voltage = result[0][1]
        Voltage = int(Voltage)
        Current = result[0][2]
        Current = int(Current)
        print("PP Voltage:", Voltage)
        # if Voltage != number[0]:
        #     number[0] = Voltage
        #     if Voltage > 0:
        #         Mode = "PP"
        #     else:
        #         Mode = "PN"

        #         print(Mode, number[0])
        #     # send Voltage value to TI
        #     sendSPI(Mode, number[0])
        # if Current != number[1]:
        #     number[1] = Current
        #     Mode = "Current"
        #     print(Mode, number[1])
        #     # send current value to TI
        #     sendSPI(Mode, number[1])
        ACK_State = -acks[6]
        ACK_kWh = ackkWh[6]
        print(ACK_kWh, ACK_State)
        res = "[1]state: -" + str(acks[6]) + "[7]kWh: " + str(ackkWh[6])
        print(res)
        res = encry(res, public_pem_)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request for /Service/SellPower."
        result = encry(result, public_pem_)
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/Status/ShowChargerResp', methods=['Post', 'GET'])
def Show_Charger_Resp():
    global ACK_kWh
    global ACK_State
    result = None
    print(ACK_kWh, ACK_State)
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        print(data_str)
        data_str = data_str.replace('deviceID=', '{"deviceID": "').replace('&Parameter=', '","Parameter": "')
        data_str = data_str + '"}'
        print(data_str)
        data_json = eval(data_str)
        deviceID = data_json["deviceID"]
        Parameter = data_json["Parameter"]

        print("*******Charger Acknowledgement:", deviceID, Parameter)
        if ACK_State == -2:
            ACK_State_Str = "Discharging"
        elif ACK_State == 0:
            ACK_State_Str = "Idle"
        else:
            ACK_State_Str = "Charging"
        res = "<tr><th>Charger/Discharge:   </th><td>" + ACK_State_Str + "</td></tr>" + "<tr><th>kWh Charged: </th><td>" + str(
            ACK_kWh) + "</td></tr>"
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


######################### Specific routes for Smartphone App ##########
@app.route('/mobile/showSellEngine', methods=['Post', 'GET'])
def show_Sell_engine():
    sql = "SELECT * FROM VehicleStatus limit 1"
    print(sql)
    # db = pymysql.connect(host='localhost', user='nie', password='nie', db='longmax')
    db = pymysql.connect('localhost','pi','1234','longmax')
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    if result is not None and len(result) > 0:
        res = result
        res = list(res)
        res[0] = list(res[0])
        res[0][0] = str(res[0][0])
        res[0][1] = str(res[0][1])
        res[0][2] = str(res[0][2])
        res[0][3] = str(res[0][3])
        if res[0][4] == 1:
            res[0][4] = "Charging"
        else:
            res[0][4] = "Discharging"

        if res[0][5] == 1:
            res[0][5] = "Plug Disconnected"
        elif res[0][5] == 2:
            res[0][5] = "Plug Connected"
        elif res[0][5] == 3:
            res[0][5] = "Plug Locked"
        elif res[0][5] == 4:
            res[0][5] = "Initializing Communication"
        elif res[0][5] == 5:
            res[0][5] = "Exchanging Battery Information"
        elif res[0][5] == 6:
            res[0][5] = "Ready to Charge"
        elif res[0][5] == 7:
            res[0][5] = "Vehicle not Compatible"
        elif res[0][5] == 8:
            res[0][5] = "Charging Started"
        elif res[0][5] == 9:
            res[0][5] = "Charging Completed"
        elif res[0][5] == 10:
            res[0][5] = "Charging Terminated"
        elif res[0][5] == 11:
            res = "Error"


    else:
        res = []
    print(">>>>>>>", res[0], res[0][1])
    db.close()
    rsp = Response(json.dumps(res), status=200, content_type="application/json")
    return rsp


@app.route('/showTables', methods=['Post', 'GET'])
def showTables():
    """
    histogram
    :return:
    """
    sql = "SELECT * FROM showTables"
    # db = pymysql.connect(host='localhost', user='nie', password='nie', db='longmax')
    db = pymysql.connect('localhost','pi','1234','longmax')
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    if request is None:
        result = []
    else:
        axis_1 = [x[1] for x in result]
        axis_0 = [x[0] for x in result]
        result = [axis_0, axis_1]
    db.close()
    rsp = Response(json.dumps(result), status=200, content_type="application/json")
    return rsp


############################################################################################################
######################################m Mobile #############################################################
@app.route('/mobile/showTables', methods=['Post', 'GET'])
def mobile_showTables():
    """
    histogram
    :return:
    """
    public_pem_ = request.headers['public_pem']
    sql = "SELECT * FROM showTables"
    # db = pymysql.connect(host='localhost', user='nie', password='nie', db='longmax')
    # db = pymysql.connect('localhost','pi','1234','longmax')
    db = pymysql.connect('localhost','pi','1234','longmax')
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    if request is None:
        result = []
    else:
        axis_1 = [x[1] for x in result]
        axis_0 = [x[0] for x in result]
        result = [axis_0, axis_1]
    db.close()
    # result = encry(result)
    result = encry(json.dumps(result), public_pem_)
    rsp = Response(json.dumps(result), status=200, content_type="application/json")
    return rsp


@app.route('/mobile/showEVStatus', methods=['Post', 'GET'])
def mobile_show_Sell_engine():
    sql = "SELECT * FROM VehicleStatus limit 1"
    public_pem_ = request.headers['public_pem']
    print(sql)
    # db = pymysql.connect(host='localhost', user='nie', password='nie', db='longmax')
    # db = pymysql.connect('localhost','pi','1234','longmax')
    db = pymysql.connect('localhost','pi','1234','longmax')
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    if result is not None and len(result) > 0:
        res = result
        res = list(res)
        res[0] = list(res[0])
        res[0][0] = str(res[0][0])
        res[0][1] = str(res[0][1])
        res[0][2] = str(res[0][2])
        res[0][3] = str(res[0][3])

        if res[0][4] == 1:
            res[0][4] = "Charging"
        else:
            res[0][4] = "Discharging"

        if res[0][5] == 1:
            res[0][5] = "Plug Disconnected"
        elif res[0][5] == 2:
            res[0][5] = "Plug Connected"
        elif res[0][5] == 3:
            res[0][5] = "Plug Locked"
        elif res[0][5] == 4:
            res[0][5] = "Initializing Communication"
        elif res[0][5] == 5:
            res[0][5] = "Exchanging Battery Information"
        elif res[0][5] == 6:
            res[0][5] = "Ready to Charge"
        elif res[0][5] == 7:
            res[0][5] = "Vehicle not Compatible"
        elif res[0][5] == 8:
            res[0][5] = "Charging Started"
        elif res[0][5] == 9:
            res[0][5] = "Charging Completed"
        elif res[0][5] == 10:
            res[0][5] = "Charging Terminated"
        elif res[0][5] == 11:
            res = "Error"


    else:
        res = []
    print(">>>>>>>", res[0], res[0][1])
    db.close()
    res = encry(json.dumps(res), public_pem_)
    rsp = Response(json.dumps(res), status=200, content_type="application/json")
    return rsp


@app.route('/mobile/UserInfo/LoginCheck', methods=['Post', 'GET'])
def mobile_Login_Check():
    public_pem_ = request.headers['public_pem']
    if request.method == 'POST':
        # Get the data from the PHP (array)
        data = request.get_data()
        data_str = data.decode('UTF-8')
        md5String = eval(data_str)['sign']
        _cipher_text = unquote(eval(data_str)['encodeString'])
        # Get deviceId and publicPem from request head
        deviceId_ = request.headers['deviceId']
        data_str = unquote(decrypt_with_private_key_for_device_id(_cipher_text, deviceId_))

        this_md5 = get_md5(data_str)

        if md5String != this_md5:
            result = encry("data not match", public_pem_)
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}

        data_json = eval(data_str)
        print(data_str)
        username = data_json["Username"]
        password = data_json["Password"]

        deviceID = data_json["deviceID"]

        print("------------ New User Login:", username, password)

        # Check if the username and password pair is exists in the database
        # sql = "SELECT * FROM UserPWD2 where Username='{0}' and Password='{1}'".format(str(username),str(password))
        sql = "SELECT * FROM UserPWD2 where Username=%s and Password=password(%s)"
        # sql = "SELECT * FROM UserPWD2 where Username=%s and Password=%s"
        val = (str(username), str(password))
        # db= pymysql.connect('localhost','nie','nie','longmax')
        # db = pymysql.connect('localhost','pi','1234','longmax')
        db = pymysql.connect('localhost','pi','1234','longmax')
        cursor = db.cursor()
        length = cursor.execute(sql, val)
        result = cursor.fetchall()
        db.close()
        print(result)

        # If the username and password is not matched, respond 0
        # if the username and password is correct in the database and charger is not occupied, respond 1
        # If the username and password is correct in the database and charger is occupied by other users, respond2

        # Php will redirect to different webpage according to the response (2/1/0)
        if length > 0:
            sql0 = "SELECT LoginUser FROM DeviceInfo where ChargerID=%s"
            val0 = (str(deviceID))
            # db0= pymysql.connect('localhost','nie','nie','longmax')
            # db0 = pymysql.connect('localhost','pi','1234','longmax')
            db0 = pymysql.connect('localhost','pi','1234','longmax')
            cursor0 = db0.cursor()
            cursor0.execute(sql0, val0)
            db0.close()
            result0 = cursor0.fetchall()

            if result0 is not None and len(result0) > 0:
                LoginUser = result0[0][0]
                print("Login User:", LoginUser)
                print("One user Logged in")
                if LoginUser == username:
                    print("same user")
                    res = "1"
                else:
                    
                    sql1 = "UPDATE DeviceInfo SET LoginUser = %s WHERE ChargerID=%s"
                    val1 = (str(username), str(deviceID))
                    # db1 = pymysql.connect('localhost','pi','1234','longmax')
                    db1 = pymysql.connect('localhost','pi','1234','longmax')
                    cursor1 = db1.cursor()
                    cursor1.execute(sql1, val1)
                    db1.commit()
                    db1.close()
                    # 1208 新加 lkl+ end
                    res = "2"
            else:
                print("Not occupied")
                res = "1"
                # sql1 = "UPDATE DeviceInfo SET LoginUser = %s WHERE ChargerID=%s"
                sql1 = "INSERT INTO DeviceInfo (LoginUser, ChargerID)" \
                       " VALUES (%s, %s)"
                val1 = (str(username), str(deviceID))
                # db1 = pymysql.connect('localhost','pi','1234','longmax')
                db1 = pymysql.connect('localhost','pi','1234','longmax')
                cursor1 = db1.cursor()
                cursor1.execute(sql1, val1)
                db1.commit()
                db1.close()

        else:
            res = "0"

        print(">>>>>>>", res)
        res = encry(res, public_pem_)
        print(">>>>>>>", res)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request for /Status/LoginCheck."
        result = encry(result, public_pem_)
        print(">>>>>>>", result)
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


def encry(res, publicPem):
    """
    Encode use public key from iOS, the key is too long so that we need to encode by different groups
    
    :param res:
    :param publicPem:
    :return:
    """
    publicPem = "-----BEGIN PUBLIC KEY-----\n" + publicPem + "\n-----END PUBLIC KEY-----"
    _rsa_key = RSA.importKey(bytes(publicPem, encoding="utf8"))
    print(publicPem)
    # _cipher = Cipher_pkcs1_v1_5.new(_rsa_key)
    # rsa1 = base64.b64encode(_cipher.encrypt(res.encode(encoding="utf-8")))
    rsa1 = rsa_encrypt_bytes(_rsa_key, res.encode())
    print("quote:" + str(rsa1))
    rsa_res = quote(rsa1.decode())
    print("quote rsa:" + rsa_res)
    return quote(rsa1.decode())


def rsa_encrypt_bytes(pub_key, bytes_str):
    """
    Devide and encode
    :param pub_key:
    :param bytes_str:
    :return:
    """
    if not isinstance(bytes_str, bytes):
        return None

    pubkey = rsa.PublicKey(pub_key.n, pub_key.e)
    key_length = rsa.common.byte_size(pub_key.n)
    max_msg_length = key_length - 11
    count = len(bytes_str) // max_msg_length
    if len(bytes_str) % max_msg_length > 0:
        count = count + 1
    cry_bytes = b''

    # rsa encode should be devided by max_msg_length, and each group need to be encoded
    # the length of the data to be encoded is key_length
    # the length of data to be decoded is the sum of different key_length
    for i in range(count):
        start = max_msg_length * i
        size = max_msg_length
        content = bytes_str[start: start + size]
        
        crypto = rsa.encrypt(content, pubkey)
        cry_bytes = cry_bytes + crypto
    return base64.b64encode(cry_bytes)


@app.route('/mobile/UserInfo/SendtoPeer', methods=['POST', 'GET'])  ####User Register
def Mobile_Send_to_Peer():
    public_pem_ = request.headers['public_pem']
    if request.method == 'POST':
        data = request.get_data()
        data_str = data.decode('UTF-8')
        _cipher_text = unquote(eval(data_str)['encodeString'])
        md5String = eval(data_str)['sign']
        # 请求头里面的deviceId 和 publicPem
        deviceId_ = request.headers['deviceId']
        data_str = unquote(decrypt_with_private_key_for_device_id(_cipher_text, deviceId_))
        print(data_str)

        this_md5 = get_md5(data_str)

        if md5String != this_md5:
            result = encry("数据不匹配", public_pem_)
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}

        data_json = eval(data_str)
        LastName = data_json["LastName"]
        FirstName = data_json["FirstName"]
        Username = data_json["Username"]
        Password = data_json["Password"]
        Email = data_json["Email"]
        Role = data_json["Role"]

        print("&&&&&&&&&&&&&&&&&&&&&&&& New Registration:", LastName, FirstName, Username, Password, Email, Role)

        sql1 = "SELECT * FROM UserPWD2 WHERE Username = %s"
        val = (str(Username))
        # db1 = pymysql.connect('localhost','pi','1234','longmax')
        # db1 = pymysql.connect('localhost','pi','1234','longmax')
        db1 = pymysql.connect('localhost','pi','1234','longmax')
        cursor1 = db1.cursor()
        length = cursor1.execute(sql1, val)
        db1.close()
        if length > 0:
            res = "The username you input is already registered"
        else:
            sql0 = "INSERT INTO UserPWD2 (LastName, FirstName, Username, Password, Email, Role) VALUES (%s, %s, %s, password(%s), %s, %s)"
            val0 = (str(LastName), str(FirstName), str(Username), str(Password), str(Email), str(Role))
            # db0 = pymysql.connect('localhost','pi','1234','longmax')
            # db0 = pymysql.connect('localhost','pi','1234','longmax')
            db0 = pymysql.connect('localhost','pi','1234','longmax')
            cursor0 = db0.cursor()
            cursor0.execute(sql0, val0)
            db0.commit()
            db0.close()
            # #find out all the peers for this charger:
            peer_DeviceID = []
            # db = pymysql.connect('localhost','pi','1234','longmax')
            db = pymysql.connect('localhost','pi','1234','longmax')
            cursor = db.cursor()
            cursor.execute("SELECT ChargerID from PeerInfo4")
            fetch_data = cursor.fetchall()
            db.close()
            print(fetch_data)
            for ChargerID in fetch_data:
                peer_DeviceID.append(ChargerID[0])
            print(peer_DeviceID)
            # index=0
            # for index in range(len(peer_DeviceID)):
            #     if peer_DeviceID[index] != LocalDeviceID:
            #         flask_url = 'https://'+peer_DeviceID[index]+'.www.mplabcharger.org:9063/UserInfo/ReceivefromPeer'
            #         print(flask_url)
            #         response = requests.post(flask_url, data=json.dumps(data_json), verify=False)
            #         print('Response from the peer', peer_DeviceID[index], ':', response.text)

            res = "Successfully insert into the database and send to peers"

        # res = "Sent the new user information to all peer chargers"
        res = encry(res, public_pem_)
        rsp = Response(json.dumps(res), status=200, content_type="application/json")
        return rsp
    else:
        result = "Invalid request."
        result = encry(result, public_pem_)
        return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}


class RSACipher(object):
    _private_pem = None
    _public_pem = None

    def __init__(self):
        _random_generator = Random.new().read
        _rsa = RSA.generate(1024, _random_generator)
        """
        self._private_pem = _rsa.exportKey()
        self._public_pem = _rsa.publickey().exportKey()
        self.save_keys()
        """
        self.load_keys()

    def get_public_key(self):
        return self._public_pem

    def get_private_key(self):
        return self._private_pem

    def load_keys(self):
        with open('master-public.pem', "r") as f:
            self._public_pem = f.read()
        with open('master-private.pem', "r") as f:
            self._private_pem = f.read()

    def save_keys(self):
        with open('master-public.pem', 'wb') as f:
            f.write(self._public_pem)
        with open('master-private.pem', 'wb') as f:
            f.write(self._private_pem)

    def encrypt_with_public_key(self, _text):
        _rsa_key = RSA.importKey(self._public_pem)
        _cipher = Cipher_pkcs1_v1_5.new(_rsa_key)
        _cipher_text = base64.b64encode(_cipher.encrypt(_text.encode(encoding="utf-8")))
        return _cipher_text

    def decrypt_with_private_key(self, _cipher_text):
        _rsa_key = RSA.importKey(self._private_pem)
        _cipher = Cipher_pkcs1_v1_5.new(_rsa_key)
        _text = _cipher.decrypt(base64.b64decode(_cipher_text), "ERROR")
        return _text.decode(encoding="utf-8")


@app.route('/mobile/getPemByDeviceId', methods=['POST', 'GET'])
def get_pem_by_device_id():
    """
    Gei key pair according to deviceId
    :param deviceID:
    :return:
    """
    data = request.get_data()
    data_str = data.decode('UTF-8')
    deviceID = eval(data_str)['deviceID']

    public_pem_ = unquote(request.headers['public_pem'])
    print(public_pem_)

    _random_generator = Random.new().read
    _rsa = RSA.generate(1024, _random_generator)

    sql1 = "SELECT ChargerID, PublicPEM, PrivatePEM FROM PeerInfo4 WHERE ChargerID = %s"
    # db1 = pymysql.connect('localhost','pi','1234','longmax')
    # db1 = pymysql.connect('localhost','pi','1234','longmax')
    db1 = pymysql.connect('localhost','pi','1234','longmax')
    cursor1 = db1.cursor()
    cursor1.execute(sql1, (deviceID,))
    res = cursor1.fetchall()
    if len(res) == 0:
        """
        insert pem
        """
        sql_inser = "insert into PeerInfo4 (ChargerID, PublicPEM, PrivatePEM) values (%s, %s, %s)"
        _private_pem_device = _rsa.exportKey()
        _public_pem_device = _rsa.publickey().exportKey()
        _public_pem_device = _public_pem_device.decode().strip().\
            replace("\n", "").replace("\t", "").replace("-----BEGIN PUBLIC KEY-----", "")\
            .replace("-----END PUBLIC KEY-----", "")

        cursor1.execute(sql_inser, (deviceID, _public_pem_device, _private_pem_device))
    else:
        _private_pem_device = res[0][2]
        _public_pem_device = res[0][1]
    db1.commit()
    db1.close()
    rsp = Response(json.dumps(encry(_public_pem_device, public_pem_)), status=200, content_type="application/json")
    return rsp


def decrypt_with_private_key_for_device_id(_cipher_text, deviceId):
    """
    Get private key from databse according to deviceId to decode
    :param _cipher_text:
    :param deviceId:
    :return:
    """
    sql1 = "SELECT ChargerID, PublicPEM, PrivatePEM FROM PeerInfo4 WHERE ChargerID = %s"
    # db1 = pymysql.connect('localhost','pi','1234','longmax')
    # db1 = pymysql.connect('localhost','pi','1234','longmax')
    db1 = pymysql.connect('localhost','pi','1234','longmax')
    cursor1 = db1.cursor()
    cursor1.execute(sql1, (deviceId,))
    res = cursor1.fetchall()
    _rsa_key = RSA.importKey(res[0][2])
    _cipher = Cipher_pkcs1_v1_5.new(_rsa_key)
    _text = _cipher.decrypt(base64.b64decode(_cipher_text), "ERROR")
    return _text.decode(encoding="utf-8")


def get_md5(date):
    obj = hashlib.md5()
    obj.update(date.encode('utf-8'))  # date to be encoded
    result = obj.hexdigest()
    return result


if __name__ == '__main__':
    app.run(debug=True, host=_host, port=_port)
    # print(encry(encry("liaokailei-/\sda")))
