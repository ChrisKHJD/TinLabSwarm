import network
import socket
from machine import Pin, PWM
import time

# Constants
SSID = b'tesla iot'
PWD = b'fsL6HgjN'
BUILT_IN_LED = 25  # Built-in LED
PWM_LM = 6  # Left Continuous Servo 
PWM_RM = 7  # Right Continuous Servo

# Calibration values for the neutral position of each motor
LEFT_NEUTRAL = 5000
RIGHT_NEUTRAL = 5000

class MotorCalibrator:
    def __init__(self):
        self.setup_pins()
        self.setup_servos()
        self.connect_wifi()
        self.left_duty_cycle = LEFT_NEUTRAL
        self.right_duty_cycle = RIGHT_NEUTRAL

    def setup_pins(self):
        self.built_in_led = Pin(BUILT_IN_LED, Pin.OUT)

    def setup_servos(self):
        self.LeftMotor = PWM(Pin(PWM_LM))
        self.LeftMotor.freq(50)
        self.RightMotor = PWM(Pin(PWM_RM))
        self.RightMotor.freq(50)

    def connect_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(SSID, PWD)
        while not wlan.isconnected():
            time.sleep(1)
            print("Connecting to WiFi...")

        self.built_in_led.value(True)
        print("Connected to WiFi")
        print("IP Address:", wlan.ifconfig()[0])

    def move_forward(self):
        self.LeftMotor.duty_u16(self.left_duty_cycle)
        self.RightMotor.duty_u16(self.right_duty_cycle)
        print("Moving Forward")

    def move_backward(self):
        self.LeftMotor.duty_u16(self.left_duty_cycle - 2000)
        self.RightMotor.duty_u16(self.right_duty_cycle - 2000)
        print("Moving Backward")

    def turn_left(self):
        self.LeftMotor.duty_u16(self.left_duty_cycle - 2000)
        self.RightMotor.duty_u16(self.right_duty_cycle + 2000)
        print("Turning Left")

    def turn_right(self):
        self.LeftMotor.duty_u16(self.left_duty_cycle + 2000)
        self.RightMotor.duty_u16(self.right_duty_cycle - 2000)
        print("Turning Right")

    def stop_motors(self):
        self.LeftMotor.duty_u16(LEFT_NEUTRAL)
        self.RightMotor.duty_u16(RIGHT_NEUTRAL)
        print("Motors Stopped")

    def serve_requests(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        print("Listening on port 80")

        while True:
            cl, addr = s.accept()
            print("Connection from", addr)
            request = cl.recv(1024).decode()
            print("Request:", request)

            if "/?left_increase" in request:
                self.left_duty_cycle += 100
            elif "/?left_decrease" in request:
                self.left_duty_cycle -= 100
            elif "/?right_increase" in request:
                self.right_duty_cycle += 100
            elif "/?right_decrease" in request:
                self.right_duty_cycle -= 100
            elif "/?move_forward" in request:
                self.move_forward()
            elif "/?move_backward" in request:
                self.move_backward()
            elif "/?turn_left" in request:
                self.turn_left()
            elif "/?turn_right" in request:
                self.turn_right()
            elif "/?stop" in request:
                self.stop_motors()

            print(f"Left Duty Cycle: {self.left_duty_cycle}, Right Duty Cycle: {self.right_duty_cycle}")

            response = self.generate_html()
            cl.send(response)
            cl.close()

    def generate_html(self):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Motor Calibration</title>
</head>
<body>
    <h1>Motor Calibration</h1>
    <p>Left Motor Duty Cycle: {left_duty_cycle}</p>
    <p>Right Motor Duty Cycle: {right_duty_cycle}</p>
    <a href="/?left_increase"><button>Increase Left</button></a>
    <a href="/?left_decrease"><button>Decrease Left</button></a>
    <a href="/?right_increase"><button>Increase Right</button></a>
    <a href="/?right_decrease"><button>Decrease Right</button></a>
    <a href="/?move_forward"><button>Move Forward</button></a>
    <a href="/?move_backward"><button>Move Backward</button></a>
    <a href="/?turn_left"><button>Turn Left</button></a>
    <a href="/?turn_right"><button>Turn Right</button></a>
    <a href="/?stop"><button>Stop Motors</button></a>
</body>
</html>
"""
        return html.format(left_duty_cycle=self.left_duty_cycle, right_duty_cycle=self.right_duty_cycle)

def main():
    calibrator = MotorCalibrator()
    calibrator.serve_requests()

if __name__ == "__main__":
    main()
