from machine import PWM, Pin
from time import sleep

# Define GPIO pins
PWM_LM = 6  # Left motor PWM pin
PWM_RM = 7  # Right motor PWM pin

# Define initial duty cycle values for calibration (reasonable midpoint)
INITIAL_DUTY_CYCLE = 4500  # Midpoint for 16-bit PWM (65535 / 2 / 2)
DIFFERENTIAL = 575  # Differential adjustment for the right motor

# Define PWM frequency for motors
MOTOR_FREQ = 50  # Typically 50Hz for servos

# Define calibration parameters
STEP_SIZE = 50  # Increment step size for duty cycle
STEP_DELAY = 5  # Delay in seconds for each step
MAX_STEPS = 5  # Number of steps for calibration

class Robot:
    def __init__(self, pwm_lm_pin, pwm_rm_pin):
        # Initialize PWM objects
        self.left_motor = PWM(Pin(pwm_lm_pin))
        self.right_motor = PWM(Pin(pwm_rm_pin))

        # Set PWM frequencies
        self.left_motor.freq(MOTOR_FREQ)
        self.right_motor.freq(MOTOR_FREQ)

        print("Robot initialized with motor pins.")

    def move_servo(self, servo, pulse_width):
        """
        Controls a servo motor with a specific pulse width.

        Args:
            servo: The PWM object representing the servo motor.
            pulse_width: The desired pulse width in microseconds.
        """
        servo.duty_u16(pulse_width)
        print(f"Moving servo with pulse width: {pulse_width}")

    def move_left(self, pulse_width):
        """
        Moves the left servo motor with a specified pulse width.

        Args:
            pulse_width: The desired pulse width in microseconds.
        """
        self.move_servo(self.left_motor, pulse_width)
        print(f"Left motor pulse width set to: {pulse_width}")

    def move_right(self, pulse_width):
        """
        Moves the right servo motor with a specified pulse width.

        Args:
            pulse_width: The desired pulse width in microseconds.
        """
        self.move_servo(self.right_motor, pulse_width)
        print(f"Right motor pulse width set to: {pulse_width}")

    def stop_servos(self):
        """
        Stops both left and right servo motors.
        """
        self.move_servo(self.left_motor, 5000)
        self.move_servo(self.right_motor, 4950)
        print("Both servos stopped.")

    def calibrate_servos(self):
        """
        Calibrates the servos by gradually changing the pulse width.
        """
        print("Starting forward calibration...")
        # Forward calibration
        for i in range(MAX_STEPS):
            left_pulse = INITIAL_DUTY_CYCLE + i * STEP_SIZE
            right_pulse = INITIAL_DUTY_CYCLE + DIFFERENTIAL + i * STEP_SIZE
            self.move_left(left_pulse)
            self.move_right(right_pulse)
            sleep(STEP_DELAY)

        self.stop_servos()
        sleep(STEP_DELAY)

        print("Starting backward calibration...")
        # Backward calibration
        for i in range(MAX_STEPS):
            left_pulse = INITIAL_DUTY_CYCLE - i * STEP_SIZE
            right_pulse = INITIAL_DUTY_CYCLE + DIFFERENTIAL - i * STEP_SIZE
            self.move_left(left_pulse)
            self.move_right(right_pulse)
            sleep(STEP_DELAY)

        self.stop_servos()
        print("Calibration complete.")

def main():
    robot = Robot(pwm_lm_pin=PWM_LM, pwm_rm_pin=PWM_RM)
    robot.calibrate_servos()

if __name__ == "__main__":
    main()
