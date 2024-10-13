"""
Demonstration of the GazeTracking library.
Check the README.md for complete documentation.
"""

import cv2
from GazeTracking.gaze_tracking import GazeTracking
import tkinter as tk
import ttkbootstrap as ttk
import threading

# xWidth, yHeight = pyautogui.size()
xcoef = []
ycoef = []


class CalibrateScreen(tk.Frame):
    def __init__(self, window, app):
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

        # Instructions message
        self.display_instructions()

        # Corner dots information
        self.dot_size = 20
        self.current_corner = 0
        self.corners = [
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
        self.eyeData = [
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ]
        self.dotShowing = False
        self.initialize_dots_as_circles()

        # Create a thread to track the gaze
        self.gaze_thread = threading.Thread(target=self.track_gaze, daemon=True)
        self.gaze_thread.start()

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

        # self.message = self.canvas.create_text(
        #     self.width // 3,
        #     self.height // 6,
        #     text="Look at the red dot for 2 seconds. \nPress space to begin timer.",
        #     font=("Arial", 24),
        #     fill="white",
        # )

    def create_dot(self, corner_index, fill, outline=""):
        """
        Creates a dot at the specified location (corner_index) on the screen with
        the specified fill and outline.
        """
        corner = self.corners[corner_index]
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
        for i in range(1, len(self.corners)):
            self.create_dot(i, fill="", outline="black")

    def dot_on(self, event=None):
        """
        Starts measuring at current dot and signals for gaze tracking.
        """
        if self.current_corner == len(self.corners):
            self.window.unbind("<space>")
            return
        # current position on the screen
        x = self.width * self.corners[self.current_corner][0]
        y = self.height * self.corners[self.current_corner][1]

        # Make dot yellow and start gaze tracking collection
        self.create_dot(self.current_corner, fill="yellow")

        self.dotShowing = True  # turns on gaze tracking
        self.window.after(2000, self.dot_off)

        self.current_corner += 1

    def dot_off(self, event=None):
        """
        After 2 seconds, turns off measuring at dot and stops gaze tracking.
        Changes dot to green color and next dot to red color.
        """
        self.dotShowing = False  # turns off gaze tracking
        self.create_dot(self.current_corner - 1, fill="green")

        # make next one red
        if self.current_corner != len(self.corners):
            self.create_dot(self.current_corner, fill="red")

    def track_gaze(self):
        """
        Tracks the gaze of the user and records the pupil position data.
        """
        gaze = GazeTracking()
        webcam = cv2.VideoCapture(0)

        while self.current_corner < len(self.corners):
            _, frame = webcam.read()
            gaze.refresh(frame)  # processing step

            left_pupil = gaze.pupil_left_coords()
            right_pupil = gaze.pupil_right_coords()

            # Store the gaze data only when the dot is displayed
            if self.dotShowing:
                if left_pupil and right_pupil:
                    # Record the average gaze position
                    avgGaze = self.avgPosition(left_pupil, right_pupil)
                    self.eyeData[self.current_corner].append(avgGaze)

        # when all corners have been calibrated, calculate the coefficients
        if self.current_corner == len(self.corners):
            # clear screen
            for widget in self.app.root.winfo_children():
                widget.destroy()
            # TODO: calculating coefficients

            # Display message that calibrating/complete calibration
            self.window.attributes("-fullscreen", False)
            self.window.geometry("800x600")
            ttk.Label(self.app.root, text="Calibration complete").pack(pady=20)

    def avgPosition(self, leftEye, rightEye):
        return [(leftEye[0] + rightEye[0]) / 2, (leftEye[1] + rightEye[1]) / 2]
