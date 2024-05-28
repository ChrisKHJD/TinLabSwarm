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

    def setup_network(self):
        network.hostname("mypicow")
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
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
        # Control the motors to move forward
        self.LeftMotor.duty_u16(5000)
        self.RightMotor.duty_u16(5000)
        #time.sleep(5)
        #self.LeftMotor.duty_u16(5000)
        #self.RightMotor.duty_u16(5000)
        print("Moving Forward")
        
    def move_backward(self):
        # Control the motors to move backward (adjust values for your robot)
        # This is a basic example, may require reversing motor direction based on hardware
        self.LeftMotor.duty_u16(3000)
        self.RightMotor.duty_u16(7000)
        #time.sleep(1)
        #self.LeftMotor.duty_u16(5000)
        #self.RightMotor.duty_u16(5000)
        print("Moving Back")

    def turn_left(self):
        # Control the servos to turn left (adjust values for your robot)
        self.LeftMotor.duty_u16(10)  # Lower duty cycle for left motor (example)
        self.RightMotor.duty_u16(1000)  # Higher duty cycle for right motor (example)
        #time.sleep(3)
        #self.LeftMotor.duty_u16(5000)
        #self.RightMotor.duty_u16(5000)
        
        print("Turning Left")

    def turn_right(self):
        # Control the servos to turn right (adjust values for your robot)
        self.LeftMotor.duty_u16(1000)  # Higher duty cycle for left motor (example)
        self.RightMotor.duty_u16(10)  # Lower duty cycle for right motor (example)
        time.sleep(1) 
        #self.LeftMotor.duty_u16(500)
        #self.RightMotor.duty_u16(0)
        
        #self.emergency_stop()
        print("Turning Right")
    
    def test_move(self):
        self.LeftMotor.duty_u16(3000)
        self.RightMotor.duty_u16(7000)
        time.sleep(1)
        self.emergency_stop()
        time.sleep(1)
        self.LeftMotor.duty_u16(0)
        self.RightMotor.duty_u16(3000)
        print("Turn Left")
        time.sleep(1)
        self.LeftMotor.duty_u16(3000)
        self.RightMotor.duty_u16(0)
        time.sleep(1)
        self.emergency_stop()
        
        print("Test Funciton")
    
        
    def send_data(self):
        """Sends a JSON-formatted payload to the server."""
        print("RobotController: Sending data...")
        try:
            if not self.s:  # Ensure socket is created before sending
                self.create_socket()

            payload = {"type": "chariot"}
            #payload = {"type": "chariot", "time_sent": datetime.now().strftime("%H:%cM:%S")}
            encoded_payload = json.dumps(payload).encode("ascii")
            self.s.sendall(encoded_payload)
            print(f"RobotController: Sent payload: {payload}")
        except Exception as e:
            print(f"RobotController: Error sending data: {e}")


    def receive_data(self):
        """Attempts to receive data from the server.

        Returns True if data is received, False otherwise.
        """
        print("RobotController: Receiving data...")
        try:
            if not self.s:  # Ensure socket is created before receiving
                self.create_socket()

            received_data = self.s.recv(1024).decode()  # Set a reasonable buffer size
            if received_data:
                print(f"RobotController: Received: {received_data}")
                
                # Parse the received data (assuming JSON format)
                try:
                    data = json.loads(received_data)
                    instruction = data.get("instruction")
                    if instruction == "move":
                        # Call a function to handle the turn_left instruction
                        self.test_move()
                    # ... add logic for other instructions (turn_right, move_forward, etc.)
                    else:
                        print(f"RobotController: Unknown instruction: {instruction}")
                    
                except Exception as e:  
                    print(f"RobotController: Error parsing data: {e}")
                return True
            else:
                print("RobotController: No data received")
                return False
        except Exception as e:
            print(f"RobotController: Error receiving data: {e}")
            return False


    def create_socket(self):
        """Creates a socket connection to the server."""
        print("RobotController: Creating socket...")
        
        try:
            self.s = socket.socket()
            self.s.connect((IP_ADDRESS, PORT))
            print("This...")
            print("RobotController: Connected!")
            self.s.settimeout(TIMEOUT_VALUE)  # Set non-blocking receive timeout
        except Exception as e:
            print(f"RobotController: Connection failed: {e}")
            self.s = None  # Reset socket on failure
            
        # Send a connection message
        connection_message = {"type": "connection", "message": "Connected from RobotController"}
        encoded_message = json.dumps(connection_message).encode("ascii")
        self.s.sendall(encoded_message)
        print(f"RobotController: Sent connection message: {connection_message}")

    def connect_wifi(self):
        time0 = time.time()
        self.wlan.connect(SSID, PWD)
        while True:
            if self.wlan.isconnected():
                print("\nConnected!\n")
                self.built_in_led.value(True)
                print("IP Address:", self.wlan.ifconfig()[0])  # Print IP address
                break
            else:
                print(".")
                time.sleep(1)
                if time.time() - time0 > 10:
                    print("Connection could not be established")
                    break

    def serve_requests(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        print("Listening to port 80\n")
        s.listen(1)

        while True:
            cl, addr = s.accept()
            print("Incoming connection request from: " + str(addr) + "\n")
            cl_file = cl.makefile('rwb', 0)
            found = False
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
                if not found:
                    if str(line).find("/?PRESS=FRONT_LED_ON") != -1:
                        self.fled.value(True)
                        found = True
                    if str(line).find("/?PRESS_1=FRONT_LED_OFF") != -1:
                        self.fled.value(False)
                        found = True
                    if str(line).find("/?PRESS_2=BACK_LED_ON") != -1:
                        self.bled.value(True)
                        found = True
                    if str(line).find("/?PRESS_3=BACK_LED_OFF") != -1:
                        self.bled.value(False)
                        found = True
                    if str(line).find("/?PRESS_4=MOVE") != -1:
                        self.move_forward(50, 1)
                        found = True

            # We process the response file
            try:
                response = "HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n" + open("main.html", "r").read()
            except:
                response = "HTTP/1.0 404 Not Found\r\n\r\n"
            cl.send(response)
            cl.close()
    
    def main_loop(self):
        """Main program loop for network communication."""
        while True:
            try:
                # Send data every second
                if time.time() - self.last_send_time >= 1:
                    self.send_data()
                    self.last_send_time = time.time()

                # Attempt to receive data non-blocking
                if self.receive_data():
                    # Handle received data as needed (e.g., process commands)
                    pass

            except Exception as e:
                print(f"RobotController: Error: {e}")

            sleep(0.5)  # Introduce a delay between attempts


# Main function
def main():
    robot = RobotController()
    robot.connect_wifi()
    #robot.serve_requests()
    robot.main_loop()

if __name__ == "__main__":
    main()
