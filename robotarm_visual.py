#!/usr/bin/env python3


import pygame
import numpy as np
import math


class Arm2Link:
    def __init__(self, screen, len1, len2, base_x, base_y):
        self.screen = screen
        self.len1 = len1
        self.len2 = len2
        self.base_x = base_x
        self.base_y = base_y
        self.q1 = 0  # Angle of the first link
        self.q2 = 0  # Angle of the second link

    def calculate_angles(self, end_x, end_y):
        # Convert end effector position to polar coordinates
        r = math.sqrt(end_x**2 + end_y**2)
        phi = math.atan2(end_y, end_x)
        # Using the cosine law to find the angles
        cos_q2 = (r**2 - self.len1**2 - self.len2**2) / (2 * self.len1 * self.len2)
        self.q2 = math.acos(cos_q2)  # Angle for the second link
        sin_q2 = math.sqrt(1 - cos_q2**2)
        self.q1 = phi - math.atan2((self.len2 * sin_q2), (self.len1 + self.len2 * cos_q2))  # Angle for the first link

    def draw_arm(self):
        # Calculate the joint position based on the angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)

        # Draw the arm: base -> joint -> end effector
        pygame.draw.line(self.screen, (0, 0, 0), (self.base_x, self.base_y), (joint_x, joint_y), 5)
        pygame.draw.line(self.screen, (0, 0, 0), (joint_x, joint_y), (end_x, end_y), 5)

        print(math.degrees(self.q1), math.degrees(self.q2))

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

    arm = Arm2Link(screen, 200, 200, 500, 500)  # Initialize the arm

    prev_end_effector_pos = None  # Initialize the previous end effector position

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