##
# @file
# A simulation for the multiple inverse kinematics solutions of
# the SCARA topology
#
"""
File:   Inverse_Kinematics.py
Description: A simulation for the SCARA inverse kinematics problem.
Author:     Thomas Snyder
Date:       2/5/2020
"""
import numpy as np
import matplotlib as mpt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from enum import Enum

class methodIK(Enum):
    JACOBIAN_PS = 0
    FABRIK = 1
    JACOBIAN_INV = 2
    GEOMETRIC = 3

LOGFILE = open("./ThetasForPositions.csv", "w")
LOGFILE.write("x,y,th1,th2\n")

SIMULATE = True 
METHOD = methodIK.GEOMETRIC

fig, ax = plt.subplots()
line, = ax.plot([], [], 'bo-', linewidth=2, markersize=12)
ax.grid()
xdata, ydata = [], []

CONVERSION=(2**14)/22
INCHES=True

class SCARA_IK:
    """
    A class to calculate the inverse kinematics of an N-link SCARA robot
    For an N-link robot, there are N joints
    """

    def __init__(self, joint_len):
        """
        joint_len: List of doubles. The double at index i represents the length of link i
        Assume: starting angle is 0 degrees for all angles
        """
        if INCHES == False:
            joint_len = [len * CONVERSION for len in joint_len]

        self.joint_lengths = joint_len

        self.joint_pos = [np.array([0,0])] # First joint is always at origin 0,0
        self.joint_ang = []


        for i in range(len(joint_len)):
            if i == 0:
                x = joint_len[i]
            else:
                x = joint_len[i] + joint_len[i-1]
                # print(self.joint_pos[i-1])
            # All joints start in pure positive x position
            y = 0
            ang = np.pi / 4
            self.joint_pos.append(np.array([x, y]))
            self.joint_ang.append(ang)

        self.calc_joint_pos()
        # self.draw()
        print(self.joint_ang)

        print(self.effector_pos())
        self.length_max = 0
        for x in self.joint_lengths:
            self.length_max += x


        self.target = None
        self.target_dist = None
        self.target_tolerance = 0.1
        
        # For animation
        self.arm_path_sim = []
        self.anim_iter = 0
        self.anim_iter_max = 0


        
    
    def plan_path(self, delta = 0.1):
        """ Path planning function that takes the amount of change between points
        on the path
        
        Args:
            delta(float): norm distance between path points

        Returns:
            list of tuples. The returned list::

                A list of tuples that describes the path in x and y
                coordinates whose norm distance from the previous
                coordinate is less than the delta argument provided.
        """
        if INCHES == False:
            delta = delta * CONVERSION
        (curr_x, curr_y) = self.effector_pos()
        # print("Current Position: {},{}".format(curr_x, curr_y))
        targ_x = self.target[0]
        targ_y = self.target[1]
        # print("Target Position: {}, {}".format(targ_x, targ_y))
        
        dx = targ_x - curr_x
        dy = targ_y - curr_y
        # print("dx: {}, dy: {}".format(dx, dy))
        if np.abs(dx) > np.abs(dy):
            steps = (int)(np.floor(np.abs(dx) / delta))
        else:
            steps = (int)(np.floor(np.abs(dy) / delta))

        # print("Number of steps: {}".format(steps))
        step_sz_x = dx / steps
        step_sz_y = dy / steps

        xpath = [(x * step_sz_x) + curr_x for x in range(1, steps)]
        ypath = [(y * step_sz_y) + curr_y for y in range(1, steps)]

        path = list(zip(xpath, ypath))
        path.append(self.target)
        print(path)
        return path
        


    def set_target(self, x, y):
        # if INCHES == False:
        #     x = x * CONVERSION
        #     y = y * CONVERSION

        if np.sqrt(x**2 + y**2) > self.max_len():
            raise Exception("Target out of reach")
        else:
            self.target = (x, y)
            self.target_dist = np.sqrt(x**2 + y**2)
        

    def linear_spline(self, last, first, step_size):

        slope = (last[1] - first[1]) / (last[0] - first[0])
        yint = last[1] - (last[0] * slope)
        line_len = (last[0] - first[0]) / step_size
        
        line = []
        print(step_size)
        print(first)
        print(last)
        print(np.arange(first[0], last[0], step_size))
        for i in np.arange(first[0], last[0], step_size):
            line.append((slope * i) + yint)

        return line


    def geometric_method_proof_of_concept(self):
        """
        x = l1 cos(th1) + l2 cos(th1 + th2)
        y = l1 sin(th1) + l2 sin(th1 + th2)
        x^2 + y^2 = l1^2 + l_2^2 + 2 l1 l2 cos(th2)


        cos(th2) = (x^2 + y^2 - l1^2 - l2^2) / 2l1l2
        sin(th2) = +/- sqrt(1-cos^2(th2))
        th2 = Atan2(sin(th2), cos(th2)) NOTE: Sign of sin(th2) determines 
                                            manipulator elbow-up (+) or 
                                            elbow-down (-)
        
        k1 = l1 + l2 cos(th2)
        k2 = l2 * sin(th2)

        gamma = Atan2(k2, k1)

        th1 = Atan2(y, x) - Atan2(k2, k1)
        """
        (x, y) = self.effector_pos()

        print(self.target[0])
        print(self.target[1])
        
        print(self.joint_lengths[0])
        print(self.joint_lengths[1])
        costh2 = ((self.target[0] ** 2) + (self.target[1] ** 2) - (self.joint_lengths[0] ** 2) - (self.joint_lengths[1] ** 2)) / (2 * self.joint_lengths[0] * self.joint_lengths[1])
        sinth2 = np.sqrt(1 - (costh2 ** 2))
        th2 = np.arctan2(sinth2, costh2)
        print("CosTh2: {}".format(costh2))
        print("SinTh2: {}".format(sinth2))
        k1 = self.joint_lengths[0] + self.joint_lengths[1] * costh2
        k2 = self.joint_lengths[1] * sinth2
        print("len2: {}".format(self.joint_lengths[1]))
        print("k1: {}, k2: {}".format(k1, k2))
        gamma = np.arctan2(k2, k1)
        th1 = np.arctan2(self.target[1], self.target[0]) - gamma
        print("Gamma: {}".format(gamma))
        print("Arctan xy: {}".format(th1 + gamma))
        print("Joint Steps: 1: {} 2: {}".format((th1 - self.joint_ang[0]) * 31.8310155049, (th2-self.joint_ang[1]) * 31.8310155049))
        self.joint_ang[0] = th1
        self.joint_ang[1] = th2
        print("Joint Angles: {}, {}".format(th1, th2))
        LOGFILE.write("{},{},{},{}\n".format(self.target[0], self.target[1], th1, th2))
        
        self.calc_joint_pos()
 

    def geometric_method(self):
        """
        x = l1 cos(th1) + l2 cos(th1 + th2)
        y = l1 sin(th1) + l2 sin(th1 + th2)
        x^2 + y^2 = l1^2 + l_2^2 + 2 l1 l2 cos(th2)


        cos(th2) = (x^2 + y^2 - l1^2 - l2^2) / 2l1l2
        sin(th2) = +/- sqrt(1-cos^2(th2))
        th2 = Atan2(sin(th2), cos(th2)) NOTE: Sign of sin(th2) determines 
                                            manipulator elbow-up (+) or 
                                            elbow-down (-)
        
        k1 = l1 + l2 cos(th2)
        k2 = l2 * sin(th2)

        gamma = Atan2(k2, k1)

        th1 = Atan2(y, x) - Atan2(k2, k1)
        """
        (x, y) = self.effector_pos()

        print(self.target[0])
        print(self.target[1])
        
        print(self.joint_lengths[0])
        print(self.joint_lengths[1])
        costh2 = ((self.target[0] ** 2) + (self.target[1] ** 2) - (self.joint_lengths[0] ** 2) - (self.joint_lengths[1] ** 2)) / (2 * self.joint_lengths[0] * self.joint_lengths[1])
        sinth2 = np.sqrt(1 - (costh2 ** 2))
        th2 = np.arctan2(sinth2, costh2)
        print("CosTh2: {}".format(costh2))
        print("SinTh2: {}".format(sinth2))
        k1 = self.joint_lengths[0] + self.joint_lengths[1] * costh2
        k2 = self.joint_lengths[1] * sinth2
        print("len2: {}".format(self.joint_lengths[1]))
        print("k1: {}, k2: {}".format(k1, k2))
        gamma = np.arctan2(k2, k1)
        th1 = np.arctan2(self.target[1], self.target[0]) - gamma
        print("Gamma: {}".format(gamma))
        print("Arctan xy: {}".format(th1 + gamma))
        print("Joint Steps: 1: {} 2: {}".format((th1 - self.joint_ang[0]) * 31.8310155049, (th2-self.joint_ang[1]) * 31.8310155049))
        diff1 = th1 - self.joint_ang[0]
        diff2 = th2 - self.joint_ang[1]
        
        # self.joint_ang[0] = th1
        # self.joint_ang[1] = th2
        # self.calc_joint_pos()
        # self.draw()

        steps1 = 31.8310155049 * diff1
        steps2 = 31.8310155049 * diff2
        dir1 = steps1 / abs(steps1)
        dir2 = steps2 / abs(steps2)
        print("Direction 1: {}, 2: {}".format(dir1, dir2))
        steps1 = abs(steps1)
        steps2 = abs(steps2)

        diffX = self.target[0] - x
        diffY = self.target[1] - y


        # for interpolating and mirroroing after the for loop
        xInc = diffX / (max(int(steps1), int(steps2)))
        yInc = diffY / (max(int(steps1), int(steps2)))


        print("Starting Joint 1:{}, 2:".format(self.joint_ang[0], self.joint_ang[1]))
        print("Target: {}, {}".format(th1, th2))
        for i in range(max(int(steps1), int(steps2))):
            if(steps1 > 0):
                self.joint_ang[0] += dir1 * 1.8 * np.pi / 180
                steps1 -= 1
            if(steps2 > 0):
                self.joint_ang[1] += dir2 * 1.8 * np.pi / 180
                steps2 -= 1
            self.calc_joint_pos()
            self.arm_path_sim.append((self.joint_pos[2][0], self.joint_pos[2][1]))


        mapped_path = [( -2 * (actual[0] - (xInc * i + x)) + actual[0] ,  -2 * (actual[1] - (yInc * i + y)) + actual[1]) for i, actual in enumerate(self.arm_path_sim)]
        # mapped_path = [((2 * (actual[0] - (xInc * i)) + actual[0]), (2 * (actual[1] - (yInc * i)) + actual[1])) for i, actual in enumerate(self.arm_path_sim)]

        ypoints = [point[1] for point in mapped_path]
        xpoints = [point[0] for point in mapped_path]
        xline = [(x + (i * xInc)) for i in range(len(self.arm_path_sim))]
        yline = [y + (i * yInc) for i in range(len(self.arm_path_sim))]

        

        print(mapped_path)

        # plt.plot(xpoints, ypoints)
        # plt.plot(xline, yline)
        # plt.show()

        print("End point: {},{}".format(self.joint_ang[0], self.joint_ang[1]))
        # self.joint_ang[0] = th1
        # self.joint_ang[1] = th2
        print("Joint Angles: {}, {}".format(th1, th2))
        LOGFILE.write("{},{},{},{}\n".format(self.target[0], self.target[1], th1, th2))

        

        self.calc_joint_pos()

        return mapped_path
            

    

    def get_joint_trajectory(self):
        """ Returns a list of tuples describing the actual path of the end effector between 
        """
        return self.arm_path_sim

    def jacobian_inverse_method(self):
        # print("Getting x and y position")
        (x, y) = self.effector_pos()

        # Assuming target is small enough
        dx = self.target[0] - x
        dy = self.target[1] - y

        # Set the distance from current to target position
        # We'll recalculate this every iteration and break our
        # loop once it is less than a tolerance
        self.target_dist = np.sqrt(dx**2 + dy**2)
        i = 0

        while(self.target_dist > self.target_tolerance):
            i += 1

            # Form the Jacobian by calculating the partial derivatives
            df1dth1 = -self.joint_lengths[0] * np.sin(self.joint_ang[0]) - self.joint_lengths[1] * np.sin(self.joint_ang[0] + self.joint_ang[1])
            df1dth2 = -self.joint_lengths[1] * np.sin(self.joint_ang[0] + self.joint_ang[1])
            df2dth1 = self.joint_lengths[0] * np.cos(self.joint_ang[0]) + self.joint_lengths[1] * np.cos(self.joint_ang[0] + self.joint_ang[1])
            df2dth2 = self.joint_lengths[1] * np.cos(self.joint_ang[0] + self.joint_ang[1])


            # Compose the jacobian
            J = np.matrix([[df1dth1, df1dth2], [df2dth1, df2dth2]])
           
            # Invert the jacobian
            J_inv = J.I

            # Build the change in position matrix
            dxhat = np.matrix([[dx], [dy]])

            # Multiply jacobian out by the change in x and y
            dthhat =  np.matmul(J_inv, dxhat)

            # Update the angles that the joints should be at
            # print("Change in thetas: {}".format(dthhat))
            self.joint_ang[0] += dthhat.A[0][0]
            self.joint_ang[1] += dthhat.A[1][0]

            # Recompute where we're at            
            self.calc_joint_pos()
            (x, y) = self.effector_pos()
            dx = self.target[0] - x
            dy = self.target[1] - y
            self.target_dist = np.sqrt(dx**2 + dy**2)
        #     print("\rIteration {}, Target Distance: {}".format(i, self.target_dist), end=" ")
        # print("Iteration {}, Target Distance: {}".format(i, self.target_dist))
        print("Joint angles are now {}".format(self.joint_ang))
        print("Change in thetas:\n\tdelta theta1: {} degrees\n\tdelta theta2: {} degrees\n".format(dthhat[0][0] * 180 / np.pi,dthhat[1][0] * 180 / np.pi))
        print("Converted to steps:\n\tdelta theta1: {} steps\n\tdelta theta2: {} steps\n".format(dthhat[0][0] * 180 / np.pi / 1.8, dthhat[1][0] * 180 / np.pi / 1.8))
        self.target_dist = 1000

   
    def jacobian_pseudoinverse_method(self):
        (x,y) = self.effector_pos()

        dx = self.target[0] - x
        dy = self.target[1] - y
        self.target_dist = np.sqrt(dx ** 2 + dy ** 2)
        iters = 0
        while(self.target_dist > self.target_tolerance):
            # if iters > 2000:
                # break

            # print("Iteration {}".format(iters))
            # iters += 1
            # step = 0.01
            # line = self.linear_spline(self.target, self.effector_pos(), step)
            # print("Line {}".format(line))
            # for i in range(len(line)):
            #     (x, y) = self.effector_pos()
            #     print("Effector Position: {}, {}".format(x, y))
            #     dx = self.target[0] + (i * step) - x
            #     dy = self.target[1] + line[i] - y
            # print("Calculating the partials")
            # Partial derivatives of the forward kinematics equations for the jacobian
            df1dth1 = -self.joint_lengths[0] * np.sin(self.joint_ang[0]) - self.joint_lengths[1] * np.sin(self.joint_ang[0] + self.joint_ang[1])
            df1dth2 = -self.joint_lengths[1] * np.sin(self.joint_ang[0] + self.joint_ang[1])
            df2dth1 = self.joint_lengths[0] * np.cos(self.joint_ang[0]) + self.joint_lengths[1] * np.cos(self.joint_ang[0] + self.joint_ang[1])
            df2dth2 = self.joint_lengths[1] * np.cos(self.joint_ang[0] + self.joint_ang[1])

            
            # Find the determinant
            det_j = (np.square(df1dth1) + np.square(df1dth2)) * (np.square(df2dth1) + np.square(df2dth2))
            det_j -= ((df2dth1 * df1dth1) + (df2dth2 * df1dth2)) * ((df1dth1 * df2dth1) + (df1dth2 * df2dth2))


            # Find the Jacobian
            if det_j != 0.0:
                a = ((df1dth1 * (np.square(df2dth1) + np.square(df2dth2))) + (df2dth1 * ((-df2dth1 * df1dth1) - (df2dth2 * df1dth2)))) / det_j
                b = ((df1dth1 * (-(df1dth1 * df2dth1) - (df1dth2 * df2dth2))) + (df2dth1 * ((np.square(df1dth1) + np.square(df1dth2))))) / det_j
                c = ((df1dth2 * (np.square(df2dth1) + np.square(df2dth2))) + (df2dth2 * (-(df2dth1 * df1dth1) - (df2dth2 * df1dth2)))) / det_j
                d = ((df1dth2 * (-(df1dth1 * df2dth1) - (df1dth2 * df2dth2))) + (df2dth2 * (np.square(df1dth1) + np.square(df1dth2)))) / det_j
            else:
                a = 0 
                b = 0
                c = 0
                d = 0

            # Multiply the jacobian through the x and y
            # Jacobian:
            #   --         -- --    -- 
            #   |   a   b   | |  dx  |
            #   |   c   d   | |  dy  |
            #   --         -- --    --
            th1 = a * dx + b * dy
            th2 = c * dx + d * dy


            # add change to current angles
            self.joint_ang[0] = self.joint_ang[0] + th1
            self.joint_ang[1] = self.joint_ang[1] + th2

            self.calc_joint_pos()
            (x, y) = self.effector_pos()
            dx = self.target[0] - x
            dy = self.target[1] - y
            self.target_dist = np.sqrt(dx ** 2 + dy ** 2)
      
        self.target_dist = 300



    def calc_joint_pos(self):
        joint_pos = []
        joint_pos.append(np.array((0,0)))
        x1 = self.joint_lengths[0] * np.cos(self.joint_ang[0])
        y1 = self.joint_lengths[0] * np.sin(self.joint_ang[0])
        (x2, y2) = self.effector_pos()
        joint_pos.append(np.array((x1, y1)))
        joint_pos.append(np.array((x2, y2)))
        self.joint_pos = joint_pos


    def FABRIK_method(self):
        if self.target_dist > self.length_max:
            print("Target distance is larger than max reach")
            raise Exception("Error: Target is out of reach")
        else:
            p_0 = self.joint_pos[0] # Set inital origin
            e_pos = np.array(self.effector_pos())

            t = np.array(self.target)
            
            joint_pos_temp = self.joint_pos

            dif_a = np.linalg.norm(t-e_pos)

            while dif_a > self.target_tolerance:
                # Move from the effector to the base: Forward reaching
                joint_pos_temp[len(joint_pos_temp)-1] = self.target

                for i in reversed(range(len(joint_pos_temp)-1)):
                    r_i = np.linalg.norm(joint_pos_temp[i] - joint_pos_temp[i+1])
                    # if(r_i == 0):
                    lambda_i = float(self.joint_lengths[i]) / float(r_i)
                    # print("1. Joint number {} at {}".format(i, joint_pos_temp[i]))
                    joint_pos_temp[i] = np.multiply((1-lambda_i),joint_pos_temp[i+1]) + np.multiply(lambda_i,joint_pos_temp[i])
                    # print("2. Joint number {} at {}".format(i, joint_pos_temp[i]))

                # Backward reaching
                # set the initial position of root back
                joint_pos_temp[0] = p_0
                for i in range(len(joint_pos_temp)-1):
                    r_i = np.linalg.norm(joint_pos_temp[i+1] - joint_pos_temp[i])
                    # if(r_i == 0):
                    lambda_i = float(self.joint_lengths[i]) / float(r_i)
                    joint_pos_temp[i+1] = np.multiply((1-lambda_i), joint_pos_temp[i]) + np.multiply(lambda_i, joint_pos_temp[i+1])
                    # print("Joint number {} at {}".format(i+1, joint_pos_temp[i+1]))
                dif_a = (np.linalg.norm(t - joint_pos_temp[len(joint_pos_temp)-1]))
                # print("Difference: {}".format(dif_a))

            

            #Set the positions and calculate the angles
            self.joint_pos = joint_pos_temp
            self.calc_angles()                    


    def check_position_viability(self):
        (x, y) = self.effector_pos()
        length = np.sqrt(x**2 + y**2)
        if length < 10.95 or length > 11.05:
            print("ERROR: Not a viable solution.") 




    def effector_pos(self):
        x = 0
        y = 0
        x = self.joint_lengths[0] * np.cos(self.joint_ang[0]) + self.joint_lengths[1] * np.cos(self.joint_ang[0] + self.joint_ang[1])
        y = self.joint_lengths[0] * np.sin(self.joint_ang[0]) + self.joint_lengths[1] * np.sin(self.joint_ang[0] + self.joint_ang[1])
        
        return (x, y)


    def run(self):
        if self.target is None:
            raise Exception("Error: No target has been set")
        self.anim_iter = 0
        # algorithms = {
        #     methodIK.JACOBIAN_PS: self.jacobian_pseudoinverse_method,
        #     methodIK.FABRIK: self.FABRIK_method,
        # }

        # algorithms[method]
        if METHOD == methodIK.JACOBIAN_PS and SIMULATE == True:
            print("")
            self.arm_path_sim.append(self.joint_pos)
            path = self.plan_path()
            for t in path:
                print("Moving to {}".format(t))
                self.target = t
                self.jacobian_pseudoinverse_method()
                self.arm_path_sim.append(self.joint_pos)

            self.anim_iter_max = len(self.arm_path_sim)

        elif METHOD == methodIK.FABRIK:
            self.FABRIK_method()
        
        elif METHOD == methodIK.JACOBIAN_INV and SIMULATE == True:
            # Start the simulator animation at the current position
            self.arm_path_sim.append(self.joint_pos)
            path = self.plan_path() # Plan path between current and target. Assumes target is set
            for t in path:
                print("Moving to {}".format(t))
                # Move to the target
                self.target = t
                # print("Target set... Calculating angles")
                self.jacobian_inverse_method()
                self.arm_path_sim.append(self.joint_pos)
                print("Moved to {}".format(t))
        elif METHOD == methodIK.GEOMETRIC and SIMULATE == True:
            self.geometric_method() # plots the points and populates the array

        elif METHOD == methodIK.GEOMETRIC_POC and SIMULATE == True:
            
            self.arm_path_sim.append(self.joint_pos)
            path = self.plan_path()
            for t in path:
                print("Moving to {}".format(t))
                self.target = t
                self.geometric_method_proof_of_concept()
                print(self.joint_pos)
                self.arm_path_sim.append(self.joint_pos)
            # print("End Goal: {}".format(robot.target))
        # self.check_position_viability()
        elif METHOD == methodIK.GEOMETRIC and SIMULATE == False:
            self.geometric_method()

        # self.draw()


    def draw(self):
        x_pos = [x[0] for x in self.joint_pos]
        y_pos = [y[1] for y in self.joint_pos]
        plt.plot(x_pos, y_pos, 'bo--', linewidth=2, markersize=12)
        plt.xlim((-6, 15))
        plt.ylim((-6, 15))
        plt.show()
        

    def calc_angles(self):
         for i in range(1, len(self.joint_pos)):
            if i == 1:
                self.joint_ang[i-1] = np.arctan2(self.joint_pos[i][1], self.joint_pos[i][0])
            else:
                self.joint_ang[i-1] = np.arctan2(self.joint_pos[i][1], self.joint_pos[i][0]) - self.joint_ang[i-2]

           
    def max_len(self) -> float:
        return self.length_max


    def angles(self):
        return self.joint_ang


    def pos(self):
        return self.joint_pos


