import time
import tkinter as tk
from tkinter import filedialog
from datetime import date
from tkinter import CENTER
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gtts import gTTS
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from playsound import playsound
from PIL import ImageTk, Image
convCoord = []  # sets up array in proper format for table
excelFilePath = '{0}-{1}-{2}_productivity_blister_pack_{3}_workers.xlsx'
port = 'COM4'
lastError = time.time()
# set global variables used everywhere
mLRefresh = True
goal = 0
numPerCycle = 5
numWorker = 2
refreshRate = 240
month = date.today().month
day = date.today().day
year = date.today().year
keepgoing = True
numPerRefresh = 5
start_time = time.time()  # to be compared with curr time in loop
xCoord = [0]  # things used to set up graph./venv
yCoord = [0]  # ideal rate
actualYCoord = [0]  # uses the arudino code
timeDone = 0  # track number of items made
timeLapsed = 0
timeComplete = 60*60*8
window = tk.Tk()  # create window and frames for buttons
window.attributes('-fullscreen', True)
numDone=0
dontCheck=False
try:
    ser = serial.Serial(port, 9600, timeout=1)
except:
    print("changing port later")
lastStateChange = time.time()


def time_convert():  # can be used to show time elapsed. May be used later
    return time.strftime("%H:%M", time.localtime(time.time()))


def changeParamBut():
    def inputStuff():
        # change global variables. If an input is not changed, do not change it
        global goal
        global numPerCycle
        global numWorker
        global refreshRate
        global numPerRefresh
        if len(inputToDo.get(1.0, "end-1c")) != 0: #change goal based on user input
            goal = inputToDo.get(1.0, "end-1c")
        if len(inputNumCycle.get(1.0, "end-1c")) != 0: #change number per cycle based on user input
            numPerCycle = inputNumCycle.get(1.0, "end-1c")
        if len(inputNumWorker.get(1.0, "end-1c")) != 0: #change number of workers based on user input
            numWorker = inputNumWorker.get(1.0, "end-1c")
        if len(inputRefreshRate.get(1.0, "end-1c")) != 0: #change refresh rate based on user input
            refreshRate = int(inputRefreshRate.get(1.0, "end-1c")) * 60
        numPerRefresh = (int(goal) - int(yCoord[len(yCoord) - 1])) / ( #change the number of blister packs per refresh based on the user inputs and the time left
                timeComplete - (timeLapsed - timeDone)) * refreshRate
        if numPerRefresh==0:
            numPerRefresh=5
        top.destroy()

    # create widgets needed for input parameter box
    top = tk.Toplevel(window)
    top.title("Set goals")
    top.attributes('-topmost', True)
    frame1SubWind = tk.Frame(master=top)
    frame1SubWind.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
    frame2SubWind = tk.Frame(master=top)
    frame2SubWind.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
    frame3SubWind = tk.Frame(master=top)
    frame3SubWind.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
    frame4SubWind = tk.Frame(master=top)
    frame4SubWind.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
    inputToDo = tk.Text(frame1SubWind, width=20, height=1)
    inputToDo.pack(side=tk.RIGHT)
    inputNumCycle = tk.Text(frame2SubWind, width=20, height=1)
    inputNumCycle.pack(side=tk.RIGHT)
    inputNumWorker = tk.Text(frame3SubWind, width=20, height=1)
    inputNumWorker.pack(side=tk.RIGHT)
    inputRefreshRate = tk.Text(frame4SubWind, width=20, height=1)
    inputRefreshRate.pack(side=tk.RIGHT)
    toDoLabel = tk.Label(frame1SubWind, text="Number of blister packs to do: ")
    toDoLabel.pack(side=tk.LEFT)
    numCycleLabel = tk.Label(frame2SubWind, text="Number of blister packs per cycle: ")
    numCycleLabel.pack(side=tk.LEFT)
    numWorkerLabel = tk.Label(frame3SubWind, text="The number of workers on this station is: ")
    numWorkerLabel.pack(side=tk.LEFT)
    refreshRateLabel = tk.Label(frame4SubWind, text="The refresh rate on this station in minutes is: ")
    refreshRateLabel.pack(side=tk.LEFT)
    button = tk.Button(top, text="input parameters", command=lambda: inputStuff())
    inputToDo.pack()
    inputNumCycle.pack()
    inputNumWorker.pack()
    inputRefreshRate.pack()
    inputRefreshRate.pack()
    button.pack()
    top.geometry("750x250")

convCoord = []  # sets up array in proper format for table

