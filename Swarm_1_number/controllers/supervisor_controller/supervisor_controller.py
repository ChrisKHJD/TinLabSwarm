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
    
    otherrobotsPOT =  sum(0.05/x - 0.1/x**2 for x in robotdistances) # in formation
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

def get_random_operation():
    """Returns 'add' or 'subtract' based on a random value."""
    return 'add' if random() < 0.5 else 'subtract'

def get_random_items_to_modify():
    """Returns a list of items to modify and their operations."""
    items_to_modify = []
    for i in range(2): # Loop through the first two items
        operation = get_random_operation()
        items_to_modify.append((i, operation))
    return items_to_modify

def modify_position(position, items_to_modify):
    """Modifies the items in the position list based on the items_to_modify list."""
    for item, operation in items_to_modify:
        if operation == 'add':
            position[item] += 0.02
        else:
            position[item] -= 0.02
    return position

def process_robot(robot):
    """Processes a robot by modifying its position."""
    initPotential = getPotential(robot)
    translationField = robot.getField("translation")
    OldPos = translationField.getSFVec3f()
    NewPos = OldPos.copy()
    
    bestPotential = initPotential
    bestPos = NewPos.copy()
    
    for _ in range(3): # Perform x random steps, more steps, better routes less stuck, more computing power
        operation = get_random_operation()
        items_to_modify = get_random_items_to_modify()
        NewPos = modify_position(NewPos, items_to_modify)
        
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

# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())
FirstNumberToShow = 2
numbers = [
[1,0,1,1,1,1,1],#0
[0,0,0,0,1,0,1],#1
[1,1,1,0,1,1,0],#2
[1,1,1,0,1,0,1],#3
[0,1,0,1,1,0,1],#4
[1,1,1,1,0,0,1],#5
[1,1,1,1,0,1,1],#6
[1,0,0,0,1,0,1],#7
[1,1,1,1,1,1,1],#8
[1,1,1,1,1,0,1],#9
]

#fill robots
robots = []
for i in range(7):
    robots.append(supervisor.getFromDef('ROBOT' + str(i)))
    
obstacles = []
for i in range(2):
    obstacles.append(supervisor.getFromDef('OBSTACLE' + str(i)))
    
objectives = []
for i in range(1):
    objectives.append(supervisor.getFromDef('OBJECTIVE' + str(i)))
    
digitStripes = []
for number in range(1):
    digitStripes.append(supervisor.getFromDef('DigitTop' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitMid' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitBottom' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitTopLeft' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitTopRight' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitBottomLeft' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitBottomRight' + str(number)))

##setup digit stripes dynamically put stripes in right positions
digit_cube_size = 3
#digit_space_between = 0.85
digit_z = 0.01
arena_size = supervisor.getFromDef('ARENA').getField('floorSize').getSFVec2f()
digitbeginpositions = [
    [(arena_size[0]/2),(arena_size[1]/2)]
]

for i in range(0,1):
    digitStripes[0+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0]+digit_cube_size,digitbeginpositions[i][1],digit_z])
    digitStripes[1+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0],digitbeginpositions[i][1],digit_z])
    digitStripes[2+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0]-digit_cube_size,digitbeginpositions[i][1],digit_z])
    digitStripes[3+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0]+(0.5*digit_cube_size),digitbeginpositions[i][1]+(0.5*digit_cube_size),digit_z])
    digitStripes[4+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0]+(0.5*digit_cube_size),digitbeginpositions[i][1]-(0.5*digit_cube_size),digit_z])
    digitStripes[5+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0]-(0.5*digit_cube_size),digitbeginpositions[i][1]+(0.5*digit_cube_size),digit_z])
    digitStripes[6+i*7].getField("translation").setSFVec3f([digitbeginpositions[i][0]-(0.5*digit_cube_size),digitbeginpositions[i][1]-(0.5*digit_cube_size),digit_z])
    

#put robots at random positions
for robot in robots:
    InitialPos = robot.getField("translation")
    if(robot.getField("name").getSFString() == "robo0"):
        NewPos = [
            13.4,
            5.4,
            0.1
        ]
    else:
        NewPos = [
            arena_size[0] * random(), 
            arena_size[1] * random(),  
            0.1
        ]
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
    
#put obstacles at random positions    
for obstacle in obstacles:
    InitialPos = obstacle.getField("translation")
    NewPos=[
        arena_size[0] * random(),
        arena_size[1] * random(),
        0.1
    ]
    # InitialPos.setSFVec3f(NewPos)

# each index is for the robot with the same index in robot, each number is the index for the digitstripe
goalAssignments = [-1] * len(robots)
SERVER_ADDRESS = '145.137.54.68'  # Change this to your server's IP address
SERVER_PORT = 8000  # Change this to the port your server is listening on
firstloop = True
stepcounter = 0
sendcounter = 0

x_mapping = 960
y_mapping = 540

amount_of_fysical_robots = 2

# Main loop:
while supervisor.step(timestep) != -1:
    if firstloop:
        assignStripesToRobots()
        firstloop=False
        setup_connection(SERVER_ADDRESS, SERVER_PORT)
        
    for robot in robots:
        process_robot(robot)
    
    if sendcounter == 20:
        data = {'type': 'webots'}
        for i in range(0,amount_of_fysical_robots):
            position = robots[i].getField("translation").getSFVec3f()
            
            new_x = (position[0]) / arena_size[0] * x_mapping
            new_y = (position[1]) / arena_size[1] * y_mapping
            if new_x > (0.95*x_mapping):
                new_x = 0.95*x_mapping
            if new_x < (0.05*x_mapping):
                new_x = 0.05*x_mapping
            if new_y > (0.95*y_mapping):
                new_y = 0.95*y_mapping
            if new_y < (0.05*y_mapping):
                new_y = 0.05*y_mapping
            
            robot_position = {"x": new_x, "y": new_y}
            data[i] = robot_position
            #TODO Als de positie buiten het speelveld is, assign het uiterste van het speelveld
            
        
        print('sendjson: ', data)
        send_json_data(data)
        sendcounter = 0
    else:
        sendcounter += 1
    
    if stepcounter == 300:
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