import cv2
from GazeTracking.gaze_tracking import GazeTracking
import pyautogui
import numpy as np
import tkinter as tk
import threading
import csv
import pandas as pd
import matplotlib.pyplot as plt
import time

from selenium import webdriver
from selenium.webdriver.common.by import By



# Global Variables
xcoef = []
ycoef = []
screenWidth = pyautogui.size()[0]
screenHeight = pyautogui.size()[1]
global model

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
        xDotPositions = np.linspace(.05, .95, 5)
        yDotPositions = np.linspace(.05, .95, 5)
        self.dotPositions = []
        for x in xDotPositions:
            for y in yDotPositions:
                self.dotPositions.append((x, y))

        # print(self.dotPositions)
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
        self.eyeData = [[] for _ in range(len(self.dotPositions))] # will contain 5 x time x [x, y]

        # initialize thread
        self.collectData = False
        self.calibrate = True
        self.gaze_thread = threading.Thread(target=self.trackGaze, daemon=True)
        self.gaze_thread.start()
        self.lock = threading.Lock()

        # timing of dots being shown on screen
        self.timeDelay = 500
        self.timeCollection = 3000

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
                        # print(self.eyeData)
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
            if len(self.eyeData[self.currentPosition]) > 5:
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
        # stackedData = np.vstack(self.eyeData)
        # mappingfunction
        global xcoef, ycoef
        xcoef, ycoef = self.calculateFunctionGrid(pyautogui.size()[0], pyautogui.size()[1])

    def calculateFunctionGrid(self, xWidth, yHeight):
        data = np.vstack(self.eyeData)
        cellWidth = 40
        cellHeight = 40
        gridWidth = xWidth // cellWidth
        gridHeight = yHeight // cellHeight
        targets = []
        for i in range(len(self.dotPositions)):
            xPix = int(self.dotPositions[i][0]*gridWidth) # x
            yPix = int(self.dotPositions[i][1]*gridHeight) # y
            for j in range(len(self.eyeData[i])):
                targets.append([xPix, yPix])
        targets = np.array(targets)
        corner_data = pd.DataFrame(data, columns=["x", "y"])  # Convert to DataFrame
        x_eye = np.array(corner_data['x'])
        y_eye = np.array(corner_data['y'])
        x_pixel = np.array(targets[:,0])
        y_pixel = np.array(targets[:,1])
        # x_pixel = np.array([gridWidth*.05, gridWidth*.25, gridWidth * .5, gridWidth * .75, gridWidth * .95])
        # y_pixel = np.array([gridHeight*.05, gridHeight*.25, gridHeight * .5, gridHeight * .75, gridHeight * .95])

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
    cellWidth = 30
    cellHeight = 30
    gridWidth = width // cellWidth
    gridHeight = height // cellHeight
    xpositions = []
    ypositions = []
    avg_frames = 5  # Number of frames to average over

    # launch google
    mainGoogle = 'https://www.google.com/'
    # chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
    # webbrowser.get(chrome_path).open(mainGoogle)

    driver = webdriver.Chrome()
    driver.maximize_window()
    # driver.execute_script("document.body.style.zoom='1.5'")
    driver.get(mainGoogle)

    scannedElements = getClickableElements(driver )
    scanFlag = False

    # low pass filter
    controlMouse = True
    updateNow = 0
    while controlMouse:
        # We get a new frame from the webcam
        _, frame = webcam.read()

        # We send this frame to GazeTracking to analyze it
        gaze.refresh(frame)

        # if cv2.waitKey(1) == 27:
        #     break

        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        if left_pupil and right_pupil:
            eyegaze = [(left_pupil[0] + right_pupil[0]) / 2, (left_pupil[1] + right_pupil[1]) / 2]
            smoothedavg = smooth_eye_position(eyegaze, xpositions, ypositions, avg_frames)
            if updateNow > 1:
                # xPixel, yPixel = predictxy(smoothedavg, gridWidth, gridHeight, cellWidth, cellHeight)
                xPixel = np.clip(int(xCoeffs[0] * smoothedavg[0] ** 2 + xCoeffs[1] * smoothedavg[0] + xCoeffs[2]), 0, gridWidth-1)*cellWidth+cellWidth/2
                yPixel = np.clip(int(yCoeffs[0] * smoothedavg[1] ** 2 + yCoeffs[1] * smoothedavg[1] + yCoeffs[2]), 0, gridHeight-1)*cellHeight+cellWidth/2
                xPixel, yPixel = weight_elements(xPixel, yPixel, scannedElements)
                pyautogui.moveTo(xPixel, yPixel)
                updateNow = 0
        updateNow +=1

    webcam.release()
    cv2.destroyAllWindows()

