# mlh-project

# Description
This is a simple eye controlled mouse. It takes input from the webcam, calculates the pupil location on the webcam frame and converts it using quadratic equations to pixels on the screen. 

## Features
1. Simple setup and calibration:
    Calibration takes less than a minute. Center your face in front of the computer screen and hold your head still. Look at a series of nine dots for 2 seconds each. Your eye positions will then be mapped to the pixels on the screen. Then start playing! 

2. Easy to use GUI:
    The GUI provides simple instructions to calibrate your controller. 

3. Helper functions to Play With: 
    Helper functions are provided that you can use a basis for improving accuracy on webpages. It finds the clickable elements on the webpage and weights the mouse location towards the clickable elements. 

## How to Use

Calibration
1. The first dot will be red. 
2. As soon as you press space (do not hold), the dot will turn yellow signaling that it is measuring. 
3. After 2 seconds, if enough data was collected the dot will turn green and the next dot to focus on will turn red. 
4. Once all data has been collected successfully the interface will close and you will now be able to move your mouse with your eyes. 
5. If the lighting is not good enough or the wewbcam is not working properly then the application will stop early. 

Stop Mouse Control
1. To stop the mouse controlled, cover your camera or look away from the screen. You can then stop the program. 

## Building the System

Gaze Tracking

We implemented our own gaze tracking methods using haar cascades. This was a simple and fast algorithm for tracking eyes. However we did not have the time to optimize the algorithm for accuracy so we used the Open Source GazeTracking library https://github.com/antoinelame/GazeTracking.git that uses dlib to map the face and track the pupils. 

Gaze to Mouse Mapping

Gaze to mouse mapping is based on a simple calibration setup. The user is asked to look at several dots on the screen for several seconds. The position of their eye on the webcam frame was recorded and the the dot locations were inputed into a mapping function. 

We tested several different methods of mapping gaze to mouse, including a linear regression model and polynomial regression model. However, these were too slow for real time applications. We ended up separating the x and y inputs and mapping them to the x and y pixels independently using two quadratic equations. This allowed for fast mapping and had high enough accuracy to follow the users gaze as long as they kept their head steady. 

Improving accuracy 

We applied a moving average function to smooth out the mouses movements with a frame of three. We found that this smoothed the mouse data without causing a significant lag. Additionally, we split the screen into a grid of 20x20 pixels. This decreased the resolution the eye data had to map to, thus reducing the jitter motion of the mouse. We found the 20-40 cell blocks improved mouse movement. 

Due to the limits of using webcam the mouse has significant jitter making it hard to hover and click over any element on the screen. To overcome this we tried snapping the mouse toward elements on the screen that the user may be interested in. We did this by opening a webpage, using selenium to extract clickable elements (buttons, links and search bars) and calculating the distance of the current x/y pixel estimate to each element on screen. If they element is within 100 pixels it will be weighted toward that element. This decreased jitter near clickable elements and increasing the likelihood of successfully clicking an item. More testing needs to be done to improve this functionality, and thus it was not included in the main application. It was however included as a separate file called unintegrated_helperfunctions. 

User Interface

The user interface was designed to be clean, simple and easy to use. 

## Future Directions
This project is a basis for a free, simple gaze controlled mouse. Future directions of the project could include:

1. Apply filtering to decrease jitter
2. Improve accracy by snapping the mouse toward elements of importance on the screen
3. Use a more sophisticated mapping function (ml models, cnn, etc)
4. Track head position and rotation and account for head movement in the mapping function so that the user can move their head without affecting the controller. 
5. Integrate a virtual keyboard
6. Setup the system so it launches automatically and calibrates without requiring any physical input (currently calibration requires pressing the space bar)

## Inspiration 
For people with motor disorders, using a mouse can be difficult. Eye tracking technology makes using computers more accessible. However the technology can be expensive, or require extensive calibration. We wanted to make an easy to setup and use eye controlled mouse that could be calibrated in a couple minutes, and have enough accuracy to be useable.

## File Locations
1. testing.py: contains the working code for calibrating the controller and using the eye controlled mouse.
2. app.py is the starting code for the improved user interface.
3. calibrate_frame.py: contains the class to the calibrate using the improved interface.
4. mouse_controller.py: contains the class to move the mouse using the calibration coefficients. 
5. unintegrated_helperfunctions.py: contains commented out methods for weighting the mouse location toward clickable elements on the screen. 

## Installation

Clone this project:

```shell
git clone https://github.com/afan104/mlh-project.git


