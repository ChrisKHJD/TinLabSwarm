# Import essential libraries
import requests
import cv2
import numpy as np
import imutils
import time

# Replace the below URL with your own. Make sure to add "/shot.jpg" at last.
url = "http://145.137.119.246:8080//shot.jpg"

frame_counter = 0
start_time = time.time()
# While loop to continuously fetching data from the Url
while True:
	img_resp = requests.get(url)
	print("succes")
	img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
	img = cv2.imdecode(img_arr, -1)
	img = imutils.resize(img, width=1000, height=1800)
	cv2.imshow("Android_cam", img)

	# Press Esc key to exit
	if cv2.waitKey(1) == 27:
		break

	frame_counter += 1
	elapsed_time = time.time() - start_time

	# Print frames processed per second every second
	if elapsed_time >= 1.0:
		print(f"Frames processed in the last second: {frame_counter}")
		frame_counter = 0
		start_time = time.time()

cv2.destroyAllWindows()
