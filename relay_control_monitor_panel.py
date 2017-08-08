
import serial
import threading
import logging
import time
import calendar
import threading
import ScrolledText as sct
import time
import datetime
import os
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from random import randint
import serial.tools.list_ports
import sys
import glob
import openpyxl
from uuid import getnode as get_mac

mac = get_mac()

xfile = openpyxl.load_workbook('Relay_Switching_log.xlsx')
sheet = xfile.get_sheet_by_name('relaylog')

cfile = openpyxl.load_workbook('Relay_current_log.xlsx')
sheetC = cfile.get_sheet_by_name('relaycurrentlog')

LARGE_FONT= ("Verdana", 12)

fig = Figure(figsize=(5,5), dpi=100)
a = fig.add_subplot(111)

try:
    import tkinter as tk                # python 3
except:
    import Tkinter as tk     # python 2

try:
    from tkinter import font  as tkfont # python 3
except:
    import tkFont as tkfont  # python 2

import ttk

connected = 0
track = 0
recur = 0

relay1 = "OFF"
relay2 = "OFF"
relay3 = "OFF"
relay4 = "OFF"
relay5 = "OFF"
relay6 = "OFF"
relay7 = "OFF"
relay8 = "OFF"

logging.basicConfig(level=logging.DEBUG, filename='logging.log')