def predictxy(eye_data, gridWidth,gridHeight, cellWidth, cellHeight):
    global model
    out = model.predict(np.array(eye_data).reshape(1, -1))
    print(out)
    xPixel = np.clip(int(out[0][0]), 0, gridWidth-1)*cellWidth+cellWidth/2
    yPixel = np.clip(int(out[0][1]), 0, gridHeight-1)*cellHeight+cellWidth/2
    return [xPixel, yPixel]


def smooth_eye_position(new_position, xlist, ylist, frameAvg):
    xlist.append(new_position[0])
    if(len(xlist) > frameAvg ):
        xlist.pop(0)
    ylist.append(new_position[1])
    if (len(ylist) > frameAvg):
        ylist.pop(0)
    return [np.mean(xlist), np.mean(ylist)]

def getClickableElements(driver):
    # driver.get(link)
    # Get all button and anchor (link) elements
    buttons = driver.find_elements(By.CSS_SELECTOR, 'button, a')
    searchbars= driver.find_elements(By.NAME, 'q')
    elements = []
    for button in buttons:
        if button.is_displayed():  # Only consider visible buttons
            location = button.location  # Get the top-left coordinates of the element
            size = button.size  # Get the width and height of the element

            # Calculate the center coordinates
            center_x = location['x'] + size['width'] / 2
            center_y = location['y'] + size['height'] / 2
            elements.append([center_x, center_y])

            print(f"Clickable element: {button.text}, Center: ({center_x}, {center_y})")
    for searchbar in searchbars:
        location = searchbar.location
        size = searchbar.size  # Get the width and height of the element

        # Calculate the center coordinates
        center_x = location['x'] + size['width'] / 2
        center_y = location['y'] + size['height'] / 2
        elements.append([center_x, center_y])

        print(f"Clickable element: {searchbar.text}, Center: ({center_x}, {center_y})")

    return elements


def calculate_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def calculate_distance2(x1, y1, x2, y2):
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def getClickableElements2(driver):
    # driver.get(link)
    # Get all button and anchor (link) elements
    buttons = driver.find_elements(By.CSS_SELECTOR, 'button, a')
    searchbars= driver.find_elements(By.NAME, 'q')
    buttons.extend(searchbars)
    return buttons

def weight_elements2(gaze_x, gaze_y, elements, snap_threshold=50, weight_exponent=3):
    gaze_point = (gaze_x, gaze_y)
    # Loop through each element to check proximity
    # Apply weights based on proximity
    total_weight = 0
    weighted_position = np.array([0.0, 0.0])
    for element in elements:
        if element.is_displayed():
            rect = element.rect  # Get the bounding box
            element_center_x = rect['x'] + rect['width'] / 2
            element_center_y = rect['y'] + rect['height'] / 2

            # Check the distance to the corners of the bounding box
            corners = [
                (rect['x'], rect['y']),  # Top-left
                (rect['x'] + rect['width'], rect['y']),  # Top-right
                (rect['x'], rect['y'] + rect['height']),  # Bottom-left
                (rect['x'] + rect['width'], rect['y'] + rect['height']),  # Bottom-right
            ]

            for corner in corners:
                distance = calculate_distance2(gaze_x, gaze_y, corner[0], corner[1])
                if distance < snap_threshold:
                    print(f"Snapping to element: {element.tag_name} at {corner}")
                    weight = (snap_threshold - distance) ** weight_exponent
                    weighted_position += np.array([element_center_x, element_center_y]) * weight
                    total_weight += weight

                    break  # Exit if we found a close enough element
    # Return weighted average position if within threshold
    if total_weight > 0:
        return weighted_position / total_weight
    else:
        return gaze_point  # Return original gaze point if no snapping

# Function to weight elements by proximity
def weight_elements(gaze_x, gaze_y, elements, snap_threshold=120, weight_exponent=6):
    gaze_point = (gaze_x, gaze_y)
    distances = []

    for index, element in enumerate(elements):
        dist = calculate_distance(gaze_point, element)
        distances.append((index, dist))

    # Sort clickable elements by distance from gaze point
    distances = sorted(distances, key=lambda tup: tup[1])

    # Apply weights based on proximity
    total_weight = 0
    weighted_position = np.array([0.0, 0.0])

    for element, distance in distances:
        if distance < snap_threshold:
            weight = (snap_threshold - distance) ** weight_exponent
            weighted_position += np.array(elements[element]) * weight
            total_weight += weight

    # Return weighted average position if within threshold
    if total_weight > 0:
        return weighted_position / total_weight
    else:
        return gaze_point  # Return original gaze point if no snapping


if __name__ == "__main__":
    gaze = GazeTracking()
    webcam = cv2.VideoCapture(0)

    root = tk.Tk()
    app = Calibrate(root, gaze, webcam)
    root.mainloop()
    runTracking(xcoef, ycoef, gaze, webcam)



