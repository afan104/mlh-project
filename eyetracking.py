import cv2
from gaze_tracking import GazeTracking
import pyautogui
import numpy as np
import tkinter as tk
import threading
import csv
import pandas as pd
import matplotlib.pyplot as plt
import time

# Global Variables
xcoef = []
ycoef = []
screenWidth = pyautogui.size()[0]
screenHeight = pyautogui.size()[1]

class Calibrate:
    def __init__(self, window, gaze, webcam):
        # setup canvas
        self.window = window
        self.window.attributes('-fullscreen', True)
        self.window.bind("<Escape>", self.exit_fullscreen)  # Allow exit with Esc key
        self.canvas = tk.Canvas(window, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.width = window.winfo_screenwidth()
        self.height = window.winfo_screenheight()

        # initialize dots
        self.dotSize = 20
        self.dotPositions = [
            (0.5, 0.05),
            (.5, .25),
            (0.5, 0.5),
            (.5, .75),
            (0.5, 0.95),
            (0.05, 0.5),
            (.25, .5),
            (.5, .5),
            (.75, .5),
            (0.95, 0.5)
        ]
        self.currentPosition = 0 # index
        x = self.width * self.dotPositions[self.currentPosition][0]
        y = self.height * self.dotPositions[self.currentPosition][1]
        self.dot = self.canvas.create_oval(
            x - self.dotSize / 2,
            y - self.dotSize / 2,
            x + self.dotSize / 2,
            y + self.dotSize / 2,
            fill='black', tags="dot"
        )
        self.dotShown = True

        # intiialize message
        self.message = self.canvas.create_text(
            self.width // 2,
            self.height // 2 - 40,
            text="Please look at the black dot for 2 seconds",
            font=("Arial", 24),
            fill="black"
        )
        self.canvas.itemconfig(self.message, state=tk.NORMAL) # draw messaage
        self.msgShown = True

        #initialize gaze tracking
        self.gaze = gaze
        self.webcam = webcam

        # init eye data array
        self.eyeData = [[] for _ in range(10)] # will contain 5 x time x [x, y]

        # initialize thread
        self.collectData = False
        self.calibrate = True
        self.gaze_thread = threading.Thread(target=self.trackGaze, daemon=True)
        self.gaze_thread.start()
        self.lock = threading.Lock()

        # timing of dots being shown on screen
        self.timeDelay = 500
        self.timeCollection = 1000

        self.window.after(self.timeDelay, self.startCollection)

    def trackGaze(self):
        while(self.calibrate):
            if (self.collectData):
                _, frame = self.webcam.read()
                self.gaze.refresh(frame)

                left_pupil = self.gaze.pupil_left_coords()
                right_pupil = self.gaze.pupil_right_coords()

                if left_pupil and right_pupil and self.currentPosition < len(self.dotPositions):
                    # Record the average gaze position
                    avgGaze = [(left_pupil[0] + right_pupil[0]) / 2, (left_pupil[1] + right_pupil[1]) / 2]
                    with self.lock:
                        self.eyeData[self.currentPosition].append(avgGaze)
            else:
                time.sleep(0.1)

    def startCollection(self):
        # Hide the message
        self.canvas.itemconfig(self.message, state=tk.HIDDEN)

        # start the thread
        self.collectData = True

        # Schedule the dot to disappear
        self.window.after(self.timeCollection, self.updateDot)

    def updateDot(self):
        # stop thread
        with self.lock:
            if len(self.eyeData[self.currentPosition]) > 10:
                self.collectData = False

                # update dot and message
                self.currentPosition += 1
                if self.currentPosition < len(self.dotPositions):
                    # Update and show the message for the next corner
                    self.canvas.itemconfig(self.message, state=tk.NORMAL)
                    x = self.width * self.dotPositions[self.currentPosition][0]
                    y = self.height * self.dotPositions[self.currentPosition][1]
                    newCoords = [x - self.dotSize / 2,
                                 y - self.dotSize / 2,
                                 x + self.dotSize / 2,
                                 y + self.dotSize / 2
                                 ]
                    self.canvas.coords(self.dot, *newCoords)

                    # Wait for 1.5 seconds before showing the next dot
                    self.window.after(self.timeDelay, self.startCollection)
                else:
                    # Exit fullscreen if all corners have been displayed
                    self.exit_fullscreen()
            else:
                print("not enough data collected, waiting...")
                self.window.after(100, self.updateDot)

    def exit_fullscreen(self, event=None):
        # stop thread
        self.calibrate = False
        if self.gaze_thread.is_alive():
            self.gaze_thread.join()

        # save data to csv
        with open('../gaze_data2.csv', 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for corner_data in self.eyeData:
                for point in corner_data:
                    csv_writer.writerow(point)
                csv_writer.writerow([])  # Blank line to separate corner

        # close calibration window
        self.window.attributes('-fullscreen', False)
        self.window.destroy()

        # average the data for each dot position
        avgData = []
        for i in range(len(self.dotPositions)):
            avgData.append(np.mean(self.eyeData[i], axis=0))

        # mappingfunction
        global xcoef, ycoef
        xcoef, ycoef = self.calculateFunctionGrid(avgData, pyautogui.size()[0], pyautogui.size()[1])

    def calculateFunctionGrid(self, data, xWidth, yHeight):
        cellWidth = 20
        cellHeight = 20
        gridWidth = xWidth // cellWidth
        gridHeight = yHeight // cellHeight

        corner_data = pd.DataFrame(data, columns=["x", "y"])  # Convert to DataFrame
        x_eye = np.array(corner_data['x'][5:])
        y_eye = np.array(corner_data['y'][:5])

        x_pixel = np.array([gridWidth*.05, gridWidth*.25, gridWidth * .5, gridWidth * .75, gridWidth * .95])
        y_pixel = np.array([gridHeight*.05, gridHeight*.25, gridHeight * .5, gridHeight * .75, gridHeight * .95])

        ycoeffs = np.polyfit(y_eye, y_pixel, 2)
        outputy = ycoeffs[0] * y_eye ** 2 + ycoeffs[1] * y_eye + ycoeffs[2]

        xcoeffs = np.polyfit(x_eye, x_pixel, 2)
        outputx = xcoeffs[0] * x_eye ** 2 + xcoeffs[1] * x_eye + xcoeffs[2]

        plt.figure(1)  # Create a new figure
        plt.scatter(x_eye, x_pixel, alpha=0.5)
        plt.plot(x_eye, outputx)
        plt.title("Gaze Data")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.grid()
        plt.show()  # Display each plot

        plt.figure(1)  # Create a new figure
        plt.scatter(y_eye, y_pixel, alpha=0.5)
        plt.plot(y_eye, outputy)
        plt.title("Gaze Data")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.grid()
        plt.show()  # Display each plot

        return [xcoeffs, ycoeffs]

def runTracking(xCoeffs, yCoeffs, gaze, webcam):
    width = pyautogui.size()[0]
    height = pyautogui.size()[1]
    cellWidth = 20
    cellHeight = 20
    gridWidth = width // cellWidth
    gridHeight = height // cellHeight
    xpositions = []
    ypositions = []
    avg_frames = 3  # Number of frames to average over

    controlMouse = True
    while controlMouse:
        # We get a new frame from the webcam
        _, frame = webcam.read()

        # We send this frame to GazeTracking to analyze it
        gaze.refresh(frame)

        if cv2.waitKey(1) == 27:
            break

        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        if left_pupil and right_pupil:
            eyegaze = [(left_pupil[0] + right_pupil[0]) / 2, (left_pupil[1] + right_pupil[1]) / 2]
            smoothedavg = smooth_eye_position(eyegaze, xpositions, ypositions, avg_frames)
            xPixel = np.clip(int(xCoeffs[0] * smoothedavg[0] ** 2 + xCoeffs[1] * smoothedavg[0] + xCoeffs[2]), 0, gridWidth-1)*cellWidth+cellWidth/2
            yPixel = np.clip(int(yCoeffs[0] * smoothedavg[1] ** 2 + yCoeffs[1] * smoothedavg[1] + yCoeffs[2]), 0, gridHeight-1)*cellHeight+cellWidth/2
            pyautogui.moveTo(xPixel, int(yPixel))

    webcam.release()
    cv2.destroyAllWindows()

def smooth_eye_position(new_position, xlist, ylist, frameAvg):
    xlist.append(new_position[0])
    if(len(xlist) > frameAvg ):
        xlist.pop(0)
    ylist.append(new_position[1])
    if (len(ylist) > frameAvg):
        ylist.pop(0)
    return [np.mean(xlist), np.mean(ylist)]

if __name__ == "__main__":
    gaze = GazeTracking()
    webcam = cv2.VideoCapture(0)
    
    root = tk.Tk()
    app = Calibrate(root, gaze, webcam)
    root.mainloop()
    runTracking(xcoef, ycoef, gaze, webcam)



