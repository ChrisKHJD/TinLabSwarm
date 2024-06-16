"""supervisor_controller controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Supervisor
from random import random
from math import sqrt, pow, dist
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
import socket
import json
import time
from datetime import datetime

def Distance(V1,V2):
    #trivial cartesian distance in 3D
    return(dist(V1.getSFVec3f(),V2.getSFVec3f()))
    
def DistancesToOtherRobots(CurrentRobot,OtherRobots):
    #calculates an array of distances between current robot and the others
    distances=[];
    for each in OtherRobots:
        distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
    return(distances)
    
def DistancesToOtherObstacles(CurrentRobot):
    distances=[];
    for each in obstacles:
        distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
    return(distances)
    
def DistancesToOtherObjectives(CurrentRobot):
    distances=[];
    for each in objectives:
        distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
    return(distances)

def DistancesToDigits(CurrentRobot):
    distances=[];
    i=0
    for each in digitStripes:
        if numbers[FirstNumberToShow][i] == 1:
            distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
        i+=1
    return(distances)
    
def GetOtherRobots(CurrentRobot): 
    OtherRobots=robots.copy()
    OtherRobots.remove(CurrentRobot)
    return(OtherRobots) 
    
def getPotential(robot):
    otherRobots = GetOtherRobots(robot)
    robotdistances = DistancesToOtherRobots(robot,otherRobots)
    obstacledistances = DistancesToOtherObstacles(robot)
    # objectivedistances = DistancesToOtherObjectives(robot)
    digitdistances = DistancesToDigits(robot)
    
    otherrobotsPOT =  sum(0.04/x - 0.12/x**2 for x in robotdistances) # in formation
    # otherrobotsPOT =  sum(0.05/x - 0.1/x**2 for x in robotdistances) # in formation
    # otherrobotsPOT = sum(-0.05/x  for x in robotdistances) # not in formation
    #als de buiten de range zijn van de obstacle moet er geen kracht meer op werken
    obstaclesPOT = sum(-0.03/x if x <= 1 else 0 for x in obstacledistances)
    
    digitPOT = 0
    for i in range(numbers[FirstNumberToShow].count(1)):
        robotindex = robots.index(robot)
        digitobjindex = goalAssignments[robotindex] #index of digit it needs to go
        # print(robot.getField("name").getSFString(),'digitobjindex', digitobjindex)
        if i == digitobjindex:
            digitPOT += 1/digitdistances[i] 
            # print(robot.getField("name").getSFString(),'target', 1/digitdistances[i] )
        else:
            if digitdistances[i] <= 2: # if robot is far enough from digit don't go further
                digitPOT += -0.01/digitdistances[i]
                # print(robot.getField("name").getSFString(),'notarget', -0.01/digitdistances[i] )
        
        
    # targetPOT = sum(4/x - 2/x**2 for x in objectivedistances)
    totalPOT = otherrobotsPOT+obstaclesPOT+digitPOT
    # print(robot.getField("name").getSFString(), totalPOT)
    return totalPOT

def get_random_items_to_modify():
    """Returns a list of items to modify and their operations."""
    items_to_modify = []
    for i in range(2): # Loop through the first two items
        operation = random() < 0.5
        items_to_modify.append((i, operation))
    return items_to_modify

def modify_position(position):
    """Modifies the items in the position list based on the items_to_modify list."""
    for i in range(2): # Loop through the first two items
        if random() < 0.5:
            position[i] += ROBOT_STEP_VALUE
        else:
            position[i] -= ROBOT_STEP_VALUE
    return position

def process_robot(robot):
    """Processes a robot by modifying its position."""
    initPotential = getPotential(robot)
    translationField = robot.getField("translation")
    OldPos = translationField.getSFVec3f()
    NewPos = OldPos.copy()
    
    bestPotential = initPotential
    bestPos = NewPos.copy()
    
    for _ in range(5): # Perform x random steps, more steps, better routes less stuck, more computing power
        NewPos = modify_position(NewPos)
        
        translationField.setSFVec3f(NewPos)
        newPotential = getPotential(robot)
        
        if newPotential > bestPotential:
            bestPotential = newPotential
            bestPos = NewPos.copy()
    
    # Move to the position with the highest potential
    translationField.setSFVec3f(bestPos)

def assignStripesToRobots():
    # Initialize an empty array with a single row
    matrix = []  # Specify dtype=object to allow for lists or tuples
    for robot in robots:
        distances_to_digits = DistancesToDigits(robot)
        matrix.append(distances_to_digits)
    
    cost = np.array(matrix)

    # Use linear_sum_assignment to find the optimal assignment
    for i in range(len(goalAssignments)):
        goalAssignments[i] = -1

    row_ind, col_ind = linear_sum_assignment(cost)
    for i in range(numbers[FirstNumberToShow].count(1)): #  is the amount of objectives should be amount
        print('robotindex',row_ind[i],'is going to digitIndex',col_ind[i])
        goalAssignments[row_ind[i]] = col_ind[i]
    
    # Calculate the total cost of the optimal assignment
    total = cost[row_ind, col_ind]
    # print(total)
    total_cost = total.sum()
    
    print("Total cost of the optimal assignment:", total_cost)
    # print('after assignments', goalAssignments)

client_socket = None;

def setup_connection(server_address, server_port):
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         # Connect to the server
        client_socket.connect((server_address, server_port))
    except Exception as e:
        print("No connection was made:", e)
        
def send_json_data(data):
    global client_socket
    try:
        # Convert data to JSON format
        json_data = json.dumps(data)

        # Send JSON data to the server
        client_socket.sendall(json_data.encode())
    except Exception as e:
        print("Error sending data:", e)

# Constants
ROBOT_STEP_VALUE = 0.04
TIMESTEPS_BETWEEN_DATA_SENDING = 5
TIMESTEPS_BETWEEN_NUMBER_CHANGE = 150
SERVER_ADDRESS = '145.24.243.16'  # Change this to your server's IP address
SERVER_PORT = 8000  # Change this to the port your server is listening on
FirstNumberToShow = 2
DIGIT_CUBE_SIZE = 3
DIGIT_Z = 0.01
X_MAPPING = 960
Y_MAPPING = 540
AMOUNT_OF_PHYSICAL_ROBOTS = 2

# Numbers pattern
numbers = [
    [1, 0, 1, 1, 1, 1, 1],  # 0
    [0, 0, 0, 0, 1, 0, 1],  # 1
    [1, 1, 1, 0, 1, 1, 0],  # 2
    [1, 1, 1, 0, 1, 0, 1],  # 3
    [0, 1, 0, 1, 1, 0, 1],  # 4
    [1, 1, 1, 1, 0, 0, 1],  # 5
    [1, 1, 1, 1, 0, 1, 1],  # 6
    [1, 0, 0, 0, 1, 0, 1],  # 7
    [1, 1, 1, 1, 1, 1, 1],  # 8
    [1, 1, 1, 1, 1, 0, 1],  # 9
]

# Create the Supervisor instance
supervisor = Supervisor()
timestep = int(supervisor.getBasicTimeStep())

# Initialize robots, obstacles, and objectives
robots = [supervisor.getFromDef(f'ROBOT{i}') for i in range(7)]
obstacles = [supervisor.getFromDef(f'OBSTACLE{i}') for i in range(2)]
objectives = [supervisor.getFromDef(f'OBJECTIVE{i}') for i in range(1)]

# Initialize digit stripes
digitStripes = []
for number in range(1):
    digitStripes.extend([
        supervisor.getFromDef(f'DigitTop{number}'),
        supervisor.getFromDef(f'DigitMid{number}'),
        supervisor.getFromDef(f'DigitBottom{number}'),
        supervisor.getFromDef(f'DigitTopLeft{number}'),
        supervisor.getFromDef(f'DigitTopRight{number}'),
        supervisor.getFromDef(f'DigitBottomLeft{number}'),
        supervisor.getFromDef(f'DigitBottomRight{number}')
    ])

# Set up digit stripes dynamically
arena_size = supervisor.getFromDef('ARENA').getField('floorSize').getSFVec2f()
digit_begin_positions = [(arena_size[0] / 2, arena_size[1] / 2)]

for i in range(1):
    digitStripes[0 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0] + DIGIT_CUBE_SIZE, digit_begin_positions[i][1], DIGIT_Z])
    digitStripes[1 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0], digit_begin_positions[i][1], DIGIT_Z])
    digitStripes[2 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0] - DIGIT_CUBE_SIZE, digit_begin_positions[i][1], DIGIT_Z])
    digitStripes[3 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0] + (0.5 * DIGIT_CUBE_SIZE), digit_begin_positions[i][1] + (0.5 * DIGIT_CUBE_SIZE), DIGIT_Z])
    digitStripes[4 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0] + (0.5 * DIGIT_CUBE_SIZE), digit_begin_positions[i][1] - (0.5 * DIGIT_CUBE_SIZE), DIGIT_Z])
    digitStripes[5 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0] - (0.5 * DIGIT_CUBE_SIZE), digit_begin_positions[i][1] + (0.5 * DIGIT_CUBE_SIZE), DIGIT_Z])
    digitStripes[6 + i * 7].getField("translation").setSFVec3f([digit_begin_positions[i][0] - (0.5 * DIGIT_CUBE_SIZE), digit_begin_positions[i][1] - (0.5 * DIGIT_CUBE_SIZE), DIGIT_Z])

# Put robots at random positions
for robot in robots:
    InitialPos = robot.getField("translation")
    if robot.getField("name").getSFString() == "robo0":
        NewPos = [16.8, 10, 0.1]
    elif robot.getField("name").getSFString() == "robo1":
        NewPos = [16.8, 1, 0.1]
    else:
        NewPos = [arena_size[0] * random(), arena_size[1] * random(), 0.1]
    InitialPos.setSFVec3f(NewPos)

#this is for initial position robot for world file
# robocount = 1
# for robot in robots:
    # InitialPos = robot.getField("translation")
    # NewPos = [
        # (1/8)* robocount * arena_size[0], 
        # (arena_size[1]/2),  
        # 0.1
    # ]
    # robocount += 1
    # InitialPos.setSFVec3f(NewPos)

# Put obstacles at random positions
for obstacle in obstacles:
    InitialPos = obstacle.getField("translation")
    NewPos = [arena_size[0] * random(), arena_size[1] * random(), 0.1]
    #InitialPos.setSFVec3f(NewPos)

# Initial configuration
goalAssignments = [-1] * len(robots)
firstloop = True
stepcounter = 0
sendcounter = 0

# Main loop:
while supervisor.step(timestep) != -1:
    if firstloop:
        assignStripesToRobots()
        firstloop=False
        setup_connection(SERVER_ADDRESS, SERVER_PORT)
        
    for robot in robots:
        process_robot(robot)
    
    if sendcounter == TIMESTEPS_BETWEEN_DATA_SENDING:
        data = {'type': 'webots'}
        for i in range(0,AMOUNT_OF_PHYSICAL_ROBOTS):
            position = robots[i].getField("translation").getSFVec3f()
            
            new_x = (position[0]) / arena_size[0] * X_MAPPING
            new_y = (position[1]) / arena_size[1] * Y_MAPPING
            if new_x > (0.95*X_MAPPING):
                new_x = 0.95*X_MAPPING
            if new_x < (0.05*X_MAPPING):
                new_x = 0.05*X_MAPPING
            if new_y > (0.95*Y_MAPPING):
                new_y = 0.95*Y_MAPPING
            if new_y < (0.05*Y_MAPPING):
                new_y = 0.05*Y_MAPPING
            
            #flip x axis
            if(new_y > (Y_MAPPING/2)):
                new_y = (Y_MAPPING/2) - (new_y - (Y_MAPPING/2))
            else:
                new_y = (Y_MAPPING/2) + ((Y_MAPPING/2) - new_y)
            
            robot_position = {"x": new_x, "y": new_y}
            data[i] = robot_position
            
        
        print('sendjson: ', data)
        send_json_data(data)
        sendcounter = 0
    else:
        sendcounter += 1
    
    if stepcounter == TIMESTEPS_BETWEEN_NUMBER_CHANGE:
        if FirstNumberToShow < 9:
            FirstNumberToShow += 1
        else:
            FirstNumberToShow = 0
        
        assignStripesToRobots()
        stepcounter = 0
        print(FirstNumberToShow)
    stepcounter += 1
    
# Enter here exit cleanup code.
# Close the connection
client_socket.close()