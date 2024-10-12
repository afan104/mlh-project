"""
Demonstration of the GazeTracking library.
Check the README.md for complete documentation.
"""

import cv2
from gaze_tracking import GazeTracking
import pyautogui
import numpy as np
import tkinter as tk
import threading
import csv
import pandas as pd
import matplotlib.pyplot as plt

# xWidth, yHeight = pyautogui.size()
xcoef = []
ycoef = []

class Calibrate:
    def __init__(self, window):
        self.window = window
        self.window.attributes('-fullscreen', True)
        self.window.bind("<Escape>", self.exit_fullscreen)  # Allow exit with Esc key
        self.canvas = tk.Canvas(window, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.width = window.winfo_screenwidth()
        self.height = window.winfo_screenheight()

        self.dot_size = 20
        self.corners = [
            (0.5, 0.05),  # Top-left corner
            (.5, .25),
            (0.5, 0.5),  # Center
            (.5, .75),
            (0.5, 0.95),  # Top-right corner
            (0.05, 0.5),  # Bottom-left corner
            (.25, .5),
            (.5, .5),
            (.75, .5),
            (0.95, 0.5)  # Bottom-right corner
        ]
        self.current_corner = 0

        self.message = self.canvas.create_text(
            self.width // 2,
            self.height // 2 - 40,
            text="Please look at the black dot for 2 seconds",
            font=("Arial", 24),
            fill="black"
        )
        self.canvas.itemconfig(self.message, state=tk.NORMAL)

        self.eyeData = [[], [], [], [], [], [], [], [], [], []] # will contain 5 x time x [x, y]
        self.dotShowing = False

        self.gaze_thread = threading.Thread(target=self.track_gaze, daemon=True)
        self.gaze_thread.start()

        x = self.width * self.corners[self.current_corner][0]
        y = self.height * self.corners[self.current_corner][1]

        # Draw a new dot
        self.canvas.create_oval(
            x - self.dot_size / 2,
            y - self.dot_size / 2,
            x + self.dot_size / 2,
            y + self.dot_size / 2,
            fill='black', tags="dot"
        )

        # Start the dot display process
        self.window.after(2000, self.show_dot)

    def track_gaze(self):
        gaze = GazeTracking()
        webcam = cv2.VideoCapture(0)

        while self.current_corner < len(self.corners):
            _, frame = webcam.read()
            gaze.refresh(frame)

            left_pupil = gaze.pupil_left_coords()
            right_pupil = gaze.pupil_right_coords()

            # Store the gaze data only when the dot is displayed
            if self.dotShowing:
                if left_pupil and right_pupil:
                    # Record the average gaze position
                    avgGaze = self.avgPosition(left_pupil, right_pupil)
                    self.eyeData[self.current_corner].append(avgGaze)

            # # Optional: Display the gaze tracking frame
            # cv2.imshow("Gaze Tracking", gaze.annotated_frame())
            # if cv2.waitKey(1) == 27:  # Exit if 'Esc' key is pressed
            #     break

        webcam.release()
        cv2.destroyAllWindows()

    def show_dot(self):
        # Hide the message
        self.canvas.itemconfig(self.message, state=tk.HIDDEN)

        self.dotShowing = True

        # Schedule the dot to disappear after 3 seconds
        self.window.after(2000, self.hide_dot)

    def hide_dot(self):
        # Remove the dot
        self.canvas.delete("dot")
        self.dotShowing = False

        # Move to the next corner
        self.current_corner += 1

        if self.current_corner < len(self.corners):
            # Update and show the message for the next corner
            self.canvas.itemconfig(self.message, state=tk.NORMAL)

            x = self.width * self.corners[self.current_corner][0]
            y = self.height * self.corners[self.current_corner][1]

            # Draw a new dot
            self.canvas.create_oval(
                x - self.dot_size / 2,
                y - self.dot_size / 2,
                x + self.dot_size / 2,
                y + self.dot_size / 2,
                fill='black', tags="dot"
            )

            # Wait for 3 seconds before showing the next dot
            self.window.after(1500, self.show_dot)
        else:
            # Exit fullscreen if all corners have been displayed
            self.exit_fullscreen()

    def exit_fullscreen(self, event=None):
        with open('../gaze_data2.csv', 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)

            for corner_data in self.eyeData:
                for point in corner_data:
                    csv_writer.writerow(point)
                csv_writer.writerow([])  # Blank line to separate corners
        self.window.attributes('-fullscreen', False)
        self.window.destroy()


        avgData = []
        for i in range(len(self.corners)):
            avgData.append(np.mean(self.eyeData[i], axis=0))

        global xcoef, ycoef
        xcoef, ycoef = self.calculateFunction(avgData, pyautogui.size()[0], pyautogui.size()[1])

    def avgPosition(self, leftEye, rightEye):
        return [(leftEye[0] + rightEye[0]) / 2, (leftEye[1] + rightEye[1]) / 2]

    def calculateFunction(self, data, xWidth, yWidth):
        corner_data = pd.DataFrame(data, columns=["x", "y"])  # Convert to DataFrame

        x_eye = np.array(corner_data['x'][5:])
        y_eye = np.array(corner_data['y'][:5])

        x_pixel = np.array([xWidth*.05, xWidth*.25, xWidth * .5, xWidth * .75, xWidth * .95])
        y_pixel = np.array([yWidth*.05, yWidth*.25, yWidth * .5, yWidth * .75, yWidth * .95])

        ycoeffs = np.polyfit(y_eye, y_pixel, 2)
        outputy = ycoeffs[0] * y_eye ** 2 + ycoeffs[1] * y_eye + ycoeffs[2]

        xcoeffs = np.polyfit(x_eye, x_pixel, 2)
        outputx = xcoeffs[0] * x_eye ** 2 + xcoeffs[1] * x_eye + xcoeffs[2]
        print(xcoeffs)
        print(x_eye)
        print(x_pixel)
        print(outputx)

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

def runTracking(xCoeffs, yCoeffs):
    gaze = GazeTracking()
    webcam = cv2.VideoCapture(0)
    width = pyautogui.size()[0]
    height = pyautogui.size()[1]
    xpositions = []
    ypositions = []
    avg_frames = 3  # Number of frames to average over


    while True:
        # We get a new frame from the webcam
        _, frame = webcam.read()

        # We send this frame to GazeTracking to analyze it
        gaze.refresh(frame)

        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        if left_pupil and right_pupil:
            eyegaze = [(left_pupil[0] + right_pupil[0]) / 2, (left_pupil[1] + right_pupil[1]) / 2]
            smoothedavg = smooth_eye_position(eyegaze, xpositions, ypositions, avg_frames)
            print(smoothedavg)
            xPixel = np.clip(xCoeffs[0] * smoothedavg[0] ** 2 + xCoeffs[1] * smoothedavg[0] + xCoeffs[2], 0, width)
            yPixel = np.clip((yCoeffs[0] * smoothedavg[1] ** 2 + yCoeffs[1] * smoothedavg[1] + yCoeffs[2]), 0, height)
            # pyautogui.moveTo(xPixel, int(yPixel))
            print(f"{xPixel} {yPixel}")

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
    root = tk.Tk()
    app = Calibrate(root)
    root.mainloop()
    xcoef = [-4.5920409855638615, 3191.7808455852887, -552069.2501368718] # 360 to 370
    ycoef = [-2.478038148486773, 892.021176404922, -78466.25432233479] # 153 to 161
    runTracking(xcoef, ycoef)



