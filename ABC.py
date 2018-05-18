import tkinter as tk 
from tkinter import ttk
from tkinter import scrolledtext
from threading import Thread
from time import sleep
import cv2
import psutil
import os
import tkinter as tk,threading
import sys
import imageio
from threading import Thread
from tkinter import *
from tkinter import ttk
from tkinter.ttk import Frame
from PIL import Image, ImageTk
import yaml
import time
from  time import sleep
import numpy as np
import paho.mqtt.client as mqtt

class GuiThread(tk.Tk):

    def __init__(self):
        self.root = tk.Tk()
        self.lightBlue2 = "#9DC3E6"
        self.root.configure(bg = self.lightBlue2)
        self.w, self.h  = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.w_frame = (self.w - 5 - 5 - 10)/2
        self.w_frame = int(self.w_frame)
        self.root.title("Gui Thread")
        self.root.geometry("%dx%d+0+0" % (self.w, self.h))
        self.green = 0
        self.red = 0
        self.laplacian_num = 1.5
        self.green = 0
        self.red = 0
        self.flat = False
        self.mainFrame = Frame(self.root)
        self.mainFrame.place(x = 5, y = 15)
        self.lmain = Label(self.mainFrame)
        self.lmain.grid(row = 0, column = 0)
        self.flat = False
        self.fff = PhotoImage(file='blu_cap.PNG')
        self.white = "#FFFFFF"
        self.fn = r"D:\Untitled Project\Untitled Project.mp4"
        fn_yaml = r"D:\detectParking-master\datasets\CUHKSquare.yml"
        self.cap = cv2.VideoCapture(self.fn)
        with open(fn_yaml, 'r') as stream:
            self.parking_data = yaml.load(stream)
        self.parking_contours = []
        self.parking_bounding_rects = []
        self.parking_mask = []
        for park in self.parking_data:
            points = np.array(park['points'])
            rect = cv2.boundingRect(points)
            points_shifted = points.copy()
            points_shifted[:,0] = points[:,0] - rect[0] 
            points_shifted[:,1] = points[:,1] - rect[1]
            self.parking_contours.append(points)
            self.parking_bounding_rects.append(rect)
            mask = cv2.drawContours(np.zeros((rect[3], rect[2]), dtype=np.uint8), [points_shifted], contourIdx=-1,
                  color=255, thickness=-1, lineType=cv2.LINE_8)
            mask = mask==255
            self.parking_mask.append(mask)
        self.parking_status = [False]*len(self.parking_data)
        self.parking_buffer = [None]*len(self.parking_data)
        self.create_thread()
        self.root.mainloop()
    
    def show_frame(self):
        if(self.flat == False):
            self.green = 0
            self.red = 0
            video_cur_pos = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 
            ret, frame = self.cap.read()
            frame_blur = cv2.GaussianBlur(frame, (5,5), 3)
            frame_gray = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2GRAY)
            for ind, park in enumerate(self.parking_data):
                    points = np.array(park['points'])
                    rect = self.parking_bounding_rects[ind]
                    roi_gray = frame_gray[rect[1]:(rect[1]+rect[3]), rect[0]:(rect[0]+rect[2])] # crop roi for faster calcluation   
                    laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F)
                    points[:,0] = points[:,0] - rect[0] # shift contour to roi
                    points[:,1] = points[:,1] - rect[1]
                    delta = np.mean(np.abs(laplacian * self.parking_mask[ind]))
                    status = delta < self.laplacian_num
                    if (status == True): self.green = self.green + 1
                    else: self.red = self.red + 1
                    if status != self.parking_status[ind] and self.parking_buffer[ind]==None:
                        self.parking_buffer[ind] = video_cur_pos
                    elif status != self.parking_status[ind] and self.parking_buffer[ind]!=None:
                        self.parking_status[ind] = status
                        self.parking_buffer[ind] = None
    
                    points = np.array(park['points'])
                    if self.parking_status[ind]:
                        cv2.drawContours(frame, [points], contourIdx=-1,color=(0,255,0), thickness=2, lineType=cv2.LINE_8)  
                    else:
                        cv2.drawContours(frame, [points], contourIdx=-1,color=(0,0,255), thickness=2, lineType=cv2.LINE_8)       
                    moments = cv2.moments(points)        
                    centroid = (int(moments['m10']/moments['m00'])-3, int(moments['m01']/moments['m00'])+3)
                    cv2.putText(frame, str(park['id']), (centroid[0]+1, centroid[1]+1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    cv2.putText(frame, str(park['id']), (centroid[0]-1, centroid[1]-1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    cv2.putText(frame, str(park['id']), (centroid[0]+1, centroid[1]-1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    cv2.putText(frame, str(park['id']), (centroid[0]-1, centroid[1]+1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
                    cv2.putText(frame, str(park['id']), centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2image   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img   = Image.fromarray(cv2image).resize((self.w_frame, 500))
            imgtk = ImageTk.PhotoImage(image = img)
            self.lmain.imgtk = imgtk
            self.lmain.configure(image=imgtk)
            self.lmain.after(1, self.show_frame)

    def MQTT_PROTO(self):
        client = mqtt.Client()
        client.username_pw_set("wwzahnpz", "pl8vWcdzWE8Y")
        a = client.connect("m14.cloudmqtt.com", 19420, 60)
        client.loop_start()
        time.sleep(1)
        while (self.flat == False):
            client.publish("A_BLANK",self.green)
            client.publish("A_TOTAL",self.red)
            time.sleep(2)
        client.loop_stop()
        client.disconnect()

    def create_thread(self):
        print("thread started")
        run1 = threading.Thread(target=self.show_frame)
        run1.setDaemon(True)
        run1.start()
        run2 = threading.Thread(target=self.MQTT_PROTO)
        run2.setDaemon(True)
        run2.start()
        run3 = threading.Thread(target=self.Show_data)
        run3.setDaemon(True)
        run3.start()

    def stopp(self):
        #sys.exit(1)
        #os._exit(1)
        self.flat = True
        self.root.destroy()

    def Show_data(self):
        Lable_control = Label(self.root, image = self.fff, borderwidth = 0) #(mainWindow,padx=788,pady=133)
        Lable_control.configure(highlightthickness = 0)
        Lable_control.place(x=5, y=527)
        Lable_draw = Label(self.root,padx=388,pady=242)
        Lable_draw.place(x = 805, y = 15)
        Label_empty = Label(self.root, text="Empty spaces:", bg = self.lightBlue2, width = 11, height = 1, font= 'Constantia 18 bold')
        Label_empty.place(x=50, y=580)
        Label_total = Label(self.root, text="Total spaces:", bg = self.lightBlue2, width = 10, height = 1, font= 'Constantia 18 bold')
        Label_total.place(x=52, y=655)
        closeButton = Button(self.root, text = "CLOSE", font= 'Courier 20 bold', bg = self.white, width = 10, height= 1)
        closeButton.configure(command= lambda: self.stopp())            
        closeButton.place(x=110,y=750)

        Label_use = Label(self.root, text="Laplacian use:", bg = self.lightBlue2, width = 11, height = 1, font= 'Constantia 18 bold')
        Label_use.place(x=448, y=580)


        Label_lapla = Label(self.root, text="Laplacian set:", bg = self.lightBlue2, width = 10, height = 1, font= 'Constantia 18 bold')
        Label_lapla.place(x=450, y=655)

        textBox = Text(self.root,font= 'Constantia 13 bold', width = 6, height = 1)
        textBox.place(x=620,y=660)

        def getdt():
            try:
                abc = float(textBox.get("1.0","end-1c"))
                textBox.delete('1.0', END)
                self.laplacian_num = abc
            except ValueError:
                print("Error.Try again !")
                textBox.delete('1.0', END)
        #inputValue=textBox.get("1.0","end-1c")
        buttonCommit = Button(self.root, height=1, font= 'Courier 20 bold',width=10, text="SET", command=lambda: getdt())
        buttonCommit.place(x=518,y=750)

        while(self.flat == False):
            Lable_usenum = Label(self.root,text = "",bg = self.lightBlue2, width = 3, height = 1, justify=LEFT,font= 'Courier 25 bold')
            Lable_usenum.config(text=self.laplacian_num)
            Lable_usenum.place(x=630, y=580)
            if (self.green + self.red == 16):
                Lable_green = Label(self.root,text = "",bg = self.lightBlue2, width = 2, height = 1, justify=LEFT,font= 'Courier 50 bold')
                Lable_green.config(text=self.green)
                Lable_green.place(x=230, y=563)

                Lable_red = Label(self.root,text = "",bg = self.lightBlue2, width = 2, height = 1,justify=LEFT,font= 'Courier 50 bold')
                Lable_red.config(text=self.red)
                Lable_red.place(x=230, y=635)
            time.sleep(1)
if __name__ == '__main__':
    GuiThread()