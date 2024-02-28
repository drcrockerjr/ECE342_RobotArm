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

#import pygame
import numpy as np
import math
import queue
import serial
import json
import threading

from Arm import Arm2Link


class DrawInteractive():
    def __init__(self, graph, arm):
        self.reading_movements = False
        self.saved_movements = []
        self.graph = graph
        self.arm = arm

    
    def add_point(self, x, y):
        self.saved_movements.append([x, y])
        #print("Point added to Draw Interactive: ", x, y)

    def execute_picture(self):

        return self.saved_movements
    

class MoveBuffer(queue.Queue):
    def __init__(self):
        super.__init__(maxsize=400)



#def write_buffer_serial(serial, buffer):  
#    for json_packet in buffer: 
#        serial.write(json_packet.encode())
#
#    buffer.clear() #clear buffer when movements have been pushed ot arduino


def draw_base_rectangle(graph, width, height, border_thickness=2, color='gray'):

    # Calculate the top left corner of the rectangle
    rect_x = 500 - width // 2
    rect_y = 500 - height

    # Draw the rectangle
    graph.DrawRectangle((rect_x, rect_y), (rect_x + width, rect_y + height), line_color=color, line_width=border_thickness)


#def execute_command():

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


def push_movements(move_buf, q1_delta, q2_delta, q1_stp_angle, q2_stp_angle):
        m1 = m2 = 0
        m1_dir = m2_dir = 0

        while((abs(q1_delta) >= q1_stp_angle) or (abs(q2_delta) >= q2_stp_angle)):

            if(abs(q1_delta) >= q1_stp_angle):
                m1 = 1
                if(q1_delta < 0 ):
                    m1_dir = 0
                    q1_delta = q1_delta + q1_stp_angle #add if q1 delta is negative to bring it to zero
                else: 
                    m2_dir = 1
                    q1_delta = q1_delta - q1_stp_angle #subtract if q1 delta is negative to bring it to zer
            else:
                m1 = 0

            if(abs(q2_delta) >= q2_stp_angle):
                m2 = 1
                if(q2_delta < 0 ):
                    m2_dir = 0
                    q2_delta = q2_delta + q2_stp_angle #add if q1 delta is negative to bring it to zero
                else: 
                    m2_dir = 1
                    q2_delta = q2_delta - q2_stp_angle #subtract if q1 delta is negative to bring it to zer
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

            move_buf.put(json_packet)
            print(json_packet)

# GUI theme
# All default themes available at:
# https://user-images.githubusercontent.com/46163555/71361827-2a01b880-2562-11ea-9af8-2c264c02c3e8.jpg
sg.theme('BlueMono')

#cap = cv2.VideoCapture(0)       # select webcam input
file_path = ""                  # File path in the file browser input box

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

        #[sg.Text('Upload an image or GCode file:'), sg.Input(key='inputbox'),
        # sg.FileBrowse(key='browse', file_types=(("Image Files", "*.png"),
        #                                         ("GCode Files", "*.txt *.gcode *.mpt *.mpf *.nc")))],

        [sg.Text('Webcam output:', key='imgtext')],

        #[sg.Image(filename='', key='image')],

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
    #[sg.TabGroup([[ sg.Tab('interactive Drawing', tab2)]])],
    [sg.Output(size=(80, 10), font='Verdana 10')],
    [sg.Button('Exit', key='exit')]
]

#Serial Configuarations
com = 'COM4'                    # Serial Communication Port to send data over.
baud = 115200                   # baud rate to use

'''serial = serial.Serial(com, baud,
                       timeout=2.5,
                       parity=serial.PARITY_NONE,
                       bytesize=serial.EIGHTBITS,
                       stopbits=serial.STOPBITS_ONE
                       )'''



# Can only call this once. Opens a window.
window = sg.Window('Robot Arm Interface', layout, location=(200, 0), finalize=True)

graph = window['-GRAPH-']  # type: sg.Graph

arm = Arm2Link( 200, 200, 500, 300, 1.8, 1.8)  # Initialize the arm with the graph element

#move_buffer = MoveBuffer()

#draw_interactive = DrawInteractive(graph, arm)


# Continue looping forever.
while True:
    # Check for events, update values
    event, values = window.read(timeout=40)
    if event in (None, 'exit'):     # If window is closed or exit button pressed, close program.
        break
    elif event == '-GRAPH-':  # Check if the event is from the Graph element
        x, y = values['-GRAPH-']
        if (x, y) == (None, None):  # Check if mouse is within the graph area
            continue
        if 0 <= x <= 400 and 0 <= y <= 600:  # Replace graph_width and graph_height with the actual dimensions of your graph
            arm.calculate_angles(x, y)
            #x = threading.Thread(target=push_movements, args=(move_buffer, arm.q1_delta, arm.q2_delta, arm.q1_step_angle, arm.q2_step_angle))
            #x.start()

            draw_base_rectangle(graph, 400, 300)
            arm.draw_arm(graph)

            #arm.push_movements(move_buffer) # error is in push movement function
        #write_buffer_serial(serial, move_buffer)

    #elif event == 'start-read': 
    #    x, y = values['-GRAPH-']
    #    draw_interactive.reading_movements = True
    
    #elif event == 'process-drawing':
        #process drawing'''

    

# Close window when loop is broken.
window.close()
