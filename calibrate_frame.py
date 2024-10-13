"""
Demonstration of the GazeTracking library.
Check the README.md for complete documentation.
"""

import cv2
from GazeTracking.gaze_tracking import GazeTracking
import tkinter as tk
import ttkbootstrap as ttk
import threading
import pyautogui
import numpy as np
import time

class CalibrateScreen(tk.Frame):
    def __init__(self, window, gazeObject, camObject, cellWidth, cellHeight, app):
        self.window = window
        self.window.attributes("-fullscreen", True)
        self.app = app

        # Create a full-screen canvas
        self.canvas = tk.Canvas(window, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Keybinds
        self.window.bind("<space>", self.dot_on)

        # screen size info
        self.width = window.winfo_screenwidth()
        self.height = window.winfo_screenheight()

        # Tranformation Function Paramters
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.screenWidth = pyautogui.size()[0]
        self.screenHeight = pyautogui.size()[1]
        self.xcoeffs = 0
        self.ycoeffs = 0

        # Instructions message
        self.display_instructions()

        # Corner dots information
        self.dotSize = 20
        self.currentPosition = 0
        self.dotPositions = [
            (0.5, 0.05),  # Top-left corner
            (0.5, 0.25),
            (0.5, 0.5),  # Center
            (0.5, 0.75),
            (0.5, 0.95),  # Top-right corner
            (0.05, 0.5),  # Bottom-left corner
            (0.25, 0.5),
            (0.5, 0.5),
            (0.75, 0.5),
            (0.95, 0.5),  # Bottom-right corner
        ]
        self.eyeData = [[] for _ in range(len(self.dotPositions))]
        self.dotShowing = False
        self.initialize_dots_as_circles()

        # Initialize gaze tracking
        self.gaze = gazeObject
        self.webcam = camObject

        # Create a thread to track the gaze
        self.collectData = False
        self.calibrate = True
        self.gaze_thread = threading.Thread(target=self.track_gaze, daemon=True)
        self.gaze_thread.start()
        self.lock = threading.Lock()

        # Timing variables
        self.timeDelay = 500
        self.timeCollection = 3000

    def display_instructions(self):
        """
        Displays instructions to look at red dot.
        Creates a color changing block to indicate progress.
        """
        labelTop = ttk.Label(
            self.app.root,
            text="Look at the red dot until it turns green.",
            style="BoldInfo.TLabel",
        )
        labelTop.place(x=100, y=50)
        labelBottom = ttk.Label(
            self.app.root,
            text="Press space to continue.                           ",
            style="ItalicInfo.TLabel",
        )
        labelBottom.place(x=100, y=100)

    def create_dot(self, corner_index, fill, outline=""):
        """
        Creates a dot at the specified location (corner_index) on the screen with
        the specified fill and outline.
        """
        corner = self.dotPositions[corner_index]
        x = self.width * corner[0]
        y = self.height * corner[1]
        self.canvas.create_oval(
            x - self.dot_size / 2,
            y - self.dot_size / 2,
            x + self.dot_size / 2,
            y + self.dot_size / 2,
            fill=fill,
            outline=outline,
            tags="dot",
        )

    def initialize_dots_as_circles(self):
        """
        Initializes the dots as circles on the screen.
        The first dot is red, and the rest are empty circles.
        """
        # first dot is red
        self.create_dot(0, fill="red")

        # other dots empty circles
        for i in range(1, len(self.dotPositions)):
            self.create_dot(i, fill="", outline="black")

    def dot_on(self, event=None):
        """
        Starts measuring at current dot and signals for gaze tracking.
        """
        if self.currentPosition == len(self.dotPositions):
            self.window.unbind("<space>")
            return
        # current position on the screen
        x = self.width * self.dotPositions[self.currentPosition][0]
        y = self.height * self.dotPositions[self.currentPosition][1]

        # Make dot yellow and start gaze tracking collection
        self.create_dot(self.currentPosition, fill="yellow")
        self.collectData = True

        self.dotShowing = True  # turns on gaze tracking
        self.window.after(2000, self.dot_off)

        

    def dot_off(self, event=None):
        """
        After 2 seconds, turns off measuring at dot and stops gaze tracking.
        Changes dot to green color and next dot to red color.
        """
        with self.lock:
            if len(self.eyeData[self.currentPosition]) > 10:
                self.collectData = False

                self.currentPosition += 1
                self.dotShowing = False  # turns off gaze tracking
                self.create_dot(self.currentPosition - 1, fill="green")

                # make next one red
                if self.currentPosition != len(self.dotPositions):
                    self.create_dot(self.currentPosition, fill="red")
                else:
                    self.finish_calibration()
            else:
                print("not enough data collected, waiting...")
                self.window.after(100, self.dot_off)

    def track_gaze(self):
        """
        Tracks the gaze of the user and records the pupil position data.
        """
    
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
                        # print(self.eyeData)
            else:
                time.sleep(0.1)


        # when all corners have been calibrated, calculate the coefficients
        if self.currentPosition == len(self.dotPositions):
            # clear screen
            for widget in self.app.root.winfo_children():
                widget.destroy()
            # TODO: calculating coefficients

            # Display message that calibrating/complete calibration
            self.window.attributes("-fullscreen", False)
            self.window.geometry("800x600")
            ttk.Label(self.app.root, text="Calibration complete").pack(pady=20)

    def exit_fullscreen(self, event=None):
        # stop thread
        self.calibrate = False
        if self.gaze_thread.is_alive():
            self.gaze_thread.join()

        # close calibration window
        self.window.attributes('-fullscreen', False)
        self.window.destroy()

        # mappingfunction
        self.calculateFunctionGrid()

    def calculateFunctionGrid(self):
        # setup grid 
        gridWidth = self.screenWidth // self.cellWidth
        gridHeight = self.screenHeight // self.cellHeight

        # stack the eye data for each dot 
        data = np.vstack(self.eyeData)
        x_eye = data[:,0]
        y_eye = x_eye = data[:,1]

        # stack the targets data
        targets = []
        for i in range(len(self.dotPositions)):
            xPix = int(self.dotPositions[i][0]*gridWidth) # x
            yPix = int(self.dotPositions[i][1]*gridHeight) # y
            for j in range(len(self.eyeData[i])):
                targets.append([xPix, yPix])
        targets = np.array(targets)
        x_pixel = np.array(targets[:,0])
        y_pixel = np.array(targets[:,1])

        # calculate polyfit
        self.app.xcoeffs = np.polyfit(x_eye, x_pixel, 2)
        self.app.ycoeffs = np.polyfit(y_eye, y_pixel, 2)
        print(f"{self.xcoeffs}, {self.ycoeffs}")
    
    