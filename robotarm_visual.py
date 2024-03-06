#!/usr/bin/env python3


import pygame
import numpy as np
import math
import json


class Arm2Link:
    def __init__(self, screen, len1, len2, base_x, base_y):
        self.screen = screen
        self.len1 = len1
        self.len2 = len2
        self.base_x = base_x
        self.base_y = base_y
        self.end_x = base_x
        self.end_y = base_y
        self.q1 = 0  # Angle of the first link
        self.q2 = 0  # Angle of the second link

        # Stepper motor angles moved per step:
        #   Nema 17 - 1.8 degrees
        self.q1_step_angle = 1.8
        self.q2_step_angle = 1.8

        self.q1_delta = 0 
        self.q2_delta = 0

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
        '''if(distance_to_endeff >= (self.len1 + self.len2)):
            self.end_x = old_x
            self.end_y = old_y
            return'''

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

    def push_movements(self, move_buffer):
        m1 = m2 = 0
        m1_dir = m2_dir = 0

        while((abs(self.q1_delta) >= self.q1_step_angle) or (abs(self.q2_delta) >= self.q2_step_angle)):

            if(abs(self.q1_delta) >= self.q1_step_angle):
                m1 = 1
                if(self.q1_delta < 0 ):
                    m1_dir = 0
                    self.q1_delta = self.q1_delta + self.q1_step_angle #add if q1 delta is negative to bring it to zero
                else: 
                    m2_dir = 1
                    self.q1_delta = self.q1_delta - self.q1_step_angle #subtract if q1 delta is negative to bring it to zer
            else:
                m1 = 0

            

            if(abs(self.q2_delta) >= self.q2_step_angle):
                m2 = 1
                if(self.q2_delta < 0 ):
                    m2_dir = 0
                    self.q2_delta = self.q2_delta + self.q2_step_angle #add if q1 delta is negative to bring it to zero
                else: 
                    m2_dir = 1
                    self.q2_delta = self.q2_delta - self.q2_step_angle #subtract if q1 delta is negative to bring it to zer
            else:
                m2 = 0

            packet = {
                "m1_tck": m1,
                "m2_tck": m2,
                "m1_dir": m1_dir,
                "m2_dir": m2_dir
            }

            # Convert the packet to a JSON string
            json_packet = json.dumps(packet)

            move_buffer.append(json_packet)
            print(json_packet)

    def draw_arm(self):
        # Draw base rectangle
        rect_width, rect_height = 100, 50
        pygame.draw.rect(self.screen, (200, 200, 200), (self.base_x - rect_width // 2, self.base_y, rect_width, rect_height))
        
        # Draw arm
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)
        pygame.draw.line(self.screen, (0, 0, 0), (self.base_x, self.base_y), (int(joint_x), int(joint_y)), 5)
        pygame.draw.line(self.screen, (0, 0, 0), (int(joint_x), int(joint_y)), (int(end_x), int(end_y)), 5)

    def update_end_effector_position(self):
        # Calculate the end effector's position based on the current angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        self.end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        self.end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)


def draw_base_rectangle(screen, width, height, border_thickness=2, color=(128, 128, 128)):

        # Calculate the top left corner of the rectangle
        rect_x = 500 - width // 2
        rect_y = 500 - height
        
        # Draw the rectangle
        pygame.draw.rect(screen, color, (rect_x, rect_y, width, height), border_thickness)


def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("Robot Arm Visualizer")
    clock = pygame.time.Clock()

    # Create a surface for drawing trails, matching the screen size. Use SRCALPHA for transparency.
    trail_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    arm = Arm2Link(screen, 400, 400, 500, 500)  # Initialize the arm

    prev_end_effector_pos = None  # Initialize the previous end effector position
    move_buffer = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = pygame.mouse.get_pos()
                target_x, target_y = mx - arm.base_x, my - arm.base_y
                arm.calculate_angles(target_x, target_y)
                arm.update_end_effector_position()  # You'll need to implement this

                arm.q1_delta = 50
                arm.q2_delta = 80

                arm.push_movements(move_buffer=move_buffer)


                # If there was a previous position, draw a line from it to the current position
                if prev_end_effector_pos is not None:
                    pygame.draw.line(trail_surface, (0, 0, 0), prev_end_effector_pos, (arm.end_x, arm.end_y), 2)
                prev_end_effector_pos = (arm.end_x, arm.end_y)

        screen.fill((255, 255, 255))  # Clear screen with white background
        screen.blit(trail_surface, (0, 0))  # Blit the trail surface onto the screen
        draw_base_rectangle(screen, 400, 300)
        arm.draw_arm()  # Draw the arm in its current configuration
        pygame.display.flip()  # Update the display
        clock.tick(60)  # Cap the framerate at 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()