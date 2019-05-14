#!/usr/bin/env python3

import socket
import re
import sys

HOST = '192.168.0.125'  # The server's hostname or IP address
PORT = 1337        # The port used by the server

#check if alarm is being cleared or set
mode = input("Set (1) or clear(2) alarm: ")
valid = re.search("(1|2)", mode)
while not valid:
    mode = input("Invalid Input! Set (1) or clear(2) alarm: : ")
    valid = re.search("(1|2)", mode)

if mode == "1":
    #get wakeup day, time, message, and sound
    #day input
    day = input("Alarm for day (1-7): ")
    #validate day
    valid = re.search("[1-7]", day)
    while not valid:
        day = input("Invalid Input! Alarm for day (1-7): ")
        valid = re.search("[1-7]", day)
    #time Input
    time = input("When should light start(hh:mm): ")
    #validate time
    valid = re.search("^(2[0-3]|1[0-9]|0[0-9]):([0-5][0-9]|60)$", time)
    while not valid:
        time = input("Invalid Input! When should light start(hh:mm): ")
        valid = re.search("^(2[0-3]|1[0-9]|0[0-9]):([0-5][0-9])$", time)
    #message may be empty 
    message = input("Wake-up message (optional): ")
    if message == "":
        message = "Good Morning"
    sound = input("Sound from Youtube (optional): ")
    if sound == "":
        sound = "https://www.youtube.com/watch?v=-FlxM_0S2lA"
    email = input("Your email (optional): ")
    if email == "":
        email = "none"
    
    #check user isn't being hackerman
    if "#@!" in message or "#@!" in sound or "#@!" in email:
        print("#@! doesn't mean anything")
        sys.exit()

else:
    #day input
    day = input("Clear alarm for day (1-7): ")
    #validate day
    valid = re.search("[1-7]", day)
    while not valid:
        day = input("Invalid Input! Clear alarm for day (1-7): ")
        valid = re.search("[1-7]", day)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    BUFF_SIZE = 4096 # 4 KiB
    s.connect((HOST, PORT))
    #send client current mode
    s.sendall(mode.encode())
    print(s.recv(BUFF_SIZE).decode())
    #send alarm data if setting an alarm
    if mode == "1":    
        s.sendall(day.encode())
        print(s.recv(BUFF_SIZE).decode())
        s.sendall(time.encode())
        print(s.recv(BUFF_SIZE).decode())
        s.sendall(message.encode())
        print(s.recv(BUFF_SIZE).decode())
        s.sendall(sound.encode())
        print(s.recv(BUFF_SIZE).decode())
        s.sendall(email.encode())
        print(s.recv(BUFF_SIZE).decode())
        s.sendall("All data sent".encode())
        data = s.recv(BUFF_SIZE)
        print(data.decode())
    else: #removing alarm
        s.sendall(day.encode())
        numAlarms = int(s.recv(BUFF_SIZE).decode())
        s.sendall("ACK num alarms".encode())
        if(numAlarms == 0):
            print("There are no alarms to clear")
        else: 
            print("Select an alarm to clear ( 1 -",str(numAlarms),")")
            #display all alarms for that day
            tempAlarmList = []
            for x in range(numAlarms):
                alarmTime = s.recv(BUFF_SIZE).decode()
                tempAlarmList.append(alarmTime)
                s.sendall(str(x+1).encode())
                print(str(x+1),"- Alarm at", alarmTime)
            
            print(s.recv(BUFF_SIZE).decode()) #confirm all alarms have been sent
            #get chosen alarm and validate input
            isNumber = True
            try:
                chosenAlarm = int(input("Selection: "))
                valid = chosenAlarm < numAlarms +1
            except ValueError:
                isNumber = False
                valid = False
            while not isNumber or not valid:
                try:
                    chosenAlarm = int(input("Invalid input! Selection: "))
                    isNumber = True
                    valid = chosenAlarm < numAlarms +1
                except ValueError:
                    isNumber = False
                    valid = False
            #send the time of the chosen alarm
            print(tempAlarmList[chosenAlarm-1])
            s.sendall(tempAlarmList[chosenAlarm-1].encode())
            print("Alarm has been cleared")

