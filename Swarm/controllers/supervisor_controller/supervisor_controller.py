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
        if i < 7:
            if numbers[FirstNumberToShow][i] == 1:
                distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
        elif i < 14:
            if numbers[SecondNumberToShow][i-7] == 1:
                distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
        elif i < 21:
            if numbers[ThirdNumberToShow][i-14] == 1:
                distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
        elif i < 28:
            if numbers[FourthNumberToShow][i-21] == 1:
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
    for i in range(numbers[FirstNumberToShow].count(1) + numbers[SecondNumberToShow].count(1) + numbers[ThirdNumberToShow].count(1)+ numbers[FourthNumberToShow].count(1)):
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
    
    #print(robot.getField('name').getSFString(), ' ', initPotential)
    NewPos = OldPos.copy()
    
    bestPotential = initPotential
    bestPos = NewPos.copy()
    
    for _ in range(3): # Perform five random steps, more steps, better routes less stuck
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
    # goalAssignments = [-1] * len(robots)

    # Initialize an empty array with a single row
    matrix = []  # Specify dtype=object to allow for lists or tuples
    for robot in robots:
        distances_to_digits = DistancesToDigits(robot)
        # to make sure the robots wont get assigned to a target that is not needed
        # for i in range(len(distances_to_digits)):
            # if numbers[numberToShow][i] == 0:
                # distances_to_digits[i]=99
        matrix.append(distances_to_digits)
    
    # print(matrix)
    
    cost = np.array(matrix)
    # print(cost)

    # Use linear_sum_assignment to find the optimal assignment
    for i in range(len(goalAssignments)):
        goalAssignments[i] = -1
    # goalAssignments = [-1] * len(robots)
    # print('before assignments', goalAssignments)
    row_ind, col_ind = linear_sum_assignment(cost)
    #print(row_ind, col_ind)
    for i in range(numbers[FirstNumberToShow].count(1) + numbers[SecondNumberToShow].count(1) + numbers[ThirdNumberToShow].count(1)+ numbers[FourthNumberToShow].count(1)): #  is the amount of objectives should be amount
        print('robotindex',row_ind[i],'digitIndex',col_ind[i])
        goalAssignments[row_ind[i]] = col_ind[i]
    
    
    # Calculate the total cost of the optimal assignment
    total = cost[row_ind, col_ind]
    # print(total)
    total_cost = total.sum()
    
    print("Total cost of the optimal assignment:", total_cost)
    # print('after assignments', goalAssignments)

def send_json_data(server_address, server_port, data):
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((server_address, server_port))

        # Convert data to JSON format
        json_data = json.dumps(data)

        # Send JSON data to the server
        client_socket.sendall(json_data.encode())

        # Close the connection
        client_socket.close()
    except Exception as e:
        print("Error:", e)
# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())
FirstNumberToShow = 2
SecondNumberToShow = 3
ThirdNumberToShow = 5
FourthNumberToShow = 8
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
for i in range(28):
    robots.append(supervisor.getFromDef('ROBOT' + str(i)))
    
obstacles = []
for i in range(2):
    obstacles.append(supervisor.getFromDef('OBSTACLE' + str(i)))
    
objectives = []
for i in range(1):
    objectives.append(supervisor.getFromDef('OBJECTIVE' + str(i)))
    
digitStripes = []
for number in range(4):
    digitStripes.append(supervisor.getFromDef('DigitTop' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitMid' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitBottom' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitTopLeft' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitTopRight' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitBottomLeft' + str(number)))
    digitStripes.append(supervisor.getFromDef('DigitBottomRight' + str(number)))

#put robots at random positions
for robot in robots:
    InitialPos = robot.getField("translation")
    NewPos=[int(80*random()-40)/10,int(80*random()-40)/10,0.1]
    InitialPos.setSFVec3f(NewPos)
    
#put obstacles at random positions    
for obstacle in obstacles:
    InitialPos = obstacle.getField("translation")
    NewPos=[int(80*random()-40)/10,int(80*random()-40)/10,0.1]
    # InitialPos.setSFVec3f(NewPos)

# each index is for the robot with the same index in robot, each number is the index for the digitstripe
goalAssignments = [-1] * len(robots)
# print(robots)
SERVER_ADDRESS = '145.137.54.45'  # Change this to your server's IP address
SERVER_PORT = 8000  # Change this to the port your server is listening on
# assignStripesToRobots()
firstloop = True
stepcounter = 0
sendcounter = 0
# Main loop:
while supervisor.step(timestep) != -1:
    if firstloop:
        assignStripesToRobots()
        firstloop=False
        
    for robot in robots:
        process_robot(robot)
    
    if sendcounter == 20:
        v0 = supervisor.getFromDef('ROBOT0').getField("translation").getSFVec3f()
        v1 = supervisor.getFromDef('ROBOT1').getField("translation").getSFVec3f()
        # Example positions of two robots
        robot0_position = {"time": datetime.now().strftime("%H:%M:%S"),"x": v0[0], "y": v0[1]}
        robot1_position = {"time": datetime.now().strftime("%H:%M:%S"),"x": v1[0], "y": v1[1]}

        # Combine positions into one dictionary
        data = {0: robot0_position, 1: robot1_position}
        print('sendjson: ', data)
        # send_json_data(SERVER_ADDRESS, SERVER_PORT, data)
        sendcounter = 0
    else:
        sendcounter += 1
    
    if stepcounter == 300:
        if FourthNumberToShow < 9:
            FourthNumberToShow += 1
        else:
            FourthNumberToShow = 0
            if ThirdNumberToShow < 5:
                ThirdNumberToShow += 1
            else:
                ThirdNumberToShow = 0
                if (SecondNumberToShow < 9 and FirstNumberToShow < 2) or (SecondNumberToShow < 3 and FirstNumberToShow == 2):
                    SecondNumberToShow += 1
                else:
                    SecondNumberToShow = 0
                    if FirstNumberToShow < 2:
                        FirstNumberToShow += 1
                    else:
                        FirstNumberToShow = 0
                        SecondNumberToShow = 0
                        ThirdNumberToShow = 0
                        FourthNumberToShow = 0
        
        assignStripesToRobots()
        stepcounter = 0
        print(FirstNumberToShow,SecondNumberToShow,':',ThirdNumberToShow,FourthNumberToShow)
    stepcounter += 1
    
# Enter here exit cleanup code.