class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget"""
    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(1, append)

class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        global f
        global t
        global g

        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.iconbitmap(self, default="iitkgp.ico")
        tk.Tk.wm_title(self, "CONTROL AND MONITOR PANEL")

        f = open("relaystatuslog.txt","a")
        g = open("currentstatus.txt","a")

        index = self.empty_cell_positioner()
        sheet["K"+index]=str(mac)
        xfile.save('Relay_Switching_log.xlsx')

        index = self.empty_cell_positioner_current()
        sheetC["K"+index]=str(mac)
        cfile.save('Relay_current_log.xlsx')

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        for F,geometry in zip((StartPage, PageOne, PageTwo, graphRelay1, graphRelay2, graphRelay3, graphRelay4, graphRelay5, graphRelay6, graphRelay7, graphRelay8), ('600x450', '600x450', '600x450', '800x650', '800x650', '800x650', '800x650', '800x650', '800x650', '800x650', '800x650')):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = (frame, geometry)
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def empty_cell_positioner(self):
        count = 1
        position = "A"+str(count)
        index = str(count)
        data = sheet[position]
        data_fetched = data.internal_value

        while data_fetched != None:
            count=count+1
            position = "A"+str(count)
            index = str(count)
            data = sheet[position]
            data_fetched = data.internal_value
        count = 1
        return index

    def empty_cell_positioner_current(self):
        count = 1
        position = "A"+str(count)
        index = str(count)
        data = sheetC[position]
        data_fetched = data.internal_value

        while data_fetched != None:
            count=count+1
            position = "A"+str(count)
            index = str(count)
            data = sheetC[position]
            data_fetched = data.internal_value
        count = 1
        return index


    def fetch_timestamp(self):
        return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

    def fetch_entry_data(self,entry):
        return entry.get()

    def change_label(self, label, data):
        label.configure(text=data)

    def show_frame(self, page_name):
        frame, geometry = self.frames[page_name]
        self.update_idletasks()
        self.geometry(geometry)
        frame.tkraise()

    def configuration(self,comPort, label):
        global ser
        global connected
        try:
            ser = serial.Serial(comPort, 9600, timeout=0)
            connected = 1
        except serial.serialutil.SerialException:
            connected = 0
            self.change_label(label,"Couldn't connect to device, Retry!!!")
            logging.exception("Oops:")


    def signin(self, page_name, uname, pword, comport, infolabel):
        global connected
        global ser

        state = "False"
        
        if connected == 0:
            self.configuration(self.fetch_entry_data(comport), infolabel)
        elif connected == 1:
            usrname = ""
            passwd = ""

            while usrname =="":
                try:
                    ser.write("unamereq")
                except:
                    logging.exception("Oops:")

                time.sleep(1)
                try:
                    usrname = ser.readline()
                except:
                    logging.exception("Oops:")
            
            while passwd =="":
                try:
                    ser.write("passreq")
                except:
                    logging.exception("Oops:")

                time.sleep(1)
                passwd = ser.readline()

            if usrname== self.fetch_entry_data(uname) and passwd == self.fetch_entry_data(pword):
                state = "True"
            else:
                state="False"
            if state == "True":
                frame, geometry = self.frames[page_name]
                self.update_idletasks()
                self.geometry(geometry)
                frame.tkraise()
            elif state == "False":
                self.change_label(infolabel, "Incorrect Username/Password")

    def control_execution(self, feedback,buttonObj):
        global ser

        try:
            if feedback == "relay1_on":
                ser.write("RL1_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay1_off":
                ser.write("RL1_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:
            if feedback == "relay2_on":
                ser.write("RL2_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay2_off":
                ser.write("RL2_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:
            if feedback == "relay3_on":
                ser.write("RL3_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay3_off":
                ser.write("RL3_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:  
            if feedback == "relay4_on":
                ser.write("RL4_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay4_off":
                ser.write("RL4_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:
            if feedback == "relay5_on":
                ser.write("RL5_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay5_off":
                ser.write("RL5_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:
            if feedback == "relay6_on":
                ser.write("RL6_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay6_off":
                ser.write("RL6_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:
            if feedback == "relay7_on":
                ser.write("RL7_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay7_off":
                ser.write("RL7_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

        try:
            if feedback == "relay8_on":
                ser.write("RL8_OFF")
                buttonObj.configure(background="red")
            elif feedback == "relay8_off":
                ser.write("RL8_ON")
                buttonObj.configure(background="blue")
        except:
                logging.exception("Oops:")

    def request_state_individual(self,command,buttonObj):
        global ser
        global relay1, relay2, relay3, relay4, relay5, relay6, relay7, relay8
        feedback = ""
        try:
            ser.write("Feed"+command)
            time.sleep(0.1)
            feedback = ser.readline()
        except:
                logging.exception("Oops:")

        if feedback == "relay1_off":
            relay1 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay1_on":
            relay1 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay2_off":
            relay2 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay2_on":
            relay2 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay3_off":
            relay3 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay3_on":
            relay3 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay4_off":
            relay4 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay4_on":
            relay4 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay5_off":
            relay5 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay5_on":
            relay5 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay6_off":
            relay6 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay6_on":
            relay6 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay7_off":
            relay7 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay7_on":
            relay7 = "ON"
            buttonObj.configure(background="blue")
        if feedback == "relay8_off":
            relay8 = "OFF"
            buttonObj.configure(background="red")
        elif feedback == "relay8_on":
            relay8 = "ON"
            buttonObj.configure(background="blue")

    def control_button(self, command,buttonObj, logger):
        global ser
        global f
        global sheet
        global relay1, relay2, relay3, relay4, relay5, relay6, relay7, relay8

        try:
            ser.write("Feed"+command)
            time.sleep(0.1)
            feedback = ser.readline()
            self.control_execution(feedback,buttonObj)
            time.sleep(0.1)
            statusW = ser.readline()+"-------------"+self.fetch_timestamp()
            #logger.critical(statusW)
            f.write(statusW+"\n")
            self.request_state_individual(command,buttonObj)
        except:
                logging.exception("Oops:")

        index = self.empty_cell_positioner()
        sheet["A"+index]=self.fetch_timestamp()
        sheet["B"+index]=relay1
        sheet["C"+index]=relay2
        sheet["D"+index]=relay3
        sheet["E"+index]=relay4
        sheet["F"+index]=relay5
        sheet["G"+index]=relay6
        sheet["H"+index]=relay7
        sheet["I"+index]=relay8
        sheet["J"+index]=calendar.timegm(time.gmtime())

        xfile.save('Relay_Switching_log.xlsx')


    def selected_on(self,rl1,rl2,rl3,rl4,rl5,rl6,rl7,rl8,bt1,bt2,bt3,bt4,bt5,bt6,bt7,bt8,logger):
        global ser
        global f
        global sheet
        global relay1, relay2, relay3, relay4, relay5, relay6, relay7, relay8

        try:
            if rl1.get()==1:
                ser.write("RL1_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt1.configure(background="blue")
                self.request_state_individual("RL1",bt1)
            elif rl1.get()==0:
                ser.write("RL1_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt1.configure(background="red")
                self.request_state_individual("RL1",bt1)
        except:
                logging.exception("Oops:")

        try:
            if rl2.get()==1:
                ser.write("RL2_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt2.configure(background="blue")
                self.request_state_individual("RL2",bt2)
            elif rl2.get()==0:
                ser.write("RL2_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt2.configure(background="red")
                self.request_state_individual("RL2",bt2)
        except:
                logging.exception("Oops:")

        try:
            if rl3.get()==1:
                ser.write("RL3_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt3.configure(background="blue")
                self.request_state_individual("RL3",bt3)
            elif rl3.get()==0:
                ser.write("RL3_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt3.configure(background="red")
                self.request_state_individual("RL3",bt3)
        except:
                logging.exception("Oops:")

        try:
            if rl4.get()==1:
                ser.write("RL4_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt4.configure(background="blue")
                self.request_state_individual("RL4",bt4)
            elif rl4.get()==0:
                ser.write("RL4_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt4.configure(background="red")
                self.request_state_individual("RL4",bt4)
        except:
                logging.exception("Oops:")

        try:
            if rl5.get()==1:
                ser.write("RL5_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt5.configure(background="blue")
                self.request_state_individual("RL5",bt5)
            elif rl5.get()==0:
                ser.write("RL5_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt5.configure(background="red")
                self.request_state_individual("RL5",bt5)
        except:
                logging.exception("Oops:")

        try:
            if rl6.get()==1:
                ser.write("RL6_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt6.configure(background="blue")
                self.request_state_individual("RL6",bt6)
            elif rl6.get()==0:
                ser.write("RL6_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt6.configure(background="red")
                self.request_state_individual("RL6",bt6)
        except:
                logging.exception("Oops:")

        try:
            if rl7.get()==1:
                ser.write("RL7_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt7.configure(background="blue")
                self.request_state_individual("RL7",bt7)
            elif rl7.get()==0:
                ser.write("RL7_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt7.configure(background="red")
                self.request_state_individual("RL7",bt7)
        except:
                logging.exception("Oops:")

        try:
            if rl8.get()==1:
                ser.write("RL8_ON")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt8.configure(background="blue")
                self.request_state_individual("RL8",bt8)
            elif rl8.get()==0:
                ser.write("RL8_OFF")
                time.sleep(0.1)
                statusW = ser.readline()+"-------------"+self.fetch_timestamp()
                #logger.critical(statusW)
                f.write(statusW+"\n")
                bt8.configure(background="red")
                self.request_state_individual("RL8",bt8)
        except:
                logging.exception("Oops:")

        index = self.empty_cell_positioner()
        sheet["A"+index]=self.fetch_timestamp()
        sheet["B"+index]=relay1
        sheet["C"+index]=relay2
        sheet["D"+index]=relay3
        sheet["E"+index]=relay4
        sheet["F"+index]=relay5
        sheet["G"+index]=relay6
        sheet["H"+index]=relay7
        sheet["I"+index]=relay8
        sheet["J"+index]=calendar.timegm(time.gmtime())

        xfile.save('Relay_Switching_log.xlsx')

    def selected_off(self,rl1,rl2,rl3,rl4,rl5,rl6,rl7,rl8,bt1,bt2,bt3,bt4,bt5,bt6,bt7,bt8,logger):
        global ser
        global sheet
        global relay1, relay2, relay3, relay4, relay5, relay6, relay7, relay8


        try:
            if rl1.get()==0:
                ser.write("RL1_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt1.configure(background="blue")
                self.request_state_individual("RL1",bt1)
            elif rl1.get()==1:
                ser.write("RL1_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt1.configure(background="red")
                self.request_state_individual("RL1",bt1)
        except:
                logging.exception("Oops:")

        try:
            if rl2.get()==0:
                ser.write("RL2_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt2.configure(background="blue")
                self.request_state_individual("RL2",bt2)
            elif rl2.get()==1:
                ser.write("RL2_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt2.configure(background="red")
                self.request_state_individual("RL2",bt2)
        except:
                logging.exception("Oops:")

        try:
            if rl3.get()==0:
                ser.write("RL3_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt3.configure(background="blue")
                self.request_state_individual("RL3",bt3)
            elif rl3.get()==1:
                ser.write("RL3_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt3.configure(background="red")
                self.request_state_individual("RL3",bt3)
        except:
                logging.exception("Oops:")

        try:
            if rl4.get()==0:
                ser.write("RL4_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt4.configure(background="blue")
                self.request_state_individual("RL4",bt4)
            elif rl4.get()==1:
                ser.write("RL4_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt4.configure(background="red")
                self.request_state_individual("RL4",bt4)
        except:
                logging.exception("Oops:")

        try:
            if rl5.get()==0:
                ser.write("RL5_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt5.configure(background="blue")
                self.request_state_individual("RL5",bt5)
            elif rl5.get()==1:
                ser.write("RL5_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt5.configure(background="red")
                self.request_state_individual("RL5",bt5)
        except:
                logging.exception("Oops:")

        try:
            if rl6.get()==0:
                ser.write("RL6_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt6.configure(background="blue")
                self.request_state_individual("RL6",bt6)
            elif rl6.get()==1:
                ser.write("RL6_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt6.configure(background="red")
                self.request_state_individual("RL6",bt6)
        except:
                logging.exception("Oops:")

        try:
            if rl7.get()==0:
                ser.write("RL7_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt7.configure(background="blue")
                self.request_state_individual("RL7",bt7)
            elif rl7.get()==1:
                ser.write("RL7_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt7.configure(background="red")
                self.request_state_individual("RL7",bt7)
        except:
                logging.exception("Oops:")

        try:
            if rl8.get()==0:
                ser.write("RL8_ON")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt8.configure(background="blue")
                self.request_state_individual("RL8",bt8)
            elif rl8.get()==1:
                ser.write("RL8_OFF")
                time.sleep(0.1)
                #logger.critical(ser.readline()+"-------------"+self.fetch_timestamp())
                bt8.configure(background="red")
                self.request_state_individual("RL8",bt8)
        except:
                logging.exception("Oops:")

        index = self.empty_cell_positioner()
        sheet["A"+index]=self.fetch_timestamp()
        sheet["B"+index]=relay1
        sheet["C"+index]=relay2
        sheet["D"+index]=relay3
        sheet["E"+index]=relay4
        sheet["F"+index]=relay5
        sheet["G"+index]=relay6
        sheet["H"+index]=relay7
        sheet["I"+index]=relay8
        sheet["J"+index]=calendar.timegm(time.gmtime())

        xfile.save('Relay_Switching_log.xlsx')

    def request_state(self,bt1,bt2,bt3,bt4,bt5,bt6,bt7,bt8):
        global sheet
        global relay1, relay2, relay3, relay4, relay5, relay6, relay7, relay8

        self.request_state_individual("RL1",bt1)
        self.request_state_individual("RL2",bt2)
        self.request_state_individual("RL3",bt3)
        self.request_state_individual("RL4",bt4)
        self.request_state_individual("RL5",bt5)
        self.request_state_individual("RL6",bt6)
        self.request_state_individual("RL7",bt7)
        self.request_state_individual("RL8",bt8)

        index = self.empty_cell_positioner()
        sheet["A"+index]=self.fetch_timestamp()
        sheet["B"+index]=relay1
        sheet["C"+index]=relay2
        sheet["D"+index]=relay3
        sheet["E"+index]=relay4
        sheet["F"+index]=relay5
        sheet["G"+index]=relay6
        sheet["H"+index]=relay7
        sheet["I"+index]=relay8
        sheet["J"+index]=calendar.timegm(time.gmtime())

        xfile.save('Relay_Switching_log.xlsx')

    def signout(self,page_name):
        global ser
        global connected
        ser.close()
        connected = 0
        self.show_frame(page_name)

    def openlog(self):
        global f
        f.close()
        os.system("notepad.exe logging.log")
        f = open("relaystatuslog.txt","a")

    def status_log(self):
        os.system('start excel.exe "%s\\Relay_Switching_log.xlsx"' % (sys.path[0], ))

    def openCurrentLog(self):
        global g
        g.close()
        os.system("notepad.exe logging.log")
        g = open("currentstatus.txt","a")

    def openCurrentStatusLog(self):
        track = 0
        os.system('start excel.exe "%s\\Relay_current_log.xlsx"' % (sys.path[0], ))
        track = 1

    def current_process(self,l1,l2,l3,l4,l5,l6,l7,l8):

        global recur
        global track
        global g
        global sheetC
        if track == 1:
            current_flow = float(randint(0,100)/10)
            relay1c = current_flow
            l1.configure(text=str(current_flow)+" A")
            g.write("Relay 1: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay2c = current_flow
            l2.configure(text=str(current_flow)+" A")
            g.write("Relay 2: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay3c = current_flow
            l3.configure(text=str(current_flow)+" A")
            g.write("Relay 3: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay4c = current_flow
            l4.configure(text=str(current_flow)+" A")
            g.write("Relay 4: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay5c = current_flow
            l5.configure(text=str(current_flow)+" A")
            g.write("Relay 5: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay6c = current_flow
            l6.configure(text=str(current_flow)+" A")
            g.write("Relay 6: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay7c = current_flow
            l7.configure(text=str(current_flow)+" A")
            g.write("Relay 7: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")
            current_flow = float(randint(0,100)/10)
            relay8c = current_flow
            l8.configure(text=str(current_flow)+" A")
            g.write("Relay 8: "+str(current_flow)+" A -------------"+self.fetch_timestamp()+"\n")

            try:
                index = self.empty_cell_positioner_current()
                sheetC["A"+index]=self.fetch_timestamp()
                sheetC["B"+index]=relay1c
                sheetC["C"+index]=relay2c
                sheetC["D"+index]=relay3c
                sheetC["E"+index]=relay4c
                sheetC["F"+index]=relay5c
                sheetC["G"+index]=relay6c
                sheetC["H"+index]=relay7c
                sheetC["I"+index]=relay8c
                sheetC["J"+index]=calendar.timegm(time.gmtime())

                cfile.save('Relay_current_log.xlsx')

            except:
                logging.exception("Oops:")
        
        if track == 1:
            try:
                recur = self.after(1000,lambda: self.current_process(l1,l2,l3,l4,l5,l6,l7,l8))
            except:
                logging.exception("Oops:")
        elif track == 0:
            self.after_cancel(recur)

    def current_update(self,l1,l2,l3,l4,l5,l6,l7,l8,b):
        global track
        global g

        if track == 0:
            track = 1
            b.configure(text='''Sense Disable''',fg="white",bg="blue")
            g = open("currentstatus.txt","a")
            self.current_process(l1,l2,l3,l4,l5,l6,l7,l8)

        elif track == 1:
            track = 0
            b.configure(text='''Sense Enable''',fg="white",bg="red")
            g.close()

    
    def plot(self,canvas,page_name):
        if page_name == "graphRelay1":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "B"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "B"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay2":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "C"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "C"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay3":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "D"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "D"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay4":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "E"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "E"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay5":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "F"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "F"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay6":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "G"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "G"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay7":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "H"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "H"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()
        elif page_name == "graphRelay8":
            
            xList = []
            yList = []


            count = 2
            position = "J"+str(count)
            data = sheetC[position]
            x = data.internal_value
            
            while x != None:
                xList.append(int(x))
                count = count+1
                position = "J"+str(count)
                data = sheetC[position]
                x = data.internal_value
            
            count = 2
            position = "I"+str(count)
            data = sheetC[position]
            y = data.internal_value
            
            while y != None:
                yList.append(int(y))
                count = count+1
                position = "I"+str(count)
                data = sheetC[position]
                y = data.internal_value

            a.clear()
            a.plot(xList, yList)
            canvas.show()

    def back_from_plot(self,page_name):
        self.show_frame(page_name)
        a.clear()
    
    


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay Driver Software", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        self.Entry1 = tk.Entry(self)
        self.Entry1.place(relx=0.4, rely=0.36, relheight=0.04, relwidth=0.27)
        self.Entry1.configure(background="white")
        self.Entry1.configure(disabledforeground="#a3a3a3")
        self.Entry1.configure(font="TkFixedFont")
        self.Entry1.configure(foreground="#000000")
        self.Entry1.configure(highlightbackground="#d9d9d9")
        self.Entry1.configure(highlightcolor="black")
        self.Entry1.configure(insertbackground="black")
        self.Entry1.configure(selectbackground="#c4c4c4")
        self.Entry1.configure(selectforeground="black")

        self.Entry2 = tk.Entry(self)
        self.Entry2.place(relx=0.4, rely=0.49, relheight=0.04, relwidth=0.27)
        self.Entry2.configure(background="white")
        self.Entry2.configure(disabledforeground="#a3a3a3")
        self.Entry2.configure(font="TkFixedFont")
        self.Entry2.configure(foreground="#000000")
        self.Entry2.configure(highlightbackground="#d9d9d9")
        self.Entry2.configure(highlightcolor="black")
        self.Entry2.configure(insertbackground="black")
        self.Entry2.configure(selectbackground="#c4c4c4")
        self.Entry2.configure(selectforeground="black")
        self.Entry2.configure(show="*")

        Label1 = tk.Label(self)
        Label1.place(relx=0.15, rely=0.36, height=21, width=59)
        Label1.configure(text='''Username''')

        Label2 = tk.Label(self)
        Label2.place(relx=0.15, rely=0.49, height=21, width=56)
        Label2.configure(text='''Password''')

        Label3 = tk.Label(self)
        Label3.place(relx=0.15, rely=0.62, height=21, width=59)
        Label3.configure(text='''COM Port''')

        Button1 = tk.Button(self, command=lambda: controller.signin("PageOne",self.Entry1,self.Entry2, self.Entry3, Label5))
        #sampleapp = SampleApp()
        #Button1 = tk.Button(self, command=sampleapp.show_frame("PageOne",parent, controller))
        Button1.place(relx=0.32, rely=0.73, height=34, width=277)
        Button1.configure(activebackground="#d9d9d9")
        Button1.configure(activeforeground="#000000")
        Button1.configure(background="blue")
        Button1.configure(disabledforeground="#a3a3a3")
        Button1.configure(foreground="white")
        Button1.configure(highlightbackground="#d9d9d9")
        Button1.configure(highlightcolor="black")
        Button1.configure(pady="0")
        Button1.configure(text='''Signin''')

        Label4 = tk.Label(self,font=controller.title_font)
        Label4.place(relx=0.27, rely=0.13, height=41, width=284)
        Label4.configure(text='''SIGNIN PAGE''')

        
        self.Entry3 = tk.Entry(self)
        self.Entry3.place(relx=0.58, rely=0.62, relheight=0.04, relwidth=0.09)
        self.Entry3.configure(background="white")
        self.Entry3.configure(disabledforeground="#a3a3a3")
        self.Entry3.configure(font="TkFixedFont")
        self.Entry3.configure(foreground="#000000")
        self.Entry3.configure(insertbackground="black")
        self.Entry3.configure(width=54)
        

        Label5 = tk.Label(self)
        Label5.place(relx=0.38, rely=0.89, height=21, width=194)
        Label5.configure(text="")
        Label5.configure(width=194)

    



class PageOne(tk.Frame):

    def __init__(self, parent, controller):

        check1 = tk.IntVar()
        check2 = tk.IntVar()
        check3 = tk.IntVar()
        check4 = tk.IntVar()
        check5 = tk.IntVar()
        check6 = tk.IntVar()
        check7 = tk.IntVar()
        check8 = tk.IntVar()

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Control and Monitor panel", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        
        st = sct.ScrolledText(self, state='disabled')
        st.place(relx=0.03, rely=0.73, relheight=0.2, relwidth=0.94)
        st.configure(font='TkFixedFont')

        # Create textLogger
        text_handler = TextHandler(st)

        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)

        Button1 = tk.Button(self, command=lambda: controller.control_button("RL1",Button1,logger))
        Button1.place(relx=0.05, rely=0.36, height=24, width=48)
        Button1.configure(activebackground="#d9d9d9")
        Button1.configure(activeforeground="#000000")
        Button1.configure(background="#d9d9d9")
        Button1.configure(disabledforeground="#a3a3a3")
        Button1.configure(fg = "white")
        Button1.configure(highlightbackground="#d9d9d9")
        Button1.configure(highlightcolor="black")
        Button1.configure(pady="0")
        Button1.configure(text="")

        Button2 = tk.Button(self, command=lambda: controller.control_button("RL2",Button2,logger))
        Button2.place(relx=0.17, rely=0.36, height=24, width=48)
        Button2.configure(activebackground="#d9d9d9")
        Button2.configure(activeforeground="#000000")
        Button2.configure(background="#d9d9d9")
        Button2.configure(disabledforeground="#a3a3a3")
        Button2.configure(fg = "white")
        Button2.configure(highlightbackground="#d9d9d9")
        Button2.configure(highlightcolor="black")
        Button2.configure(pady="0")
        Button2.configure(text="")

        Button3 = tk.Button(self, command=lambda: controller.control_button("RL3",Button3,logger))
        Button3.place(relx=0.28, rely=0.36, height=24, width=48)
        Button3.configure(activebackground="#d9d9d9")
        Button3.configure(activeforeground="#000000")
        Button3.configure(background="#d9d9d9")
        Button3.configure(disabledforeground="#a3a3a3")
        Button3.configure(fg = "white")
        Button3.configure(highlightbackground="#d9d9d9")
        Button3.configure(highlightcolor="black")
        Button3.configure(pady="0")
        Button3.configure(text="")

        Button4 = tk.Button(self, command=lambda: controller.control_button("RL4",Button4,logger))
        Button4.place(relx=0.4, rely=0.36, height=24, width=48)
        Button4.configure(activebackground="#d9d9d9")
        Button4.configure(activeforeground="#000000")
        Button4.configure(background="#d9d9d9")
        Button4.configure(disabledforeground="#a3a3a3")
        Button4.configure(fg = "white")
        Button4.configure(highlightbackground="#d9d9d9")
        Button4.configure(highlightcolor="black")
        Button4.configure(pady="0")
        Button4.configure(text="")

        Button5 = tk.Button(self, command=lambda: controller.control_button("RL5",Button5,logger))
        Button5.place(relx=0.52, rely=0.36, height=24, width=48)
        Button5.configure(activebackground="#d9d9d9")
        Button5.configure(activeforeground="#000000")
        Button5.configure(background="#d9d9d9")
        Button5.configure(disabledforeground="#a3a3a3")
        Button5.configure(fg = "white")
        Button5.configure(highlightbackground="#d9d9d9")
        Button5.configure(highlightcolor="black")
        Button5.configure(pady="0")
        Button5.configure(text="")

        Button6 = tk.Button(self, command=lambda: controller.control_button("RL6",Button6,logger))
        Button6.place(relx=0.63, rely=0.36, height=24, width=48)
        Button6.configure(activebackground="#d9d9d9")
        Button6.configure(activeforeground="#000000")
        Button6.configure(background="#d9d9d9")
        Button6.configure(disabledforeground="#a3a3a3")
        Button6.configure(fg = "white")
        Button6.configure(highlightbackground="#d9d9d9")
        Button6.configure(highlightcolor="black")
        Button6.configure(pady="0")
        Button6.configure(text="")

        Button7 = tk.Button(self, command=lambda: controller.control_button("RL7",Button7,logger))
        Button7.place(relx=0.75, rely=0.36, height=24, width=48)
        Button7.configure(activebackground="#d9d9d9")
        Button7.configure(activeforeground="#000000")
        Button7.configure(background="#d9d9d9")
        Button7.configure(disabledforeground="#a3a3a3")
        Button7.configure(fg = "white")
        Button7.configure(highlightbackground="#d9d9d9")
        Button7.configure(highlightcolor="black")
        Button7.configure(pady="0")
        Button7.configure(text="")

        Button8 = tk.Button(self, command=lambda: controller.control_button("RL8",Button8,logger))
        Button8.place(relx=0.87, rely=0.36, height=24, width=48)
        Button8.configure(activebackground="#d9d9d9")
        Button8.configure(activeforeground="#000000")
        Button8.configure(background="#d9d9d9")
        Button8.configure(disabledforeground="#a3a3a3")
        Button8.configure(fg = "white")
        Button8.configure(highlightbackground="#d9d9d9")
        Button8.configure(highlightcolor="black")
        Button8.configure(pady="0")
        Button8.configure(text="")

        Checkbutton1 = tk.Checkbutton(self)
        Checkbutton1.place(relx=0.05, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton1.configure(justify="left")
        Checkbutton1.configure(text="")
        Checkbutton1.configure(variable=check1)

        Checkbutton2 = tk.Checkbutton(self)
        Checkbutton2.place(relx=0.17, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton2.configure(justify="left")
        Checkbutton2.configure(text="")
        Checkbutton2.configure(variable=check2)

        Checkbutton3 = tk.Checkbutton(self)
        Checkbutton3.place(relx=0.28, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton3.configure(justify="left")
        Checkbutton3.configure(text="")
        Checkbutton3.configure(variable=check3)

        Checkbutton4 = tk.Checkbutton(self)
        Checkbutton4.place(relx=0.4, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton4.configure(justify="left")
        Checkbutton4.configure(text="")
        Checkbutton4.configure(variable=check4)

        Checkbutton5 = tk.Checkbutton(self)
        Checkbutton5.place(relx=0.52, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton5.configure(justify="left")
        Checkbutton5.configure(text="")
        Checkbutton5.configure(variable=check5)

        Checkbutton6 = tk.Checkbutton(self)
        Checkbutton6.place(relx=0.63, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton6.configure(justify="left")
        Checkbutton6.configure(text="")
        Checkbutton6.configure(variable=check6)

        Checkbutton7 = tk.Checkbutton(self)
        Checkbutton7.place(relx=0.75, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton7.configure(justify="left")
        Checkbutton7.configure(text="")
        Checkbutton7.configure(variable=check7)

        Checkbutton8 = tk.Checkbutton(self)
        Checkbutton8.place(relx=0.87, rely=0.24, relheight=0.06, relwidth=0.1)
        Checkbutton8.configure(justify="left")
        Checkbutton8.configure(text="")
        Checkbutton8.configure(variable=check8)

        Button9 = tk.Button(self, command=lambda: controller.show_frame("PageTwo",))
        Button9.place(relx=0.03, rely=0.64, height=24, width=97)
        Button9.configure(activebackground="#d9d9d9")
        Button9.configure(activeforeground="#000000")
        Button9.configure(background="green")
        Button9.configure(disabledforeground="#a3a3a3")
        Button9.configure(foreground="black")
        Button9.configure(highlightbackground="#d9d9d9")
        Button9.configure(highlightcolor="black")
        Button9.configure(pady="0")
        Button9.configure(text='''Current Monitor''')

        Button10 = tk.Button(self, command=lambda: controller.selected_on(check1,check2,check3,check4,check5,check6,check7,check8,Button1,Button2,Button3,Button4,Button5,Button6,Button7,Button8,logger))
        Button10.place(relx=0.35, rely=0.64, height=24, width=72)
        Button10.configure(activebackground="#d9d9d9")
        Button10.configure(activeforeground="#000000")
        Button10.configure(background="green")
        Button10.configure(disabledforeground="#a3a3a3")
        Button10.configure(foreground="black")
        Button10.configure(highlightbackground="#d9d9d9")
        Button10.configure(highlightcolor="black")
        Button10.configure(pady="0")
        Button10.configure(text='''Selected on''')

        Button11 = tk.Button(self, command=lambda: controller.selected_off(check1,check2,check3,check4,check5,check6,check7,check8,Button1,Button2,Button3,Button4,Button5,Button6,Button7,Button8,logger))
        Button11.place(relx=0.5, rely=0.64, height=24, width=73)
        Button11.configure(activebackground="#d9d9d9")
        Button11.configure(activeforeground="#000000")
        Button11.configure(background="green")
        Button11.configure(disabledforeground="#a3a3a3")
        Button11.configure(foreground="black")
        Button11.configure(highlightbackground="#d9d9d9")
        Button11.configure(highlightcolor="black")
        Button11.configure(pady="0")
        Button11.configure(text='''Selected off''')

        Button15 = tk.Button(self, command=lambda: controller.status_log())
        Button15.place(relx=0.66, rely=0.64, height=24, width=82)
        Button15.configure(activebackground="#d9d9d9")
        Button15.configure(activeforeground="#000000")
        Button15.configure(background="green")
        Button15.configure(disabledforeground="#a3a3a3")
        Button15.configure(foreground="black")
        Button15.configure(highlightbackground="#d9d9d9")
        Button15.configure(highlightcolor="black")
        Button15.configure(pady="0")
        Button15.configure(text="Status Log")

        Button12 = tk.Button(self, command=lambda: controller.request_state(Button1,Button2,Button3,Button4,Button5,Button6,Button7,Button8))
        Button12.place(relx=0.82, rely=0.64, height=24, width=82)
        Button12.configure(activebackground="#d9d9d9")
        Button12.configure(activeforeground="#000000")
        Button12.configure(background="green")
        Button12.configure(disabledforeground="#a3a3a3")
        Button12.configure(foreground="black")
        Button12.configure(highlightbackground="#d9d9d9")
        Button12.configure(highlightcolor="black")
        Button12.configure(pady="0")
        Button12.configure(text='''Request State''')

        Label1 = tk.Label(self)
        Label1.place(relx=0.05, rely=0.44, height=21, width=44)
        Label1.configure(text='''Relay 1''')
        Label1.configure(width=44)

        Label2 = tk.Label(self)
        Label2.place(relx=0.17, rely=0.44, height=21, width=44)
        Label2.configure(text='''Relay 2''')
        Label2.configure(width=44)

        Label3 = tk.Label(self)
        Label3.place(relx=0.28, rely=0.44, height=21, width=44)
        Label3.configure(text='''Relay 3''')
        Label3.configure(width=44)

        Label4 = tk.Label(self)
        Label4.place(relx=0.4, rely=0.44, height=21, width=44)
        Label4.configure(text='''Relay 4''')
        Label4.configure(width=44)

        Label5 = tk.Label(self)
        Label5.place(relx=0.52, rely=0.44, height=21, width=44)
        Label5.configure(text='''Relay 5''')
        Label5.configure(width=44)

        Label6 = tk.Label(self)
        Label6.place(relx=0.63, rely=0.44, height=21, width=44)
        Label6.configure(text='''Relay 6''')
        Label6.configure(width=44)

        Label7 = tk.Label(self)
        Label7.place(relx=0.75, rely=0.44, height=21, width=44)
        Label7.configure(text='''Relay 7''')
        Label7.configure(width=44)

        Label8 = tk.Label(self)
        Label8.place(relx=0.87, rely=0.44, height=21, width=44)
        Label8.configure(text='''Relay 8''')
        Label8.configure(width=44)  

        Button13 = tk.Button(self,command=lambda: controller.signout("StartPage"))
        Button13.place(relx=0.87, rely=0.02, height=24, width=52)
        Button13.configure(activebackground="#d9d9d9")
        Button13.configure(activeforeground="#000000")
        Button13.configure(background="red")
        Button13.configure(disabledforeground="#a3a3a3")
        Button13.configure(foreground="white")
        Button13.configure(highlightbackground="#d9d9d9")
        Button13.configure(highlightcolor="black")
        Button13.configure(pady="0")
        Button13.configure(text='''Signout''')

        Button14 = tk.Button(self,command=lambda: controller.openlog())
        Button14.place(relx=0.82, rely=0.58, height=24, width=83)
        Button14.configure(activebackground="#d9d9d9")
        Button14.configure(activeforeground="#000000")
        Button14.configure(background="green")
        Button14.configure(disabledforeground="#a3a3a3")
        Button14.configure(foreground="black")
        Button14.configure(highlightbackground="#d9d9d9")
        Button14.configure(highlightcolor="black")
        Button14.configure(pady="0")
        Button14.configure(text='''Error Log''')


          


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Current Monitoring panel", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        
        Button5 = tk.Button(self,command=lambda: controller.show_frame("graphRelay1"))
        Button5.place(relx=0.1, rely=0.45, height=24, width=67)
        Button5.configure(font="font10")
        Button5.configure(foreground="#000000")
        Button5.configure(text='''RELAY 1''')

        Button6 = tk.Button(self,command=lambda: controller.show_frame("graphRelay2"))
        Button6.place(relx=0.37, rely=0.45, height=24, width=67)
        Button6.configure(font="font10")
        Button6.configure(foreground="#000000")
        Button6.configure(text='''RELAY2''')

        Button7 = tk.Button(self,command=lambda: controller.show_frame("graphRelay3"))
        Button7.place(relx=0.6, rely=0.45, height=24, width=67)
        Button7.configure(font="font10")
        Button7.configure(foreground="#000000")
        Button7.configure(text='''RELAY 3''')

        Button8 = tk.Button(self,command=lambda: controller.show_frame("graphRelay4"))
        Button8.place(relx=0.85, rely=0.45, height=24, width=67)
        Button8.configure(font="font10")
        Button8.configure(foreground="#000000")
        Button8.configure(text='''RELAY 4''')

        Button9 = tk.Button(self,command=lambda: controller.show_frame("graphRelay5"))
        Button9.place(relx=0.1, rely=0.67, height=24, width=67)
        Button9.configure(font="font10")
        Button9.configure(foreground="#000000")
        Button9.configure(text='''RELAY 5''')

        Button10 = tk.Button(self,command=lambda: controller.show_frame("graphRelay6"))
        Button10.place(relx=0.37, rely=0.67, height=24, width=67)
        Button10.configure(font="font10")
        Button10.configure(foreground="#000000")
        Button10.configure(text='''RELAY 6''')

        Button11 = tk.Button(self,command=lambda: controller.show_frame("graphRelay7"))
        Button11.place(relx=0.6, rely=0.67, height=24, width=67)
        Button11.configure(font="font10")
        Button11.configure(foreground="#000000")
        Button11.configure(text='''RELAY 7''')

        Button12 = tk.Button(self,command=lambda: controller.show_frame("graphRelay8"))
        Button12.place(relx=0.85, rely=0.67, height=24, width=67)
        Button12.configure(font="font10")
        Button12.configure(foreground="#000000")
        Button12.configure(text='''RELAY 8''')


        Label9 = tk.Label(self)
        Label9.place(relx=0.1, rely=0.54, height=21, width=64)
        Label9.configure(background="#c0c0c0")
        Label9.configure(disabledforeground="#a3a3a3")
        Label9.configure(foreground="#400040")
        Label9.configure(text="0.0 A")

        Label10 = tk.Label(self)
        Label10.place(relx=0.37, rely=0.54, height=21, width=64)
        Label10.configure(background="#c0c0c0")
        Label10.configure(disabledforeground="#a3a3a3")
        Label10.configure(foreground="#000000")
        Label10.configure(text="0.0 A")

        Label11 = tk.Label(self)
        Label11.place(relx=0.6, rely=0.54, height=24, width=64)
        Label11.configure(background="#c0c0c0")
        Label11.configure(disabledforeground="#a3a3a3")
        Label11.configure(foreground="#000000")
        Label11.configure(text="0.0 A")

        Label12 = tk.Label(self)
        Label12.place(relx=0.85, rely=0.54, height=24, width=64)
        Label12.configure(background="#c0c0c0")
        Label12.configure(disabledforeground="#a3a3a3")
        Label12.configure(foreground="#000000")
        Label12.configure(text="0.0 A")

        Label13 = tk.Label(self)
        Label13.place(relx=0.1, rely=0.78, height=24, width=64)
        Label13.configure(background="#c0c0c0")
        Label13.configure(disabledforeground="#a3a3a3")
        Label13.configure(foreground="#000000")
        Label13.configure(text="0.0 A")

        Label14 = tk.Label(self)
        Label14.place(relx=0.37, rely=0.78, height=24, width=64)
        Label14.configure(background="#c0c0c0")
        Label14.configure(disabledforeground="#a3a3a3")
        Label14.configure(foreground="#000000")
        Label14.configure(text="0.0 A")

        Label15 = tk.Label(self)
        Label15.place(relx=0.6, rely=0.78, height=24, width=64)
        Label15.configure(background="#c0c0c0")
        Label15.configure(disabledforeground="#a3a3a3")
        Label15.configure(foreground="#000000")
        Label15.configure(text="0.0 A")

        Label16 = tk.Label(self)
        Label16.place(relx=0.85, rely=0.78, height=24, width=64)
        Label16.configure(background="#c0c0c0")
        Label16.configure(disabledforeground="#a3a3a3")
        Label16.configure(foreground="#000000")
        Label16.configure(text="0.0 A")

        Button1 = tk.Button(self, text="Back",command=lambda: controller.show_frame("PageOne"))
        Button1.place(relx=0.92, rely=0.02, height=24, width=36)
        Button1.configure(activebackground="#d9d9d9")
        Button1.configure(activeforeground="#000000")
        Button1.configure(background="red")
        Button1.configure(disabledforeground="#a3a3a3")
        Button1.configure(foreground="white")
        Button1.configure(highlightbackground="#d9d9d9")
        Button1.configure(highlightcolor="black")
        Button1.configure(pady="0")

        Button2 = tk.Button(self, text="Error Log",command=lambda: controller.openCurrentLog())
        Button2.place(relx=0.78, rely=0.29, height=34, width=107)
        Button2.configure(activebackground="#d9d9d9")
        Button2.configure(activeforeground="#000000")
        Button2.configure(background="green")
        Button2.configure(disabledforeground="#a3a3a3")
        Button2.configure(foreground="black")
        Button2.configure(highlightbackground="#d9d9d9")
        Button2.configure(highlightcolor="black")
        Button2.configure(pady="0")
        Button2.configure(width=107)

        Button3 = tk.Button(self, command=lambda: controller.current_update(Label9,Label10,Label11,Label12,Label13,Label14,Label15,Label16,Button3))
        Button3.place(relx=0.10, rely=0.29, height=34, width=77)
        Button3.configure(activebackground="#d9d9d9")
        Button3.configure(activeforeground="#000000")
        Button3.configure(background="red")
        Button3.configure(disabledforeground="#a3a3a3")
        Button3.configure(foreground="white")
        Button3.configure(highlightbackground="#d9d9d9")
        Button3.configure(highlightcolor="black")
        Button3.configure(pady="0")
        Button3.configure(text='''Sense Enable''')
        Button3.configure(width=77)

        Button4 = tk.Button(self, text="Current log",command=lambda: controller.openCurrentStatusLog())
        Button4.place(relx=0.59, rely=0.29, height=34, width=107)
        Button4.configure(activebackground="#d9d9d9")
        Button4.configure(activeforeground="#000000")
        Button4.configure(background="green")
        Button4.configure(disabledforeground="#a3a3a3")
        Button4.configure(foreground="black")
        Button4.configure(highlightbackground="#d9d9d9")
        Button4.configure(highlightcolor="black")
        Button4.configure(pady="0")
        Button4.configure(width=107)

class graphRelay1(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 1 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay1"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


class graphRelay2(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 2 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay2"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        


class graphRelay3(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 3 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay3"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        


class graphRelay4(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 4 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay4"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        


class graphRelay5(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 5 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay5"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        


class graphRelay6(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 6 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay6"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        

class graphRelay7(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 7 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay7"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        


class graphRelay8(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Relay 8 Current(A) vs Time(s)", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = tk.Button(self, text="Plot",command=lambda: controller.plot(canvas,"graphRelay8"))
        button1.pack()

        button2 = tk.Button(self, text="Back",command=lambda: controller.back_from_plot("PageTwo"))
        button2.pack()
        
        
        canvas = FigureCanvasTkAgg(fig, self)
        #canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


try:
    if __name__ == "__main__":
        global f

        app = SampleApp()
        app.mainloop()
        f.close()
except:
    logging.exception("Oops:")