# close big full screen window. Saves an extra copy of the excel spreadsheet
def killBut():
    # creates table
    global convCoord
    convCoord.append([time_convert(), actualYCoord[len(actualYCoord) - 1]])

    tableCoords = np.array(convCoord)  # convert fake table to real table
    df = pd.DataFrame(tableCoords, columns=['Time', 'numDone'])
    print(df)  # check table looks good
    print(type(df))  # for debugging, show table
    try:
        df.to_excel(
            excelFilePath.format(year, month, day, numWorker))  # push to excel
    except:
        print("bad excel file path")
        if time.time-lastError > 600:
            portFileChange()
            lastError=time.time()
    window.destroy()
    window.quit()
    global keepgoing
    keepgoing = False


# speak. Depending on progress, the message changes
def speakBut():
    if actualYCoord[len(actualYCoord) - 1] >= yCoord[len(yCoord) - 1]:
        message = "You are on track"
    elif actualYCoord[len(actualYCoord) - 1] >= yCoord[len(yCoord) - 1] * .9:
        message = "You are almost on track. You are {0} off".format(
            yCoord[len(yCoord) - 1] - actualYCoord[len(actualYCoord) - 1])
    else:
        message = "You are almost not on track. You are {0} off".format(
            yCoord[len(yCoord) - 1] - actualYCoord[len(actualYCoord) - 1])
    speech = gTTS(text=message)
    speech.save("msg.mp3")
    try:
        playsound('msg.mp3')
    except:
        print("no input device")

# main method that loops. Repeats once a millisecond
def task():
    global timeDone
    global timeLapsed
    global numDone
    global numPerCycle
    global ser
    global dontCheck
    global lastStateChange
    global mLRefresh
    try:
        value = int.from_bytes(ser.read(1), "big") #take arduino input
    except:
        print("kinda need to change ports")
        if time.time-lastError > 600:
            portFileChange()
            lastError=time.time()
    if(time.time()-lastStateChange>=100): #increments number done based on arduino input
        if dontCheck==False:
            if value==1:
                numDone+=int(numPerCycle)
                dontCheck=True
                lastStateChange=time.time()
        else:
            if value==0:
                dontCheck=False
                lastStateChange=time.time()
    timeLapsed = time.time() - start_time
    if timeLapsed % refreshRate <= .1 and mLRefresh == True:  # checks if interval is hit
        mLRefresh = False
        xCoord.append(int(timeLapsed/60))  # add entry to table
        timeDone += numPerRefresh
        yCoord.append(timeDone)
        print(yCoord)
        actualYCoord.append(numDone)
        prodGraph.plot(xCoord, yCoord, 'g', linewidth=10)
        prodGraph.plot(xCoord, actualYCoord, 'b', linewidth=10)

        global canvas
        canvas.draw()
        global convCoord
        convCoord.append([time_convert(), actualYCoord[len(actualYCoord)-1]])

        tableCoords = np.array(convCoord)  # convert fake table to real table
        df = pd.DataFrame(tableCoords, columns=['Time (minutes)', 'numDone'])
        print(df)  # check table looks good
        print(type(df))
        try:
            df.to_excel(
                 excelFilePath.format(year, month, day,
                                                                            numWorker))  # push to excel
        except:
            print("wrong file path")
            if time.time-lastError > 600:
                portFileChange()
                lastError=time.time()
        
        speakBut()
        if actualYCoord[len(actualYCoord) - 1] >= yCoord[len(yCoord) - 1]: #change the icon of top left icon based on progress
            image=Image.open("goodIcon.png")
        elif actualYCoord[len(actualYCoord) - 1] >= yCoord[len(yCoord) - 1] * .9:
            image=Image.open("mediumIcon.png")
        else:
            image=Image.open("badIcon.png")
        global dimension
        image=image.resize((dimension, dimension))
        global progIcon
        progIcon= ImageTk.PhotoImage(image)
        global progButton
        progButton.config(image=progIcon)
    elif timeLapsed % refreshRate >= .1: #ensure no double hit
        mLRefresh = True
       
        
    
    window.update()
    window.after(1, lambda: task())
