"""my_simple_supervisor controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot
from controller import Supervisor
from random import random
from math import sqrt, pow, dist
import sys

def GetOtherRobots(CurrentRobot): 
    # gets an array of the other (different from the current instance) nodes of type MyFirstProto
    OtherRobots=[] 
    # gets the full list of nodes from the root
    root_node = robot.getRoot()
    root_children_field = root_node.getField("children")
    n = root_children_field.getCount()
    #print("This world contains ", n,"nodes\n");
    # selects all the robots generated from the Proto
    j=0
    for i in range(0,n):
        node=root_children_field.getMFNode(i)
        if node.getTypeName()=="MyFirstProto":
            #print("A robot node named: ",node.getField("name").getSFString(),"\n")
            if node.getField("name").getSFString()!=CurrentRobot.getField("name").getSFString():
                OtherRobots.append(node)
                j=j+1
    return(OtherRobots) 

def Distance(V1,V2):
    #trivial cartesian distance in 3D
    return(dist(V1.getSFVec3f(),V2.getSFVec3f()))
    
def ArrayByScalar(V1,n):
    V=[]
    for each in V1:
        V.append(each*n)
    return(V)

def ArrayPlusArray(V1,V2):
    V=[]
    for i in range(0,len(V1)):
        V.append(V1[i]+V2[i])
    return(V)

def ArrayNorm(V1):
    return(dist([0,0,0],V1)) 

def DistancesToOtherRobots(CurrentRobot,OtherRobots):
    #calculates an array of distances between current robot and the others
    distances=[];
    for each in OtherRobots:
        distances.append(Distance(CurrentRobot.getField("translation"),each.getField("translation")))
    return(distances)

def DirectionsToOtherRobots(CurrentRobot,OtherRobots):
    # calcuates the direction vector between CurrentRObot and the others
    directions=[]
    for each in OtherRobots:
        CurrentPos=CurrentRobot.getField("translation").getSFVec3f()
        eachPos=each.getField("translation").getSFVec3f()
        direction=[]
        for i in range(0,len(CurrentPos)):
            direction.append(eachPos[i]-CurrentPos[i])
        l=dist([0,0,0],direction) # a trick to calculate the norm of the direction vector
        for i in range(0,len(direction)):
            direction[i]=direction[i]/l
        # now direction contains a unit vector pointing from the CurrentRobot to one of the Others
        # and directions contains the same for eveyone of the others
        directions.append(direction)
    return(directions)

def ForcesToOtherRObots(CurrentRobot,OtherRobots):
    #defines the interaction force depending on the distance
    # positive force is attractive
    # force becomes repulsive below a distance of 1
    # force fades in the distance as 1/x
    Distances=DistancesToOtherRobots(CurrentRobot,OtherRobots)
    Directions=DirectionsToOtherRobots(CurrentRobot,OtherRobots)
    # calculates the intensity of the forces
    IntensityOfForces=[]
    for each in Distances:
        if each<0.5:
            IntensityOfForces.append(2)
        else:
            #IntensityOfForces.append((1/each-2/pow(each,2)))
            IntensityOfForces.append((1/each))
     # calculates the actual force vector from the current robot to the others
    Forces=[]
    for i in range(0,len(Directions)):
        direction=Directions[i]
        intensity=IntensityOfForces[i]
        force=[]
        for j in range(0,len(direction)):
            force.append(direction[j]*intensity)
        Forces.append(force)
    return(Forces)
    


robot = Supervisor() # instead of robot = Robot()
# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

supervisorNode = robot.getSelf() # the robot we are going to control from the current instance of this code
#print("current robot is: ",supervisorNode.getField("name").getSFString(),"\n")

# sets a random initial position
InitialPos = supervisorNode.getField("translation")
if not supervisorNode.getField("name").getSFString()=="SPACE1":
    NewPos=[int(80*random()-40)/10,int(80*random()-40)/10,0.1]
    InitialPos.setSFVec3f(NewPos)

# wants to list the other robots in the scene
OtherRobots=GetOtherRobots(supervisorNode)

while robot.step(timestep) != -1:
    # extracts the velocity of the CurrentRobot
    CurrentVelocity=supervisorNode.getField("velocity").getSFVec3f()

    # calculates the force acting on the current robot due to the presence of the  others
    #Distances=DistancesToOtherRobots(supervisorNode,OtherRobots)
    #Directions=DirectionsToOtherRobots(supervisorNode,OtherRobots)
    Forces=ForcesToOtherRObots(supervisorNode,OtherRobots)
    #print("The other Robots are:\n")
    
    #for i in range(0,len(OtherRobots)):
    #    print(OtherRobots[i].getField("name").getSFString()," at distance ",Distances[i]," in direction ",Directions[i], " with Force ", Forces[i],"\n")
    
    TotalForce=[0,0,0]
    for each in Forces:
        TotalForce=ArrayPlusArray(TotalForce,each)
    # we now update the force field in the robot
    ForceHandle = supervisorNode.getField("force")
    ForceHandle.setSFVec3f(TotalForce) 

    
    if supervisorNode.getField("name").getSFString()=="ROBOT1":
        print("***********************************\n")
    print("Total Force acting on ",supervisorNode.getField("name").getSFString()," is: ",dist([0,0,0],TotalForce),"\n")
    # now we update the position of the robot...
    # we assume M=1, so acceleration equal force and so the new velocity is
    Mass=1
    # we also assume the simulation is in milliseconds
    BasicTime=0.005
    CurrentVelocity=ArrayPlusArray(CurrentVelocity,ArrayByScalar(TotalForce,1/Mass*timestep*BasicTime))
    # and from this one, we calculate the next position
    CurrentPos = supervisorNode.getField("translation").getSFVec3f()
    NextPos=ArrayPlusArray(CurrentPos,ArrayByScalar(CurrentVelocity,timestep*BasicTime))
    # update the position
    trans = supervisorNode.getField("translation")
    if not supervisorNode.getField("name").getSFString()=="SPACE1":
        trans.setSFVec3f(NextPos) # pos = [x, y, z]
    
    #exit condition
    # if ALL the forces are below the minimum value, we stop
    MinForceValue=0.001
    MaxForce=ArrayNorm(TotalForce) # the force acting on the CurrentRobot
    for each in OtherRobots:
        MaxForce=max(MaxForce,ArrayNorm(each.getField("force").getSFVec3f()))
    if MaxForce<=MinForceValue:
        break
sys.exit(0) 
        
    
    
    
    

        
            
    
    

