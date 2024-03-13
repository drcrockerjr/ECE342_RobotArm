
import numpy as np
import math

import json
import serial
import time
import threading
#from pprint import pprint


class Arm2Link:
    def __init__(self, len1, len2, base_x, base_y, q1_step_angle, q2_step_angle ):
        self.len1 = len1
        self.len2 = len2
        self.base_x = base_x
        self.base_y = base_y
        self.end_x = base_x + 10
        self.end_y = base_y + 10
        self.q1 = 0  # Angle of the first link
        self.q2 = 0  # Angle of the second link

        # Stepper motor angles moved per step:
        #   Nema 17 - 1.8 degrees
        self.q1_step_angle = q1_step_angle
        self.q2_step_angle = q2_step_angle

        self.q1_delta = 0 
        self.q2_delta = 0

        #self.end_x_delta = 0
        #self.end_y_delta = 0

        self.resolution_constant = 0.2

        self.delta_lock = threading.Lock()

    def calibrate(self):
        self.end_x = 0
        self.end_y = 0

    def move_to_zero(self, graph, move_que):
        self.calculate_angles_V2(graph, 0, 0, move_que)

    def set_end_effector_position(self, x, y):
        self.end_x = x
        self.end_y = y

    def calculate_angles(self, end_x, end_y):

        old_x = self.end_x
        old_y = self.end_y

        self.end_x = end_x
        self.end_y = end_y

        old_q1 = self.q1
        old_q2 = self.q2

        distance_to_endeff = math.sqrt((end_x - self.base_x)**2 + (end_y - self.base_y)**2)

        if(distance_to_endeff >= (self.len1 + self.len2)):
            self.end_x = old_x
            self.end_y = old_y
            return

        # Convert end effector position to polar coordinates
        r = math.sqrt((self.end_x - self.base_x)**2 + (self.end_y - self.base_y)**2)
        phi = math.atan2(self.end_y - self.base_y, self.end_x - self.base_x)
        # Using the cosine law to find the angles
        cos_q2 = (r**2 - self.len1**2 - self.len2**2) / (2 * self.len1 * self.len2)
        self.q2 = math.acos(cos_q2)  # Angle for the second link
        sin_q2 = math.sqrt(1 - cos_q2**2)
        self.q1 = phi - math.atan2((self.len2 * sin_q2), (self.len1 + self.len2 * cos_q2))  # Angle for the first link

        self.q1_delta = self.q1_delta + ( old_q1 - self.q1 )
        self.q2_delta = self.q2_delta + ( old_q2 - self.q2 )

        #print(self.q1_delta, self.q2_delta)

    def calculate_angles_V2(self, graph, new_end_x, new_end_y, move_que):
        old_x = self.end_x
        old_y = self.end_y

        self.end_x = new_end_x
        self.end_y = new_end_y

        q1_buf = 0 
        q2_buf = 0

        target_coords = []

        dis_base_to_endeff = math.sqrt((new_end_x - self.base_x) ** 2 + (new_end_y - self.base_y) ** 2)

        distance_to_new_endeff = math.sqrt((new_end_x - old_x) ** 2 + (new_end_y - old_y) ** 2)

        #if mouse pointer is outside of range possible with arm configuration dont draw updated 
        if dis_base_to_endeff >= (self.len1 + self.len2):
            self.end_x = old_x
            self.end_y = old_y
            return
        
        num_steps = max(int(distance_to_new_endeff * self.resolution_constant), 1)  # Ensure num_steps is at least 1

        deltaX = (self.end_x - old_x) / num_steps
        deltaY = (self.end_y - old_y) / num_steps

        for i in range(1, num_steps + 1):  # Include final point in the loop
            step_x = (i * deltaX) + old_x
            step_y = (i * deltaY) + old_y
            target_coords.append((step_x, step_y))

        print(f"\n\nTotal Coordinates: {len(target_coords)}\n")

        for coord in target_coords:

            old_q1 = self.q1
            old_q2 = self.q2

            x, y = coord

            #draw points of path
            graph.DrawPoint((int(x), int(y)), size=5, color='red')

            r = math.sqrt((x - self.base_x) ** 2 + (y - self.base_y) ** 2)
            phi = math.atan2(y - self.base_y, x - self.base_x)
            cos_q2 = (r ** 2 - self.len1 ** 2 - self.len2 ** 2) / (2 * self.len1 * self.len2)
            cos_q2 = max(min(cos_q2, 1), -1)  # Clamp cos_q2 to the range [-1, 1]
            self.q2 = math.acos(cos_q2)
            sin_q2 = math.sqrt(1 - cos_q2 ** 2)
            self.q1 = phi - math.atan2((self.len2 * sin_q2), (self.len1 + self.len2 * cos_q2))

            m1_n = abs(math.ceil(((old_q1 - self.q1) + q1_buf) / self.q1_step_angle))
            m2_n = abs(math.ceil(((old_q2 - self.q2) + q2_buf) / self.q2_step_angle))

            #save left over angle needed to traverse for new coordinate instructions
            q1_buf = abs(math.ceil(((old_q1 - self.q1) + q1_buf) % self.q1_step_angle))
            q2_buf = abs(math.ceil(((old_q2 - self.q2) + q2_buf) % self.q2_step_angle))

            if (old_q1 - self.q1) <= 0:
                m1_dir = 1
            else:
                m1_dir = 0

            if (old_q2 - self.q2) <= 0:
                m2_dir = 1
            else:
                m2_dir = 0

            data = {}
            data["m1_n"] = m1_n
            data["m2_n"] = m2_n
            data["m1_dir"] = m1_dir
            data["m2_dir"] = m2_dir

            '''packet = {
                "m1_tck":                 "m1_tck": m1_ticks,
,
                "m2_tck": m2_ticks,
                "m1_dir": m1_dir,
                "m2_dir": m2_dir
            }'''

            data = json.dumps(data)
            print(data)
            move_que.put(data)

        print("\n\n Coordinates Flushed \n\n ")
        


    def draw_arm(self, graph):
        # Clear previous drawings
        #graph.erase()

        # Calculate the joint position based on the angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)


        # Draw the arm: base -> joint -> end effector
        graph.draw_line((self.base_x, self.base_y), (joint_x, joint_y), width=5)
        graph.draw_line((joint_x, joint_y), (self.end_x, self.end_y), width=5)

        #print(math.degrees(self.q1), math.degrees(self.q2))

    def update_end_effector_position(self):
        # Calculate the end effector's position based on the current angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        self.end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        self.end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)
