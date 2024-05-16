# Import essential libraries 
import requests 
import cv2
import numpy as np 
import imutils
import time

# Replace the below URL with your own. Make sure to add "/shot.jpg" at last. 
url = "http://192.168.178.232:8080/shot.jpg"

# While loop to continuously fetching data from the Url 
while True:
	start = time.time()
	points = list()
	img_resp = requests.get(url) 
	img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8) 
	img = cv2.imdecode(img_arr, -1)
	img = imutils.resize(img, width=1000, height=1800) 
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

	lowerRed = np.array([5,95,95])
	upperRed = np.array([10,255,255])
	mask = cv2.inRange(hsv, lowerRed, upperRed)
	contour, hei = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

	for c in contour:
		area = cv2.contourArea(c)
		if area > 10:
			(x,y),radius = cv2.minEnclosingCircle(c)
			center = (int(x),int(y))
			points.append(center)
			if (time.time() - start) < 2:
				point = max(set(points), key = points.count)
				print(point)
				start = time.time()
			radius = int(radius)
			cv2.circle(img,center,radius,(0,255,0),2)

	cv2.imshow("cam", img) 

	# Press Esc key to exit 
	if cv2.waitKey(1) == 27: 
		break


cv2.destroyAllWindows() 
