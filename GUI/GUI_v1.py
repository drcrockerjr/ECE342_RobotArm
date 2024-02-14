##
# @file
# A graphical user interface for the GCode parser and computer vision modules

"""
    Program:    GUI_v1.py
    Author:     
    Date:       

    Description:
        Uses the PySimpleGUI library to create a Graphical User Interface
        for a Selective Compliance Assembly Robot Arm (SCARA).

        User can capture images using a webcam, load their own .png image,
        or load a .gcode file.

        Consists of two tabs:

        OpenCV parameters can be set in the OpenCV Settings tab.
"""

import PySimpleGUI as sg
#import cv2
import numpy as np
#from Deprecated import easycall as easycall
#from Vision import vision as vision
#import FTPInterface as ftp

import pygame
import numpy as np
import math

from Arm import Arm2Link


class DrawInteractive():
    def __init__(self, graph, arm):
        self.reading_movements = False
        self.saved_movements = []
        self.graph = graph
        self.arm = arm

    def clear_movements(self):
        self.saved_movements = []
    
    def add_point(self, x, y):
        self.saved_movements.append([x, y])
        print("Point added to Draw Interactive: ", x, y)

    def execute_picture(self):

        return self.saved_movements

        

def draw_base_rectangle(graph, width, height, border_thickness=2, color='gray'):

    # Calculate the top left corner of the rectangle
    rect_x = 500 - width // 2
    rect_y = 500 - height

    # Draw the rectangle
    graph.DrawRectangle((rect_x, rect_y), (rect_x + width, rect_y + height), line_color=color, line_width=border_thickness)


def execute_command():





# An unused test function to demonstrate functionality of the GUI.
def test_func(colorPalette, granularity, maxlines, papersize):
    print("Color: ",colorPalette, "Granularity: ", granularity, "maxlines: ", maxlines, "papersize: ", papersize)

# Prints to console when command is complete.
def reportDone():
    print("Command is done")

# Prints command to console that is being sent.
def reportSend(gcode):
    print("Command is being sent: {}".format(gcode))

# Prints whether the command was successful or not.
def reportSent(success, code):
    if success:
        print("Command {} is sent".format(code))
    else:
        print("Command {} send failed".format(code))

# GUI theme
# All default themes available at:
# https://user-images.githubusercontent.com/46163555/71361827-2a01b880-2562-11ea-9af8-2c264c02c3e8.jpg
sg.theme('BlueMono')

#cap = cv2.VideoCapture(0)       # select webcam input
recording = True                # Bool that tracks whether to read from webcam
final_img = None                # img to be sent to CV. Should be RGB numpy matrix
frame = None                    # image last captured from webcam
ret = None                      # Bool that indicates if image capture is successful
imgbytes = None                 # byte array of image
file_path = ""                  # File path in the file browser input box
height = 482                    # Default height of video capture
width = 642                     # Default width of video capture

com = 'COM4'                    # Serial Communication Port to send data over.
baud = 115200                   # baud rate to use

'''# Default OpenCV values:
color1 = int(0x0000ff)
color2 = int(0x00ff00)
color3 = int(0xff0000)
colorPalette = [(color1 >> 16,  color1 % (2**16) >> 8, color1 % (2**8)), (color2 >> 16, (color2 % (2**16)) >> 8,
                color2 % (2**8)), (color3 >> 16,  (color3 % (2**16)) >> 8, color3 % (2**8))]
'''

granularity = 1
maxLines = 100
paperSize = (279, 215)

# Main tab for selecting data to send
tab1 = [

        [sg.Text('Capture a webcam image, upload an image, or upload a GCode file.')],

        [sg.Text('Upload an image or GCode file:'), sg.Input(key='inputbox'),
         sg.FileBrowse(key='browse', file_types=(("Image Files", "*.png"),
                                                 ("GCode Files", "*.txt *.gcode *.mpt *.mpf *.nc")))],

        [sg.Text('Webcam output:', key='imgtext')],

        [sg.Image(filename='', key='image')],

        [sg.Text('Camera Controls:\t'),
         sg.Button('Capture Image', key='capimg'), sg.Button('Clear Image', key='retake', disabled=True)],

        [sg.Text("Send Output:\t"),
         sg.Button("Send Image", key="sendimg", disabled=True),
         sg.Button("Send GCode File", key="sendGcode", disabled=True)]
         
]

# Tab dedicated to manually entering drawbot commands.
tab2 = [
        [sg.Text('Enter drawing interactive parameters', key='db_text')],

        [sg.Text('Color Palette (6 digit hex)', size=(40, 1)),
            sg.Input(size=(13, 1), key='color1', default_text="0000FF"),
            sg.Input(size=(13, 1), key='color2', default_text="00FF00"),
            sg.Input(size=(13, 1), key='color3', default_text="FF0000")],

        [sg.Text('Granularity (float between 1 and 50)', size=(40, 1)),
            sg.Input(key='granularity', default_text="1")],

        [sg.Text('Max Lines (int between 1 and 1000)', size=(40, 1)), sg.Input(key='maxlines', default_text="100")],

        [sg.Text('Paper Size in mm (int in [10, 279], int in [10, 215])', size=(40, 1)),
            sg.Input(size=(21, 1), key='dim1', default_text="279"),
            sg.Input(size=(21, 1), key='dim2', default_text="215")],

        [sg.Button('Apply', key='apply')],
        [sg.Text('Robot Arm Visualization:')],
        [sg.Graph(canvas_size=(600, 400), graph_bottom_left=(0, 0), graph_top_right=(600, 400), background_color='white', key='-GRAPH-', enable_events=True, drag_submits=True)],
        [sg.Button('Start Reading', key='start-read')],
        [sg.Button('Process Contents', key='process-drawing')]

]

# Putting everything together into a single window.
layout = [
    [sg.TabGroup([[sg.Tab('Main Interface', tab1), sg.Tab('interactive Drawing', tab2)]])],
    [sg.Output(size=(80, 10), font='Verdana 10')],
    [sg.Button('Exit', key='exit')]
]

# Can only call this once. Opens a window.
window = sg.Window('Robot Arm Interface', layout, location=(200, 0))

graph = window['-GRAPH-']  # type: sg.Graph

arm = Arm2Link(graph, 200, 200, 500, 300)  # Initialize the arm with the graph element

draw_interactive = DrawInteractive(graph, arm)


# Continue looping forever.
while True:
    # Check for events, update values
    event, values = window.read(timeout=20)
    if event in (None, 'exit'):     # If window is closed or exit button pressed, close program.
        break
    elif event == '-GRAPH-':  # Check if the event is from the Graph element

        x, y = values['-GRAPH-']
        print('Mouse moved to:', x, y)

        if (x, y) == (None, None):  # Check if mouse is within the graph area
            continue

        #arm.calculate_angles(target_x, target_y)
        arm.calculate_angles(x, y)
        draw_base_rectangle(window['-GRAPH-'], 400, 300)
        arm.draw_arm()
        if draw_interactive.reading_movements == True: 
            draw_interactive.add_point(x, y)

    elif event == 'start-read': 
        x, y = values['-GRAPH-']
        draw_interactive.reading_movements = True
    
    elif event == 'process-drawing':
        #process drawing




# Close window when loop is broken.
window.close()
