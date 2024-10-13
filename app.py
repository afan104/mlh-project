import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from calibrate_frame import CalibrateScreen
from mouse_controller import MouseController
import pyautogui
import cv2
from GazeTracking.gaze_tracking import GazeTracking


class EyeTrackingApp(tk.Tk):
    def __init__(self, root, gaze, webcam, theme="morph"):
        self.root = root
        self.gaze = gaze
        self.webcam = webcam
        self.root.geometry("800x600")
        self.root.title("Eye Tracking App")

        self.xcoeff, self.ycoeff = None, None

        # Define styles
        self.style = ttk.Style(theme=theme)
        self.style.configure("Title.TLabel", font=("Helvetica", 24, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Helvetica", 14))
        self.style.configure("Instructions.TLabel", font=("Helvetica", 14, "italic"))
        self.style.configure(
            "BoldInfo.TLabel",
            font=("Helvetica", 24, "bold"),
            background="#d9edf7",
            foreground="#31708f",
            padding=10,
        )
        self.style.configure(
            "ItalicInfo.TLabel",
            font=("Helvetica", 24, "italic"),
            background="#d9edf7",
            foreground="#31708f",
            padding=10,
        )

        # Initialize the home screen
        self.init_home_screen()

        # Keybinds
        self.root.bind("<space>", self.calibration_screen)

    def init_home_screen(self):
        # Add labels to the home screen
        ttk.Label(self.root, text="Welcome to Eye TrackPad", style="Title.TLabel").pack(
            pady=28
        )
        ttk.Label(self.root, text="Start Calibration", style="Subtitle.TLabel").pack(
            pady=(100, 5)
        )
        ttk.Label(
            self.root, text="Press space bar to start.", style="Instructions.TLabel"
        ).pack(pady=5)

    def calibration_screen(self, event=None):
        # Clear the screen
        for widget in self.root.winfo_children():
            widget.destroy()
        # Instantiate the Calibrate class
        CalibrateScreen(self.root, self.gaze, self.webcam, 20, 20, self)


if __name__ == "__main__":
    cellWidth  = 20 
    cellHeight = 20
    screenWidth = pyautogui.size()[0]
    screenHeight = pyautogui.size()[1]

    gaze = GazeTracking()
    webcam = cv2.VideoCapture(0)

    root = tk.Tk()
    app = EyeTrackingApp(root, gaze, webcam)
    root.mainloop()

    # Start tracking
    if app.xcoeff != None and app.ycoeff != None:
        app = MouseController(app.xcoeff, app.ycoeff, gaze, webcam, cellWidth, cellHeight, screenWidth, screenHeight)

    webcam.release()
    cv2.destroyAllWindows()