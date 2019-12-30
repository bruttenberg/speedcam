"""Python Speed Camera

   Uses a camera connected to a raspberry Pi to track and record the speed of vehicles on a road.
   author: Brian Ruttenberg
   email: ruttenberg@gmail.com

   This code is heavily inspired by https://github.com/gregtinkers/carspeed.py. While this version uses a different
   tracking system/method, and thus is not a direct extension of that code, it does heavily borrow from the computer
   vision methods in the original carspeed.py
"""

import datetime
import math

import cv2

from simple_tracker import SimpleTracker
from webcam import Webcam


# place a prompt on the displayed image
def prompt_on_image(txt):
    global image
    cv2.putText(image, txt, (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)


# calculate speed from pixels and time
def get_speed(pixels, ftperpixel, secs):
    if secs > 0.0:
        return ((pixels * ftperpixel)/ secs) * 0.681818  
    else:
        return 0.0

 
# calculate elapsed seconds
def secs_diff(endTime, begTime):
    diff = (endTime - begTime).total_seconds()
    return diff

# record speed in .csv format
def record_speed(res):
    global csvfileout
    f = open(csvfileout, 'a')
    f.write(res+"\n")
    f.close

# mouse callback function for drawing capture area
def draw_rectangle(event,x,y,flags,param):
    global ix,iy,fx,fy,drawing,setup_complete,image, org_image, prompt
 
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix,iy = x,y
 
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            image = org_image.copy()
            prompt_on_image(prompt)
            cv2.rectangle(image, (ix, iy), (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        fx, fy = x, y
        image = org_image.copy()
        prompt_on_image(prompt)
        cv2.rectangle(image, (ix, iy), (fx, fy), (0, 255, 0), 2)


# define some constants

# Distance from the camera to "cars", in meters
# Note depending on the distance of the camera to the road, you might get different speeds depending on the direction
# of the traffic.
DISTANCE_METERS = 13.7

# Minumum speed to record
MIN_KPH = 20

SAVE_CSV = False  # <---- record the results in .csv format in carspeed_(date).csv

THRESHOLD_INTENSITY = 15
MIN_AREA_PIXELS = 175
BLURSIZE_PIXELS = (15, 15)
X_PAD_PERCENT = .05
IMAGEWIDTH = 640
IMAGEHEIGHT = 480
RESOLUTION = [IMAGEWIDTH, IMAGEHEIGHT]
FOV_DEGREES = 78
FPS = 20
SHOW_BOUNDS = True
SHOW_IMAGE = True

# calculate the the width of the image at the distance specified
frame_width_meters = 2 * (math.tan(math.radians(FOV_DEGREES * 0.5)) * DISTANCE_METERS)
# Meters per pixel
mpp = frame_width_meters / float(IMAGEWIDTH)
print("Image width in feet {} at {} from camera".format("%.0f" % frame_width_meters, "%.0f" % DISTANCE_METERS))

# -- other values used in program
base_image = None
abs_chg = 0
mph = 0
secs = 0.0
ix, iy = -1, -1
fx, fy = -1, -1
drawing = False
setup_complete = False
tracking = False
text_on_image = 'No cars'
prompt = ''

webcam = Webcam("calibrated.avi", FPS)

# create an image window and place it in the upper left corner of the screen
cv2.namedWindow("Speed Camera")
cv2.moveWindow("Speed Camera", 10, 40)

# call the draw_rectangle routines when the mouse is used
cv2.setMouseCallback('Speed Camera',draw_rectangle)
 
# grab a reference image to use for drawing the monitored area's boundry
image = webcam.get_image()
org_image = image.copy()

if SAVE_CSV:
    csvfileout = "carspeed_{}.cvs".format(datetime.datetime.now().strftime("%Y%m%d_%H%M"))
    record_speed('Date,Day,Time,Speed,Image')
else:
    csvfileout = ''

prompt = "Define the monitored area - press 'c' to continue" 
prompt_on_image(prompt)
 
# wait while the user draws the monitored area's boundry
while not setup_complete:
    cv2.imshow("Speed Camera",image)
 
    #wait for for c to be pressed  
    key = cv2.waitKey(1) & 0xFF
  
    # if the `c` key is pressed, break from the loop
    if key == ord("c"):
        break

# the monitored area is defined, time to move on
prompt = "Press 'q' to quit" 
 
# since the monitored area's bounding box could be drawn starting 
# from any corner, normalize the coordinates
 
if fx > ix:
    upper_left_x = ix
    lower_right_x = fx
else:
    upper_left_x = fx
    lower_right_x = ix
 
if fy > iy:
    upper_left_y = iy
    lower_right_y = fy
else:
    upper_left_y = fy
    lower_right_y = iy
     
monitored_width = lower_right_x - upper_left_x
monitored_height = lower_right_y - upper_left_y

print("Monitored area:")
print(" upper_left_x {}".format(upper_left_x))
print(" upper_left_y {}".format(upper_left_y))
print(" lower_right_x {}".format(lower_right_x))
print(" lower_right_y {}".format(lower_right_y))
print(" monitored_width {}".format(monitored_width))
print(" monitored_height {}".format(monitored_height))
print(" monitored_area {}".format(monitored_width * monitored_height))

tracker = SimpleTracker(5)

last_time_stamp = datetime.datetime.now()
base_image = None
base_image_time = last_time_stamp
while True:
    # initialize the timestamp
    time_stamp = datetime.datetime.now()

    image = webcam.get_image()

    # crop area defined by [y1:y2,x1:x2]
    gray = image[upper_left_y:lower_right_y, upper_left_x:lower_right_x]

    # convert the frame to grayscale, and blur it
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, BLURSIZE_PIXELS, 0)

    # if the base image has not been defined, initialize it
    if base_image is None or (
            secs_diff(time_stamp, base_image_time) > 60 and not tracker.get_active_tracks()):
        base_image = gray.copy().astype("float")
        base_image_time = time_stamp
        cv2.imshow("Speed Camera", image)

    # compute the absolute difference between the current image and
    # base image and then turn everything lighter gray than THRESHOLD into
    # white
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(base_image))
    thresh = cv2.threshold(frameDelta, THRESHOLD_INTENSITY, 255, cv2.THRESH_BINARY)[1]

    # dilate the thresholded image to fill in any holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # cv2.imshow("Speed Camera", thresh)
    # key = cv2.waitKey(0)

    # Find objects
    observations = []
    directions = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area > MIN_AREA_PIXELS:
            moments = cv2.moments(c)
            cx = int(moments['m10'] / moments['m00'])
            cx_meters = cx * mpp
            observations.append(cx_meters)
            directions.append(1 if cx < monitored_width / 2 else -1)

    tracker.update_tracks(observations, directions, secs_diff(time_stamp, last_time_stamp))
    tracker.print_tracks()

    last_time_stamp = time_stamp

# cleanup the camera and close any open windows
cv2.destroyAllWindows()
