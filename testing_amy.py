import cv2
import pyautogui
import numpy as np


class MouseController:
    def __init__(self, gaze, webcam, xcoef, ycoef):
        # initialize gaze tracking
        self.gaze = gaze
        self.webcam = webcam

        # receive coefficients
        self.xcoef = xcoef
        self.ycoef = ycoef

    def runTracking(self, gaze, webcam):
        width = pyautogui.size()[0]
        height = pyautogui.size()[1]
        cellWidth = 30
        cellHeight = 30
        gridWidth = width // cellWidth
        gridHeight = height // cellHeight
        xpositions = []
        ypositions = []
        avg_frames = 5  # Number of frames to average over

        # low pass filter
        controlMouse = True
        updateNow = 0
        while controlMouse:
            # We get a new frame from the webcam
            _, frame = webcam.read()

            # We send this frame to GazeTracking to analyze it
            gaze.refresh(frame)

            left_pupil = gaze.pupil_left_coords()
            right_pupil = gaze.pupil_right_coords()
            if left_pupil and right_pupil:
                eyegaze = [
                    (left_pupil[0] + right_pupil[0]) / 2,
                    (left_pupil[1] + right_pupil[1]) / 2,
                ]
                smoothedavg = self.smooth_eye_position(
                    eyegaze, xpositions, ypositions, avg_frames
                )
                if updateNow > 1:

                    xPixel = (
                        np.clip(
                            int(
                                self.xcoef[0] * smoothedavg[0] ** 2
                                + self.xcoef[1] * smoothedavg[0]
                                + self.xcoef[2]
                            ),
                            0,
                            gridWidth - 1,
                        )
                        * cellWidth
                        + cellWidth / 2
                    )
                    yPixel = (
                        np.clip(
                            int(
                                self.ycoef[0] * smoothedavg[1] ** 2
                                + self.ycoef[1] * smoothedavg[1]
                                + self.ycoef[2]
                            ),
                            0,
                            gridHeight - 1,
                        )
                        * cellHeight
                        + cellWidth / 2
                    )

                    pyautogui.moveTo(xPixel, yPixel)
                    updateNow = 0
            updateNow += 1

        webcam.release()
        cv2.destroyAllWindows()

    def smooth_eye_position(self, new_position, xlist, ylist, frameAvg):
        xlist.append(new_position[0])
        if len(xlist) > frameAvg:
            xlist.pop(0)
        ylist.append(new_position[1])
        if len(ylist) > frameAvg:
            ylist.pop(0)
        return [np.mean(xlist), np.mean(ylist)]
