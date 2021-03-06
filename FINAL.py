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
import numpy as np
import paho.mqtt.client as mqtt

green = 0
red = 0
laplacian_num = 1.5
white 		= "#ffffff"
lightBlue2 	= "#9DC3E6"
font 		= "Constantia"
fontButtons = (font, 12)

#Graphics window
mainWindow = tk.Tk()
mainWindow.configure(bg=lightBlue2)
w, h = mainWindow.winfo_screenwidth(), mainWindow.winfo_screenheight()
w_frame = (w - 5 - 5 - 10)/2
w_frame = int(w_frame)
mainWindow.geometry("%dx%d+0+0" % (w, h))
#mainWindow.resizable(0,0)
mainFrame = Frame(mainWindow)
mainFrame.place(x=5, y=15)   

    #Capture video frames
lmain = tk.Label(mainFrame)
lmain.grid(row=0, column=0)
fn = r"D:\Untitled Project\Untitled Project.mp4"
fn_yaml = r"D:\detectParking-master\datasets\CUHKSquare.yml"
cap = cv2.VideoCapture(fn)
with open(fn_yaml, 'r') as stream:
        parking_data = yaml.load(stream)
parking_contours = []
parking_bounding_rects = []
parking_mask = []
for park in parking_data:
            points = np.array(park['points'])
            rect = cv2.boundingRect(points)
            points_shifted = points.copy()
            points_shifted[:,0] = points[:,0] - rect[0] 
            points_shifted[:,1] = points[:,1] - rect[1]
            parking_contours.append(points)
            parking_bounding_rects.append(rect)
            mask = cv2.drawContours(np.zeros((rect[3], rect[2]), dtype=np.uint8), [points_shifted], contourIdx=-1,
                  color=255, thickness=-1, lineType=cv2.LINE_8)
            mask = mask==255
            parking_mask.append(mask)
parking_status = [False]*len(parking_data)
parking_buffer = [None]*len(parking_data)


def show_frame():
        global green
        global red
        global laplacian_num
        global w_frame
        green = 0
        red = 0
        video_cur_pos = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 
        ret, frame = cap.read()
        frame_blur = cv2.GaussianBlur(frame, (5,5), 3)
        frame_gray = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2GRAY)
        for ind, park in enumerate(parking_data):
                points = np.array(park['points'])
                rect = parking_bounding_rects[ind]
                roi_gray = frame_gray[rect[1]:(rect[1]+rect[3]), rect[0]:(rect[0]+rect[2])] # crop roi for faster calcluation   
                laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F)
                points[:,0] = points[:,0] - rect[0] # shift contour to roi
                points[:,1] = points[:,1] - rect[1]
                delta = np.mean(np.abs(laplacian * parking_mask[ind]))
                status = delta < laplacian_num
                if (status == True): green = green + 1
                else: red = red + 1
                if status != parking_status[ind] and parking_buffer[ind]==None:
                    parking_buffer[ind] = video_cur_pos
                elif status != parking_status[ind] and parking_buffer[ind]!=None:
                    parking_status[ind] = status
                    parking_buffer[ind] = None
    
                points = np.array(park['points'])
                if parking_status[ind]:
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
        img   = Image.fromarray(cv2image).resize((w_frame, 500))
        imgtk = ImageTk.PhotoImage(image = img)
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
        lmain.after(1, show_frame)


def stopp():
    sys.exit()
    mainWindow.destroy()

def Show_data():
    global red
    global green
    global laplacian_num
    global w
    global w_frame
    fff = PhotoImage(file='blu_cap.PNG')
    Lable_control = Label(mainWindow, image = fff, borderwidth = 0,highlightthickness = 0) #(mainWindow,padx=788,pady=133)
    Lable_control.place(x=5, y=527)

    Lable_draw = Label(mainWindow,padx=388,pady=242)
    Lable_draw.place(x = 805, y = 15)

    Label_empty = Label(mainWindow, text="Empty spaces:", bg = lightBlue2, width = 11, height = 1, font= 'Constantia 18 bold')
    Label_empty.place(x=50, y=580)
    Label_total = Label(mainWindow, text="Total spaces:", bg = lightBlue2, width = 10, height = 1, font= 'Constantia 18 bold')
    Label_total.place(x=52, y=655)

    closeButton = Button(mainWindow, text = "CLOSE", font= 'Courier 20 bold', bg = white, width = 10, height= 1)
    closeButton.configure(command= lambda: stopp())            
    closeButton.place(x=110,y=750)

    Label_use = Label(mainWindow, text="Laplacian use:", bg = lightBlue2, width = 11, height = 1, font= 'Constantia 18 bold')
    Label_use.place(x=448, y=580)


    Label_lapla = Label(mainWindow, text="Laplacian set:", bg = lightBlue2, width = 10, height = 1, font= 'Constantia 18 bold')
    Label_lapla.place(x=450, y=655)

    textBox = Text(mainWindow,font= 'Constantia 13 bold', width = 6, height = 1)
    textBox.place(x=620,y=660)
    def getdt():
        global laplacian_num
        try:
            abc = float(textBox.get("1.0","end-1c"))
            textBox.delete('1.0', END)
            laplacian_num = abc
        except ValueError:
            print("Error.Try again !")
            textBox.delete('1.0', END)
    #inputValue=textBox.get("1.0","end-1c")
    buttonCommit=Button(mainWindow, height=1, font= 'Courier 20 bold',width=10, text="SET", command=lambda: getdt())
    buttonCommit.place(x=518,y=750)

    while(1):
        Lable_usenum = Label(mainWindow,text = "",bg = lightBlue2, width = 3, height = 1, justify=LEFT,font= 'Courier 25 bold')
        Lable_usenum.config(text=laplacian_num)
        Lable_usenum.place(x=630, y=580)
        if (green + red == 16):
            Lable_green = Label(mainWindow,text = "",bg = lightBlue2, width = 2, height = 1, justify=LEFT,font= 'Courier 50 bold')
            Lable_green.config(text=green)
            Lable_green.place(x=230, y=563)

            Lable_red = Label(mainWindow,text = "",bg = lightBlue2, width = 2, height = 1,justify=LEFT,font= 'Courier 50 bold')
            Lable_red.config(text=red)
            Lable_red.place(x=230, y=635)
        time.sleep(1)


def MQTT_PROTO():
    global green 
    global red 

    client = mqtt.Client()
    client.username_pw_set("wwzahnpz", "pl8vWcdzWE8Y")
    a = client.connect("m14.cloudmqtt.com", 19420, 60)
    print(a)
    client.loop_start()
    time.sleep(1)
    while True:
        client.publish("A_BLANK",green)
        client.publish("A_TOTAL",red)
        time.sleep(2)
    client.loop_stop()
    client.disconnect()

try:
    a = Thread(None,show_frame,None,())
   # b = Thread(None,MQTT_PROTO,None,())
    c = Thread(None,Show_data,None,())
    #d = Thread(None,get_data,None,())
    a.start() 
   # b.start()
    c.start()
    #d.start()
    mainWindow.mainloop()
except (KeyboardInterrupt, SystemExit):
    Thread.stop()
