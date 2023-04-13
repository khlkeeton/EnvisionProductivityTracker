import time
import tkinter as tk
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gtts import gTTS
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from playsound import playsound

# set global variables used everywhere
goal = 0
numPerCycle = 0
numWorker = 0
refreshRate = 5
month = date.today().month
day = date.today().day
year = date.today().year
keepgoing = True
numPerRefresh = 5
start_time = time.time()  # to be compared with curr time in loop
xCoord = [0]  # things used to set up graph
yCoord = [0]  # ideal rate
actualYCoord = [0]  # uses the arudino code
timeDone = 0  # track number of items made
timeLapsed = 0
timeComplete = 60 * 60 * 8


def time_convert():  # can be used to show time elapsed. May be used later
    return time.strftime("%H:%M", time.localtime(time.time()))


def changeParamBut():
    def inputstuff():
        # change global variables. If an input is not changed, do not change it
        global goal
        global numPerCycle
        global numWorker
        global refreshRate
        global numPerRefresh
        if len(inputToDo.get(1.0, "end-1c")) != 0:
            goal = inputToDo.get(1.0, "end-1c")
        if len(inputNumCycle.get(1.0, "end-1c")) != 0:
            numPerCycle = inputNumCycle.get(1.0, "end-1c")
        if len(inputNumWorker.get(1.0, "end-1c")) != 0:
            numWorker = inputNumWorker.get(1.0, "end-1c")
        if len(inputRefreshRate.get(1.0, "end-1c")) != 0:
            refreshRate = int(inputRefreshRate.get(1.0, "end-1c")) * 60
        numPerRefresh = (int(goal) - int(yCoord[len(yCoord) - 1])) / (
                timeComplete - (timeLapsed - timeDone)) * refreshRate
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
    button = tk.Button(top, text="input parameters", command=inputstuff())
    inputToDo.pack()
    inputNumCycle.pack()
    inputNumWorker.pack()
    inputRefreshRate.pack()
    inputRefreshRate.pack()
    button.pack()
    top.geometry("750x250")


# close big full screen window. Saves an extra copy of the excel spreadsheet
def killBut():
    # creates table
    convCoord = []  # sets up array in proper format for table
    i = 0
    while i < len(xCoord):
        convCoord.append([time_convert(), yCoord[i]])
        i += 1

    tableCoords = np.array(convCoord)  # convert fake table to real table
    df = pd.DataFrame(tableCoords, columns=['Time', 'numDone'])
    print(df)  # check table looks good
    print(type(df))  # for debugging, show table
    df.to_excel(
        '{0}-{1}-{2}_productivity_blister_pack_{3}_workers.xlsx'.format(year, month, day, numWorker))  # push to excel
    window.destroy()
    window.quit()
    global keepgoing
    keepgoing = False


# speak. Depending on parameters, the message changes
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
    playsound('msg.mp3')


# main method that loops. Repeats once a millisecond
def task():
    global timeDone
    global timeLapsed
    timeLapsed = time.time() - start_time
    if timeLapsed % int(refreshRate) <= .1:  # checks if interval is hit
        timeDone += numPerRefresh
        xCoord.append(int(timeLapsed / 60))  # add entry to table
        yCoord.append(timeDone)
        prodGraph.plot(xCoord, yCoord, 'g')
        prodGraph.plot(xCoord, actualYCoord, 'b')
        canvas.draw()
        convCoord = []  # sets up array in proper format for table
        i = 0
        while i < len(xCoord):
            convCoord.append([time_convert(), yCoord[i]])
            i += 1

        tableCoords = np.array(convCoord)  # convert fake table to real table
        df = pd.DataFrame(tableCoords, columns=['Time', 'numDone'])
        print(df)  # check table looks good
        print(type(df))
        df.to_excel(
            '{0}-{1}-{2}_productivity_blister_pack_{3}_workers.xlsx'.format(year, month, day,
                                                                            numWorker))  # push to excel
        speakBut()
        while timeLapsed % int(refreshRate) < .1:  # ensure loop not re-entered immediately
            timeLapsed = time.time() - start_time

    window.update()
    window.after(1, lambda: task())


window = tk.Tk()  # create window and frames for buttons
window.attributes('-fullscreen', True)
frame1 = tk.Frame(master=window, width=250, height=100, bg="red")
frame1.pack(fill=tk.BOTH, side=tk.RIGHT, expand=True)
frame2 = tk.Frame(master=window, width=100, bg="YELLOW")
frame2.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=True)
frame3 = tk.Frame(master=window, width=50, bg="blue")
frame3.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
frame4 = tk.Frame(master=window, width=100, bg="BLUE")
frame4.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=True)
frame5 = tk.Frame(master=window, width=50, bg="yellow")
frame5.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=True)

# graph
fig = plt.Figure(dpi=100, facecolor="white", edgecolor='white', figsize=(frame1.winfo_x(), frame1.winfo_y()))
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
buttonChangeParam = tk.Button(frame5, text="Change parameters", command=lambda: changeParamBut())
buttonChangeParam.pack()
buttonKill = tk.Button(frame2, text="close window",
                       command=lambda:
                       killBut())
buttonKill.pack()
buttonSpeak = tk.Button(frame4, text="speak", command=lambda: speakBut())
buttonSpeak.pack()

window.after(1, func=task())
changeParamBut()
window.mainloop()
