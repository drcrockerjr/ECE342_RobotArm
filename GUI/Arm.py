
import numpy as np
import math

import json
import serial
import time
import threading
#from pprint import pprint


def round_half_up(n, decimals=0):
        multiplier = 10**decimals
        return math.floor(n * multiplier + 0.5) / multiplier

def calculate_closest_point(arm, q1, q2):
        """
        Calculate the closest possible point that can be reached by the arm,
        given its step angle limitations.
        """

        # Recalculate the end effector position based on the adjusted angles
        joint_x = arm.base_x + arm.len1 * math.cos(q1)
        joint_y = arm.base_y + arm.len1 * math.sin(q1)
        end_x = joint_x + arm.len2 * math.cos(q1 + q2)
        end_y = joint_y + arm.len2 * math.sin(q1 + q2)

        return end_x, end_y

class Arm2Link:
    def __init__(self, len1, len2, base_x, base_y, q1_step_angle, q2_step_angle ):
        self.len1 = len1
        self.len2 = len2
        self.draw_base_x = base_x
        self.draw_base_y = base_y

        self.base_x = 0
        self.base_y = 0

        self.end_x = self.end_y = 0
        self.last_end_x = self.last_end_y = 0

        self.q1 = 0  # Angle of the first link
        self.q2 = 0  # Angle of the second link

        self.q1_draw = self.q2_draw = 0

        # Stepper motor angles moved per step:
        #   Nema 17 - 1.8 degrees
        self.q1_step_angle = q1_step_angle
        self.q2_step_angle = q2_step_angle

        self.q1_delta = 0 
        self.q2_delta = 0

        #self.end_x_delta = 0
        #self.end_y_delta = 0

        self.resolution_constant = 0.05


    def calibrate(self):
        self.end_x = 0
        self.end_y = 0

    def move_to_zero(self, graph, move_que):
        self.calculate_angles_V2(graph, 0, 0, move_que)

    def set_end_effector_position(self, x, y):
        self.end_x = x
        self.end_y = y

    def calculate_drawing_angles(self, graph, new_end_x, new_end_y):

        self.end_x = new_end_x
        self.end_y = new_end_y

        target_coords = []

        dis_base_to_endeff = math.sqrt((new_end_x - self.draw_base_x) ** 2 + (new_end_y - self.draw_base_y) ** 2)

        distance_to_new_endeff = math.sqrt((new_end_x - self.last_end_x) ** 2 + (new_end_y - self.last_end_y) ** 2)

        #if mouse pointer is outside of range possible with arm configuration dont draw updated 
        if dis_base_to_endeff >= (self.len1 + self.len2):
            self.end_x = self.last_end_x
            self.end_y = self.last_end_y
            return
        
        num_steps = max(int(distance_to_new_endeff * self.resolution_constant), 1)  # Ensure num_steps is at least 1

        deltaX = (new_end_x - self.last_end_x) / num_steps
        deltaY = (new_end_y - self.last_end_y) / num_steps

        for i in range(1, num_steps + 1):  # Include final point in the loop
            step_x = (i * deltaX) + self.last_end_x
            step_y = (i * deltaY) + self.last_end_y
            target_coords.append((step_x, step_y))

        target_coords.append((new_end_x, new_end_y))

        print(f"\n\nTotal Coordinates: {len(target_coords)}\n")

        for coord in target_coords:

            x, y = coord

            #draw points of path
            graph.DrawPoint((int(x), int(y)), size=5, color='red')

            r = math.sqrt((x - self.draw_base_x) ** 2 + (y - self.draw_base_y) ** 2)
            phi = math.atan2(y - self.draw_base_y, x - self.draw_base_x)
            cos_q2 = (r ** 2 - self.len1 ** 2 - self.len2 ** 2) / (2 * self.len1 * self.len2)
            cos_q2 = max(min(cos_q2, 1), -1)  # Clamp cos_q2 to the range [-1, 1]
            self.q2_draw = math.acos(cos_q2)
            sin_q2 = math.sqrt(1 - cos_q2 ** 2)
            self.q1_draw = phi - math.atan2((self.len2 * sin_q2), (self.len1 + self.len2 * cos_q2))



    def calculate_angles_V2(self, graph, new_end_x, new_end_y, move_que):
        old_x = self.last_end_x
        old_y = self.last_end_y

        self.end_x = new_end_x
        self.end_y = new_end_y

        q1_buf = 0 
        q2_buf = 0

        target_coords = []

        dis_base_to_endeff = math.sqrt((new_end_x - self.draw_base_x) ** 2 + (new_end_y - self.draw_base_y) ** 2)

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

        target_coords.append((self.end_x, self.end_y))

        print(f"\n\nTotal Coordinates: {len(target_coords)}\n")

        self.base_x = self.draw_base_x
        self.base_y = self.draw_base_y

        for coord in target_coords:

            old_q1 = self.q1
            old_q2 = self.q2

            x, y = coord

            r = math.sqrt((x - self.base_x) ** 2 + (y - self.base_y) ** 2)
            phi = math.atan2(y - self.base_y, x - self.base_x)
            cos_q2 = (r ** 2 - self.len1 ** 2 - self.len2 ** 2) / (2 * self.len1 * self.len2)
            cos_q2 = max(min(cos_q2, 1), -1)  # Clamp cos_q2 to the range [-1, 1]
            self.q2 = math.acos(cos_q2)
            sin_q2 = math.sqrt(1 - cos_q2 ** 2)
            self.q1 = phi - math.atan2((self.len2 * sin_q2), (self.len1 + self.len2 * cos_q2))

            m1_n = abs(int(round_half_up( ( (old_q1 - self.q1) + q1_buf ) / self.q1_step_angle ) ))
            m2_n = abs(int(round_half_up( ( (old_q2 - self.q2) + q2_buf) / self.q2_step_angle ) ))

            #save left over angle needed to traverse for new coordinate instructions
            q1_buf = abs(((old_q1 - self.q1) + q1_buf) % self.q1_step_angle)
            q2_buf = abs(((old_q2 - self.q2) + q2_buf) % self.q2_step_angle)

            possible_q1 = self.q1 + (self.q1_step_angle * m1_n)
            possible_q2 = self.q2 + (self.q2_step_angle * m2_n)
            #Find closest possible point with step angle limitations
            possible_x , possible_y = calculate_closest_point(self, possible_q1, possible_q2)

            #draw points of path
            graph.DrawPoint((int(possible_x), int(possible_y)), size=5, color='blue')

            if (old_q1 - self.q1) <= 0:
                m1_dir = 0
            else:
                m1_dir = 1

            if (old_q2 - self.q2) <= 0:
                m2_dir = 0
            else:
                m2_dir = 1

            data = {}
            data["m1_n"] = m1_n
            data["m2_n"] = m2_n
            data["m1_dir"] = m1_dir
            data["m2_dir"] = m2_dir

            data = json.dumps(data)
            print(data)
            move_que.put(data)

        print("\n\n Coordinates Flushed \n\n ")

        self.last_end_x = new_end_x
        self.last_end_y = new_end_y
        


    def draw_arm(self, graph):
        # Clear previous drawings
        #graph.erase()

        # Calculate the joint position based on the angles
        joint_x = self.draw_base_x + self.len1 * math.cos(self.q1_draw)
        joint_y = self.draw_base_y + self.len1 * math.sin(self.q1_draw)


        # Draw the arm: base -> joint -> end effector
        graph.draw_line((self.draw_base_x, self.draw_base_y), (joint_x, joint_y), width=5)
        graph.draw_line((joint_x, joint_y), (self.end_x, self.end_y), width=5)

        #print(math.degrees(self.q1), math.degrees(self.q2))

    def update_end_effector_position(self):
        # Calculate the end effector's position based on the current angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        self.end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        self.end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)
