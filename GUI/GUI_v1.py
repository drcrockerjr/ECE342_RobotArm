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
import queue
import serial
import json
import threading
import time
import os
import cProfile
import os
from gCodeInt import process_file
from gCodeInt import process_movements

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
        super().__init__()
    def flush_to_serial(self, serial):
        while not self.empty():

            if serial.isOpen():
                p = self.get()
                # Concatenate a newline character to the message
                full_message = p + '\n'
                serial.write(full_message.encode('ascii'))
                serial.flush()

    # <----  Iter Protocol  ------>
    def __iter__(self):
        return self

    def __next__(self):
        try:
            if not self.empty():

                ret = self.get() # delete when not formating with newline

                return ret  # block=True | default
            else:
                raise StopIteration
        except ValueError:  # the Queue is closed
            raise StopIteration


def draw_centered_rectangle(graph, width, height, border_thickness=2, color='gray'):
    graph_width, graph_height = graph.get_size()

    # Calculate the top left corner of the rectangle
    rect_x = (graph_width - width) // 2
    rect_y = (graph_height - height) // 2

    # Draw the rectangle
    graph.DrawRectangle((rect_x, rect_y), (rect_x + width, rect_y + height), line_color=color, line_width=border_thickness)



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
file_path = ""                  # File path in the file browser input box


granularity = 1
maxLines = 100
paperSize = (279, 215)


# Main tab for selecting data to send
tab1 = [

        [sg.Text('Capture a webcam image, upload an image, or upload a GCode file.', key='img_text')],

        [sg.Text('Upload an image or GCode file:'), sg.Input(key='inputbox'),
            sg.FileBrowse(key='browse', file_types=(("Image Files", "*.png"),
                                                 ("GCode Files", "*.txt *.gcode *.mpt *.mpf *.nc")))],

        [sg.Text('Webcam output:', key='imgtext')],

        #[sg.Image(filename='', key='image')],

        [sg.Text('Camera Controls:\t'),
         sg.Button('Capture Image', key='capimg'), sg.Button('Clear Image', key='retake', disabled=True)],

        [sg.Text("Send Output:\t"),
         sg.Button("Send Image", key="sendimg", disabled=True),
         sg.Button("Send GCode File", key="sendGcode", disabled=False)]
         
]

# Tab dedicated to manually entering drawbot commands.
tab2 = [
        [sg.Text('Enter drawing interactive parameters', key='db_text')],

        [sg.Text('Granularity (float between 1 and 50)', size=(40, 1), key='gran_txt'),
            sg.Input(key='granularity', default_text="1")],

        [sg.Button('Apply', key='apply')],
        [sg.Text('Robot Arm Visualization:', key='visual_txt')],
        [sg.Button('Calibrate', key='calibrate')],
        [sg.Button('Zero', key='zero')],

        [sg.Graph(canvas_size=(600, 400), graph_bottom_left=(0, 0), graph_top_right=(600, 400), background_color='white', key='-GRAPH-', enable_events=True, drag_submits=True)],

        #[sg.Multiline(list(move_buffer), key='-QUE_TEXT-', size=(20, 5), disabled=True)],

        [sg.Button('Start Reading', key='start-read')],
        [sg.Button('Connect to Serial', key='connect_serial')]

]

# Putting everything together into a single window.
layout = [
    [sg.TabGroup([[sg.Tab('Main Interface', tab1), sg.Tab('interactive Drawing', tab2)]])],
    #[sg.TabGroup([[ sg.Tab('interactive Drawing', tab2)]])],
    [sg.Output(size=(80, 10), font='Verdana 10')],
    [sg.Button('Exit', key='exit')]
]

#Serial Configuarations

#MacOS example
com = '/dev/tty.usbmodem14101'  # Serial Communication Port to send data over (example for macOS).

#Windows Example
#com = 'COM4'                    # Serial Communication Port to send data over.

baud = 9600                   # baud rate to use


arm = Arm2Link( 142.875, 173.355, 300, 25, 1.8, 1.8)  # Initialize the arm with the graph element

move_buffer = MoveBuffer()

arduino_serial = None

# Can only call this once. Opens a window.
window = sg.Window('Robot Arm Interface', layout, location=(200, 0), finalize=True)

graph = window['-GRAPH-']  # type: sg.Graph

last_mouse_event = 0
current_mouse_event = 0

# Continue looping forever.
while True:
    # Check for events, update values
    event, values = window.read(timeout=0)
    if event in (None, 'exit'):     # If window is closed or exit button pressed, close program.
        break
    elif event == '-GRAPH-':  # Check if the event is from the Graph element
        

        x, y = values['-GRAPH-']

        if (x, y) == (None, None):  # Check if mouse is within the graph area
            continue
            
        if 0 <= x <= 600 and 0 <= y <= 400:  # Replace graph_width and graph_height with the actual dimensions of your graph
            current_mouse_event = time.time() * 1000 # ms measurement of time when mouse event occurs

            #debouncing multiple mouse events
            if(current_mouse_event - last_mouse_event >= 200):
                graph.erase()

                arm.calculate_drawing_angles(graph, x, y)

                draw_centered_rectangle(graph, 400, 300)
                arm.draw_arm(graph)
                #print("\n\n Serial Flushed \n\n ")

                arm.calculate_angles_V2(graph, x, y, move_buffer)

                try:
                    move_buffer.flush_to_serial(serial=arduino_serial)
                    print("\n Flushed to Arduino \n")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

                last_mouse_event = time.time() * 1000
    
    elif event == 'connect_serial':
        try:
            arduino_serial = serial.Serial(com, baud,
                                        timeout=None,
                                        #parity=serial.PARITY_NONE,
                                        bytesize=serial.EIGHTBITS,
                                        #stopbits=serial.STOPBITS_ONE
                                        )
            print("sSerial port opened successfully")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    elif event == 'sendGcode':
        target_coords = []
        try:
            file_path = values['browse']

            print(f'Sending G-code file {file_path} ...')

            if os.path.exists(file_path):
                process_file(file_path, arm.end_x, arm.end_y, target_coords)
            else: 
                print(f"File not found: {file_path}")

        except Exception as e:
            print(f"Error occured: {e}")

        for coord in target_coords: 

            try:
                x, y = coord
                arm.calculate_angles_V2(graph, x, y, move_buffer)

                move_buffer.flush_to_serial(serial=arduino_serial)
                print("\n Flushed to Arduino \n")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
    
    elif event == 'calibrate':
        arm.calibrate()

    elif event == 'zero':
        arm.move_to_zero(graph, move_buffer)


# Close window when loop is broken.
window.close()

if __name__ == "__main__": 
    main()
