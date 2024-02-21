
import numpy as np
import math

import json
import serial
import time
from pprint import pprint


class Arm2Link:
    def __init__(self, graph, len1, len2, base_x, base_y, q1_step_angle, q2_step_angle ):
        self.graph = graph
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

        self.movement_buffer = []


    def set_end_effector_position(self, x, y):
        self.end_x = x
        self.end_y = y

    def calculate_angles(self, end_x, end_y):

        old_x = self.end_x
        old_y = self.end_y

        self.end_x = end_x
        self.end_y = end_y

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


    def draw_arm(self):
        # Clear previous drawings
        self.graph.erase()

        # Calculate the joint position based on the angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        #end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        #end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)


        # Draw the arm: base -> joint -> end effector
        self.graph.draw_line((self.base_x, self.base_y), (joint_x, joint_y), width=5)
        self.graph.draw_line((joint_x, joint_y), (self.end_x, self.end_y), width=5)

        print(math.degrees(self.q1), math.degrees(self.q2))

    def update_end_effector_position(self):
        # Calculate the end effector's position based on the current angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        self.end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        self.end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)
