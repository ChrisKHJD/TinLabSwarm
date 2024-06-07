import socket
import threading
import json
import math
import time
from datetime import datetime
from time import sleep

webots = {
    0: (50, 50),  # Target position for robot_1
}

chariots = {
    0: (0, 50, 0),  # Real position and orientation for robot_1
}


# Calculate the angle between two points.
def calculate_angle(x1, y1, x2, y2):
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


# Calculate the smallest difference between two angles.
def angle_difference(angle1, angle2):
    return (angle1 - angle2 + 180) % 360 - 180


# Calculate the Euclidean distance between two points.
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# Generate movement instructions for robot to reach target. test threshold value
def get_instruction(robot_id, target_x, target_y, real_x, real_y, orientation, threshold=0.5):
    instruction = ""

    target_angle = calculate_angle(real_x, real_y, target_x, target_y)
    print("target angle",target_angle)
    angle_diff = angle_difference(target_angle, orientation)
    print("angle dif", angle_diff)

    if distance(real_x, real_y, target_x, target_y) <= threshold:
        instruction = 'stop'
    elif abs(angle_diff) < 5:  # Within 5 degrees, move forward (maybe lower this value)
        instruction = 'move_forward'
    elif angle_diff > 0:
        instruction = 'rotate_right'
    else:
        instruction = 'rotate_left'

    return instruction


def chariot_instructions():
    global chariots

    while True:
        for chariot in chariots:
            #print(chariots[chariot])
            real_x, real_y, orientation = chariots[chariot]
            target_x, target_y = webots[chariot]
            instr = get_instruction(chariot, target_x, target_y, real_x, real_y, orientation)
            print('instruction send:', chariot, instr)

        sleep(3)

print("------------------------------------------------------")
chariot_instructions()
