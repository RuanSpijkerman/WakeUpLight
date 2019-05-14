#!/usr/bin/env python3

#server side
import socketserver
import schedule
import time
import datetime
import os
import signal
import pafy
import vlc
import smtplib, ssl #email code from https://realpython.com/python-send-email/ by Joska de Langen
import scrollphathd as sphd
import RPi.GPIO as GPIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Handler_TCPServer(socketserver.BaseRequestHandler):

    #vars
    clientMode = ""
    day = ""
    time = ""
    message = ""
    sound = ""
    email = ""

    tempForkValue = 0

    dayOfWeek = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }


    #turn on wakeuplight job
    def wakeUpAlarm(theThing, msg, alarmLink, receiver_email):
        
        print("waking up for:", os.getpid())
        ##code to start wake up light
        GPIO.setmode(GPIO.BCM) #it is the same as pHAT
        #vars for button length
        deltaTime = 0
        startTime = 0
        endTime = 0
        sleepTime = 0.1
        #pin being used
        buttonPin = 17 #using gpio pin 17 - physically pin 11
        #GPIO code from https://www.youtube.com/watch?v=LEi_dT9KDJI done by BurgZerg Arcade
        GPIO.setup(buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP) #setup pint to check for button push

        #wake up light loop
        #exit this loop once wake up time is finished or when button is pushed
        wakingUp = True
        timeCount = 0
        levelCount = 1
        levelTime = 6 #level time of 6 seconds () makes wake up time 1 minute instead of 30 minutes 
        
        while wakingUp:
            try:
                #increase brightness if the time between levels has passed
                if timeCount >= levelTime:    
                    levelCount += 1
                    timeCount = 0
                    if levelCount == 11:
                        wakingUp = False
                    else:
                        #set all pixels to current brighness
                        for r in range(0,7):
                            for c in range(0,17):
                                sphd.set_pixel(c,r,levelCount*0.1)
                        sphd.show()
                
                #increase time spent for this loop
                timeCount += 0.1

                #button code
                if not GPIO.input(buttonPin): #the circuit closes so button is being pushed
                    if startTime == 0: #The button is not already being pressed
                        startTime = time.time()  
                else:
                    if(not startTime == 0): #Button has been pressed and is now released
                        endTime = time.time()
                        deltaTime = endTime - startTime    #Time passed during button press
                        startTime = 0
                        #check length of button push
                        if deltaTime < .15: #less than 1 second is accidental push
                            #do nothing
                            print("Accidental push")
                        else:
                            raise KeyboardInterrupt
                
                time.sleep(sleepTime)
                #check if the button has been pushed to skip the rest of wakeup
            except KeyboardInterrupt:#if the button has been pressed skip to message
                wakingUp = False

        ##end of wake up light code
        sphd.clear()
        sphd.show()
        #start music and show message
        #music
        url = alarmLink
        video = pafy.new(url)
        best = video.getbest()
        playurl = best.url

        media = vlc.MediaPlayer(playurl)
        media.play()

        sphd.write_string(msg+" ")
        print(msg)
        #continously show message
        sphd.set_brightness(0.2)
        cont = True
        while cont:
            try:
                sphd.show()
                sphd.scroll(1)
                
                #button code
                if not GPIO.input(buttonPin): #the circuit closes so button is being pushed
                    if startTime == 0: #The button is not already being pressed
                        startTime = time.time()
                        
                else:
                    if(not startTime == 0): #Button has been pressed and is now released
                        endTime = time.time()
                        deltaTime = endTime - startTime    #Time passed during button press
                        startTime = 0
                        #check length of button push
                        if deltaTime < .15: #less than 1 second is accidental push
                            #do nothing
                            print("Accidental push")
                        else:
                            raise KeyboardInterrupt
                
                time.sleep(sleepTime)
            except KeyboardInterrupt:
                    cont = False
                    #stop music
                    media.stop()

        #clear led board
        sphd.clear()
        sphd.show()
        GPIO.cleanup()
        #send email to user if one was given
        if receiver_email != 'none':
            smtp_server = "smtp.gmail.com"
            port = 587  # For starttls
            sender_email = "ruan.raspi@gmail.com"
            password = "DataComs@1"

            # Create a secure SSL context
            context = ssl.create_default_context()

            # Try to log in to server and send email
            try:
                server = smtplib.SMTP(smtp_server,port)
                server.ehlo() # Can be omitted
                server.starttls(context=context) # Secure the connection
                server.ehlo() # Can be omitted
                server.login(sender_email, password)
                #message that tells user the person woke up
                message = MIMEMultipart("alternative")
                message["Subject"] = "The Pi woke them up at "+ str(datetime.datetime.now().time())
                message["From"] = sender_email
                message["To"] = receiver_email
                msgText = """\
                They should feel well rested now thanks to the song and time you chose"""
                messageBody = MIMEText(msgText, "plain")
                message.attach(messageBody)
                server.sendmail(sender_email, receiver_email, message.as_string())
            except Exception as e:
                # Print any error messages to stdout
                print(e)
            finally:
                server.quit() 


    def AlarmsOnDay(theThing, chosenDay):
        #read current values
        print(chosenDay)
        scheduleFile = open("schedule.txt")
        alarmList = []
        for line in scheduleFile:
            #parts of alarm 
            parts = line.split("#@!")
            tempDay = parts[0]
            if tempDay == chosenDay:
                tempTime = parts[1]
                alarmList.append(tempTime)
        scheduleFile.close()
        #return the list of alarms on the given day
        print(alarmList)
        return alarmList
                
    def RemoveAlarm(theThing, chosenDay, chosenAlarm):
        #code from houbysoft on stackoverflow https://stackoverflow.com/questions/4710067/using-python-for-deleting-a-specific-line-in-a-file
        with open("schedule.txt","r") as f:
            allAlarms = f.readlines()
        with open("schedule.txt", "w") as f:
            for line in allAlarms:
                #split line into parts
                parts = line.split("#@!")
                tempDay = parts[0]
                tempTime = parts[1]
                #check if line is the alarm to be removed
                if not tempDay == chosenDay or not tempTime == chosenAlarm:
                    f.write(line)
        f.close()

    def handle(self):
        print("Accepted Connection")
        if(int(os.environ["runningChild"]) > 0): #there is another handle running - kill it before handling new request
            print("killing child ", os.environ["runningChild"])
            os.kill(int(os.environ["runningChild"]), signal.SIGKILL)
        
        #check if client is clearing alarm or setting new one
        self.clientMode = self.request.recv(4096).strip().decode()
        self.request.sendall("ACK mode".encode())
        if self.clientMode == "1":#if alarm is being set 
            # self.request - TCP socket connected to the client
            print("Setting new Alarm")
            self.day = self.request.recv(4096).strip().decode()
            self.request.sendall("ACK day".encode())
            self.time = self.request.recv(4096).strip().decode()
            self.request.sendall("ACK time".encode())
            self.message = self.request.recv(4096).strip().decode()
            self.request.sendall("ACK request".encode())
            self.sound = self.request.recv(4096).strip().decode()
            self.request.sendall("ACK sound".encode())
            self.email = self.request.recv(4096).strip().decode()
            self.request.sendall("ACK email".encode())
            print("{} sent:".format(self.client_address[0]))
            print(self.day)
            print(self.time)
            print(self.message)
            print(self.sound)
            print(self.email)
            #all data sent
            clientAck = self.request.recv(4096).strip()
            print(clientAck.decode())
            #write new alarm to file
            scheduleFile = open("schedule.txt", "a+")
            line = self.day+"#@!"+self.time+"#@!"+self.message+"#@!"+self.sound+"#@!"+self.email+"\r\n"
            scheduleFile.write(line)
            scheduleFile.close()
            # just send back ACK for data arrival confirmation
            self.request.sendall("Alarm has been set".encode())
        else:#if alarm is being cleared
            self.day = self.request.recv(4096).strip().decode()
            #reply with number of alarms for that day
            tempAlarmList = self.AlarmsOnDay(self.day)
            self.request.sendall(str(len(tempAlarmList)).encode())
            self.request.recv(4096).strip()
            for alarm in tempAlarmList: #send alarm times for that day
                self.request.sendall(alarm.encode())
                self.request.recv(4096).strip() #receive ack of alarm 
            #if there were alarms on the day, receive the one being removed
            if len(tempAlarmList) > 0:
                print("waiting for client to choose alarm")
                self.request.sendall("All alarms sent".encode())
                selectedAlarm = self.request.recv(4096).strip().decode()
                print(selectedAlarm)
                #remove selected alarm
                self.RemoveAlarm(self.day,selectedAlarm)
    
        #open and close file before scheduling starts; ensuring no exceptions
        #create schedule using file
        schedule.clear()
        #read current values
        scheduleFile = open("schedule.txt")
        for line in scheduleFile:
            #parts of alarm 
            parts = line.split("#@!")
            tempDay = parts[0]
            tempTime = parts[1]
            tempMsg = parts[2]
            tempSound = parts[3]
            tempEmail = parts[4]
            #set schedule job based on line input
            if tempDay == "1":
                schedule.every().monday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
            elif tempDay == "2":
                schedule.every().tuesday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
            elif tempDay == "3":
                schedule.every().wednesday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
            elif tempDay == "4":
                schedule.every().thursday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
            elif tempDay == "5":
                schedule.every().friday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
            elif tempDay == "6":
                schedule.every().saturday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
            elif tempDay == "7":
                schedule.every().sunday.at(tempTime).do(self.wakeUpAlarm,msg = tempMsg, alarmLink = tempSound, receiver_email = tempEmail)
        scheduleFile.close()
        #close file before this point

        #start new process using data
        self.tempForkValue = os.fork()

        if self.tempForkValue == 0:  #run wake up process if child process
            while True:
                schedule.run_pending()
                time.sleep(1)
            #command = "python3 ~/Documents/PythonProjects/testProject/process1.py "+self.day.decode()
            #print(command)
            #os.system(command)
            
        else: #store pid of new child process
            os.environ["runningChild"] = str(self.tempForkValue)
        
        
        

if __name__ == "__main__":
    HOST, PORT = "", 1337
    os.environ["runningChild"] = "-1"
    print("server running")
    # Init the TCP server object, bind it to the localhost on 1337 port
    tcp_server = socketserver.TCPServer((HOST, PORT), Handler_TCPServer)

    # Activate the TCP server.
    # To abort the TCP server, press Ctrl-C.
    tcp_server.serve_forever()
