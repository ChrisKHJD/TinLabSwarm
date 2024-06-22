import cv2
import imutils
import time


# Function to list all available webcams
def list_available_cameras():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(index)
        cap.release()
        index += 1
    return arr


# Print available webcams
available_cameras = list_available_cameras()
print("Available webcams:", available_cameras)

# Initialize the webcam (using the first available camera)
cap = cv2.VideoCapture(available_cameras[2])

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Capture the first frame to print its dimensions
ret, frame = cap.read()
if not ret:
    print("Error: Could not read frame.")
    cap.release()
    exit()

# Print the dimensions of the first frame
print("Initial frame dimensions (height, width, channels):", frame.shape)

frame_counter = 0
start_time = time.time()
# While loop to continuously capture frames from the webcam
while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    frame = imutils.resize(frame, width=1080, height=1920)
    cv2.imshow("Webcam", frame)

    frame_counter += 1

    # Calculate elapsed time
    elapsed_time = time.time() - start_time

    # Print frames processed per second every second
    if elapsed_time >= 1.0:
        print(f"Frames processed in the last second: {frame_counter}")
        frame_counter = 0
        start_time = time.time()

    # Press Esc key to exit
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()

cap.release()
cv2.destroyAllWindows()