### ANIMATION FUNCTIONS ###
    def playback(self):
        for arm_pos in self.arm_path_sim:
            # print("Returning {}, {}".format(x, y))
            yield arm_pos


def init_animation():
    del xdata[:]
    del ydata[:]
    if INCHES == False:
        ax.set_ylim(-6 * CONVERSION, 11 * CONVERSION)
        ax.set_xlim(-6 * CONVERSION, 11 * CONVERSION)
    else:
        ax.set_ylim(-15, 15)
        ax.set_xlim(-15, 15)
    line.set_data(xdata, ydata)
    return line,

    # (x, y) = self.arm_path_sim[self.anim_iter]
    # self.anim_iter += 1

def animate(data):
    xdata = list()
    ydata = list()
    
    # print("{}, {}".format(x, y))
    xdata = [x for (x, y) in data]
    ydata = [y for (x, y) in data]

    line.set_data(xdata, ydata)
    return line, 


def animate_geometric(data):
    xdata.append(data[0])
    ydata.append(data[1])
    line.set_data(xdata, ydata)
    return line, 

if __name__ == '__main__':
    robot = SCARA_IK([5.55, 9.25])

    print("Maximum stretch: {}".format(robot.max_len()))
    print("Current joint angles: {}".format(robot.angles()))
    print("Current joint pos: {}".format(robot.pos()))

    try:
        print("Setting target")
        # robot.set_target(2904, 9830)
        # robot.set_target(4.9, 13.2)
        # print("Running math")
        # robot.run()
        # robot.set_target(5.9, 13.2)
        # robot.run()
        # robot.set_target(5.9, 12.2)
        # robot.run()
        # robot.set_target(4, 12.9)
        # robot.run()
        robot.set_target(6, 4)
        robot.geometric_method()
        # robot.run()
        # robot.set_target(4, 5)
        # robot.run()



        print("Joint Angles:")
        print(robot.angles)
        # robot.set_target(1, 1)
        # robot.run()
        #robot.set_target(3, 9)
        #robot.run()
        #robot.set_target(5,7)
        #robot.run()
        #robot.set_target(1,1)
        #robot.run()
        if SIMULATE == True:
            animate = animation.FuncAnimation(fig, animate_geometric, robot.playback, blit=False, interval=1, repeat=False, init_func=init_animation)
            # animate = animation.FuncAnimation(fig, animate_geometric, robot.playback, blit=False, interval=1, repeat=True, init_func=init_animation)
    except Exception as ex:
        print(ex)

    # robot.set_target(1, 8)
    # robot.run(methodIK.FABRIK)
    # animate = animation.FuncAnimation(fig, animate, robot.playback, blit=False, interval=40, repeat=False, init_func=init_animation)


    
    plt.title('SCARA Simulator')
    plt.show()
    print("Current joint angles: {}".format(robot.angles()))
    print("Current joint pos: {}".format(robot.pos()))