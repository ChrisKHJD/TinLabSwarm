import socket
import network
import time
from machine import Pin, PWM
import json
from time import sleep




# Constants
BUILT_IN_LED = 25  # Built-in LED
FLED = 20  # Front LED Red
BLED = 21  # Back LED Green
PWM_LM = 6  # Left Continuous Servo 
PWM_RM = 7  # Right Continuous Servo
PWM_SC = 10  # Panning Servo
SDA = 4
SCL = 5
MISO = 16
MOSI = 19
SCK = 18
CS = 17

# Insert your network parameters
SSID = b'tesla iot' 
PWD = b'fsL6HgjN' 

PORT = 8000
IP_ADDRESS = "145.24.223.115"
TIMEOUT_VALUE = 0.1  # Set timeout for non-blocking receive operations

class RobotController:
    def __init__(self):
        self.setup_pins()
        self.setup_servos()
        self.setup_network()
        self.last_send_time = time.time()  # Set initial time
        self.s = None  

    def setup_pins(self):
        self.built_in_led = Pin(BUILT_IN_LED, Pin.OUT)
        self.fled = Pin(FLED, Pin.OUT)
        self.bled = Pin(BLED, Pin.OUT)

    def setup_servos(self):
        self.LeftMotor = PWM(Pin(PWM_LM))
        self.LeftMotor.freq(50)
        self.RightMotor = PWM(Pin(PWM_RM))
        self.RightMotor.freq(50)
        self.PanMotor = PWM(Pin(PWM_SC))
        self.PanMotor.freq(50)
        
    def blink_leds(self):
        # Blink the front and back LEDs
        for _ in range(5):  # Blink 5 times
            self.fled.value(not self.fled.value())  # Toggle front LED
            self.bled.value(not self.bled.value())  # Toggle back LED
            time.sleep(0.5)  # 0.5 second delay between blinks
            print("Blinking Led'")
            
    def emergency_stop(self):
        # Stop all movements and blink LEDs
        self.LeftMotor.duty_u16(0)
        self.RightMotor.duty_u16(0)
        #self.PanMotor.duty_u16(0)
        self.blink_leds()
        print("Emergency Stop") 
            
    def move_forward(self):
        print("Moving Forward")

        # Control the motors to move forward
        self.LeftMotor.duty_u16(5000)
        self.RightMotor.duty_u16(5000)
        
    def move_backward(self):
        print("Moving Back")

        # Control the motors to move backward (adjust values for your robot)
        self.LeftMotor.duty_u16(3000)
        self.RightMotor.duty_u16(7000)

    def turn_left(self):
        # Control the servos to turn left (adjust values for your robot)
        print("Turning Left")

        self.LeftMotor.duty_u16(10)  # Lower duty cycle for left motor (example)
        self.RightMotor.duty_u16(1000)  # Higher duty cycle for right motor (example)
        

    def turn_right(self):
        # Control the servos to turn right (adjust values for your robot)
        print("Turning Right")

        self.LeftMotor.duty_u16(1000)  # Higher duty cycle for left motor (example)
        self.RightMotor.duty_u16(10)  # Lower duty cycle for right motor (example)
        
    
    def main_loop(self):
        while True:
            self.move_forward()
            time.sleep(2)

            self.turn_left()
            time.sleep(2)

            self.turn_right()
            time.sleep(2)

            self.move_backward()
            time.sleep(2)


# Main function
def main():
    robot = RobotController()
    robot.main_loop()

if __name__ == "__main__":
    main()
