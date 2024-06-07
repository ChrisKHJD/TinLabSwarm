import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class Robot:
    def __init__(self, front_x, front_y, back_x, back_y):
        self.front_x = front_x
        self.front_y = front_y
        self.back_x = back_x
        self.back_y = back_y
        self.path = [(front_x, front_y)]
        self.orientation = self.calculate_orientation()

    def calculate_orientation(self):
        dx = self.front_x - self.back_x
        dy = self.front_y - self.back_y
        return math.degrees(math.atan2(dy, dx))

    def rotate_left(self):
        self.orientation += 3
        if self.orientation > 180:
            self.orientation -= 360
        self.update_position()

    def rotate_right(self):
        self.orientation -= 3
        if self.orientation < -180:
            self.orientation += 360
        self.update_position()

    def move_forward(self):
        rad = math.radians(self.orientation)
        move_x = math.cos(rad)
        move_y = math.sin(rad)

        self.front_x += move_x
        self.front_y += move_y
        self.back_x += move_x
        self.back_y += move_y

        self.path.append((self.front_x, self.front_y))

    def distance_to_target(self, target_x, target_y):
        return math.sqrt((self.front_x - target_x) ** 2 + (self.front_y - target_y) ** 2)

    def angle_to_target(self, target_x, target_y):
        target_angle = math.degrees(math.atan2(target_y - self.front_y, target_x - self.front_x))
        angle_diff = target_angle - self.orientation
        return (angle_diff + 180) % 360 - 180  # normalize to [-180, 180]

    def update_position(self):
        length = math.sqrt((self.front_x - self.back_x) ** 2 + (self.front_y - self.back_y) ** 2)
        rad = math.radians(self.orientation)

        self.back_x = self.front_x - length * math.cos(rad)
        self.back_y = self.front_y - length * math.sin(rad)

    def navigate_step(self, target_x, target_y):
        if self.distance_to_target(target_x, target_y) > 1:  # assuming a threshold distance of 1 unit to reach the target
            angle_diff = self.angle_to_target(target_x, target_y)
            if abs(angle_diff) > 3:  # tolerance for angle alignment
                if angle_diff > 0:
                    self.rotate_left()
                else:
                    self.rotate_right()
            else:
                self.move_forward()

            # Output robot's state for debugging
            print(
                f"Robot at Front Position: ({self.front_x:.2f}, {self.front_y:.2f}), Orientation: {self.orientation:.2f}°")


def update(num, robots, target_x, target_y, lines, scatters, orientation_lines):
    for i, robot in enumerate(robots):
        robot.navigate_step(target_x, target_y)
        lines[i].set_data(*zip(*robot.path))
        scatters[i].set_offsets([robot.path[-1]])

        # Update orientation line
        rad = math.radians(robot.orientation)
        orientation_end_x = robot.front_x + 0.5 * math.cos(rad)  # Length of the orientation line segment
        orientation_end_y = robot.front_y + 0.5 * math.sin(rad)
        orientation_lines[i].set_data([robot.front_x, orientation_end_x], [robot.front_y, orientation_end_y])


# Example usage
robots = [
    Robot(0, 0, 0, -1),
    Robot(16, 14, 17, 14),
    Robot(10, 0, 9, -1)
]  # Initial positions for the front and back of the robots
target_x, target_y = 10, 10  # Target position

fig, ax = plt.subplots()
ax.set_xlim(-1, 20)
ax.set_ylim(-1, 20)
ax.set_aspect('equal')
ax.plot(target_x, target_y, 'ro')  # Target position

lines = [ax.plot([], [], 'b-')[0] for _ in robots]  # Robot paths
scatters = [ax.scatter([], [], c='blue') for _ in robots]  # Robot positions
orientation_lines = [ax.plot([], [], 'g-')[0] for _ in robots]  # Orientation lines

ani = animation.FuncAnimation(fig, update, fargs=(robots, target_x, target_y, lines, scatters, orientation_lines),
                              interval=1000)

plt.show()