def portFileChange():
    def windKilller():
        global excelFilePath
        excelFilePath=fileFinder + '/{0}-{1}-{2}_productivity_blister_pack_{3}_workers.xlsx'
        print(excelFilePath)
        errorScreen.destroy()
    def changePort(selection):
        global port
        global ser
        port=selection
        ser = serial.Serial(port, 9600, timeout=1)
    errorScreen = tk.Toplevel(window)
    errorScreen.attributes('-topmost', True)
    errorScreen.title("reset inputs/file path")
    frame1Error = tk.Frame(master=errorScreen)
    frame1Error.pack(fill = tk.BOTH, side = tk.TOP, expand=True)
    frame3Error = tk.Frame(master=errorScreen)
    frame3Error.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
    frame4Error = tk.Frame(master=errorScreen)
    frame4Error.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
    errorMessage=tk.Label(frame1Error, text="You are probably getting this screen because a file path is wrong or the wrong input port is being used. Please select a valid one from the dropdown menu below")
    errorMessage.pack()
    selectArduiPath=tk.Label(frame3Error, text="The Arduino port is ")
    selectArduiPath.pack(side=tk.LEFT)
    ports = serial.tools.list_ports.comports()
    portSelector = tk.OptionMenu(frame3Error, "Please select your port", *ports, command=changePort)
    portSelector.pack(side=tk.RIGHT)
    fileFinder = filedialog.askdirectory()

    closeErrorWindBut = tk.Button(frame4Error, text="close", command=lambda: windKilller())
    closeErrorWindBut.pack()


#more window setup
frame1 = tk.Frame(master=window, width=250, height=100, bg="red")
frame1.pack(fill=tk.BOTH, side=tk.RIGHT, expand=True)
frame2 = tk.Frame(master=window, width=100, bg="#a2c4ca")
frame2.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=True)
frame3 = tk.Frame(master=window, width=50, bg="#a2c4ca")
frame3.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
frame4 = tk.Frame(master=window, width=100, bg="#a2c4ca")
frame4.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=True)
frame5 = tk.Frame(master=window, width=50, bg="#a2c4ca")
frame5.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=True)





# graph
fig = plt.Figure(dpi=100, facecolor="#d0e0e3", edgecolor='#d0e0e3', figsize=(frame1.winfo_x(), frame1.winfo_y()))
prodGraph = fig.add_subplot(111)
prodGraph.xaxis.label.set_color('black')  # setting up X-axis label color to black
prodGraph.yaxis.label.set_color('black')  # setting up Y-axis label color to black
prodGraph.tick_params(axis='x', colors='black')  # setting up X-axis tick color to black
prodGraph.tick_params(axis='y', colors='black')  # setting up Y-axis tick color to black
prodGraph.plot(xCoord, yCoord)
prodGraph.set_xlabel("time")
prodGraph.set_ylabel("cycles completed")
prodGraph.set_title("Productivity graph")
prodGraph.grid()
prodGraph.margins(x=0)
prodGraph.margins(y=0)
canvas = FigureCanvasTkAgg(fig, frame1)
canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
canvas.draw()

# create buttons
image=Image.open("settingsIcon.png")
image=image.resize((int(frame5.winfo_width()*.9*72), int(frame5.winfo_width()*.9*72)))
settingsImage= ImageTk.PhotoImage(image)
buttonChangeParam = tk.Button(frame5, text="Change parameters", image=settingsImage,
                              command=lambda: changeParamBut())
buttonChangeParam.place(relx=0.5, rely=0.5, anchor= CENTER)

image=Image.open("powerIcon.png")
image=image.resize((int(frame5.winfo_width()*.9*72), int(frame5.winfo_width()*.9*72)))
killImage= ImageTk.PhotoImage(image)
buttonKill = tk.Button(frame2, text="close window", image=killImage,
                       command=lambda:
                       killBut())
buttonKill.place(relx=0.5, rely=0.5, anchor= CENTER)

image=Image.open("soundIcons.png")
image=image.resize((int(frame5.winfo_width()*.9*72), int(frame5.winfo_width()*.9*72)))
soundImage= ImageTk.PhotoImage(image)
buttonSpeak = tk.Button(frame4, text="speak", image=soundImage, command=lambda: speakBut())
buttonSpeak.place(relx=0.5, rely=0.5, anchor= CENTER)

image=Image.open("goodIcon.png")
image=image.resize((int(frame5.winfo_width()*.9*72), int(frame5.winfo_width()*.9*72)))
progIcon= ImageTk.PhotoImage(image)
progButton = tk.Button(frame3, text="speak", image=progIcon, command= portFileChange())
progButton.place(relx=0.5, rely=0.5, anchor= CENTER)
dimension=int(frame5.winfo_width()*.9*72)



window.after(1, func=task())
changeParamBut()
window.mainloop()
