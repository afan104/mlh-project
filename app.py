import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.calibrate_frame import CalibrateScreen


class EyeTrackingApp(tk.Tk):
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.root.title("Eye Tracking App")

        # Define styles
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=("Helvetica", 24, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Helvetica", 14))

        # Initialize the home screen
        self.init_home_screen()

        # Keybinds
        self.root.bind("<space>", self.calibration_screen)

    def init_home_screen(self):
        # Add labels to the home screen
        ttk.Label(self.root, text="Welcome to Eye Tracking", style="Title.TLabel").pack(
            pady=20
        )
        ttk.Label(self.root, text="Start Calibration", style="Subtitle.TLabel").pack(
            pady=(100, 5)
        )
        ttk.Label(
            self.root, text="Press space bar to start.", style="Subtitle.TLabel"
        ).pack(pady=5)

    def calibration_screen(self, event=None):
        # Clear the screen
        for widget in self.root.winfo_children():
            widget.destroy()
        # Instantiate the Calibrate class
        self.calibrate_frame = CalibrateScreen(self.root, self)

if __name__ == "__main__":
    root = tk.Tk()
    app = EyeTrackingApp(root)
    root.mainloop()
