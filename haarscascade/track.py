import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier("haarscascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("haarscascade_eye.xml")

# blob detection algorithm
detector_params = cv2.SimpleBlobDetector_Params()
detector_params.filterByArea = True  # max area of pupil won't be greater than 1500 px
detector_params.maxArea = 1500
detector = cv2.SimpleBlobDetector_create(detector_params)


def detect_eyes(img, classifier):
    # convert image to grayscale
    gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #
    eyes = classifier.detectMultiScale(gray_frame, 1.3, 5)  # detect eyes
    width = np.size(img, 1)  # get face frame width
    height = np.size(img, 0)  # get face frame height
    left_eye, right_eye = None, None  # initialize in case none detected
    for x, y, w, h in eyes:
        if y > height / 2:  # pass if the eye is detected at the bottom half of face
            pass
        eyecenter = x + w / 2  # get the eye center
        # determine left and right eyes
        if eyecenter < width * 0.5:
            left_eye = img[y : y + h, x : x + w]
        else:
            right_eye = img[y : y + h, x : x + w]
    return left_eye, right_eye


def detect_faces(img, classifier):
    gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    coords = classifier.detectMultiScale(gray_frame, 1.3, 5)
    # if multiple faces detected, choose largest one as face
    if len(coords) > 1:
        biggest = (0, 0, 0, 0)
        for i in coords:
            if i[3] > biggest[3]:
                biggest = i
        biggest = np.array([i], np.int32)
    elif len(coords) == 1:
        biggest = coords
    else:
        return None
    for x, y, w, h in biggest:
        frame = img[y : y + h, x : x + w]
    return frame


def cut_eyebrows(img):
    height, width = img.shape[:2]
    eyebrow_h = int(height / 4)
    img = img[eyebrow_h:height, 0:width]  # cut eyebrows out (15 px)
    return img


def blob_process(img, threshold, detector):
    gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(gray_frame, threshold, 255, cv2.THRESH_BINARY)
    # transformations to reduce noise:
    img = cv2.erode(img, None, iterations=2)  # 1
    img = cv2.dilate(img, None, iterations=4)  # 2
    img = cv2.medianBlur(img, 5)  # 3

    keypoints = detector.detect(img)
    return keypoints


def nothing(x):
    pass


def main():
    # camera capture
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("image")
    cv2.createTrackbar("threshold", "image", 0, 255, nothing)
    while True:
        # take in frames
        _, frame = cap.read()
        # extract face location
        face_frame = detect_faces(frame, face_cascade)
        # if face extracted, find eyes
        if face_frame is not None:
            eyes = detect_eyes(face_frame, eye_cascade)
            # if eye(s) extracted, find pupils
            for eye in eyes:
                if eye is not None:
                    threshold = cv2.getTrackbarPos(
                        "threshold", "image"
                    )  # moving threshold
                    eye = cut_eyebrows(eye)
                    keypoints = blob_process(eye, threshold, detector)
                    eye = cv2.drawKeypoints(
                        eye,
                        keypoints,
                        eye,
                        (0, 0, 255),
                        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
                    )
                    cv2.imshow("my image", face_frame)  # ???
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                    cap.release()
                    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
