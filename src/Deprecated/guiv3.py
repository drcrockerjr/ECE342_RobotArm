import PySimpleGUI as sg
import cv2
import numpy as np
import pygame
import math
from Deprecated import easycall as easycall
from Vision import vision as vision
import FTPInterface as ftp


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
        cos_q2 = (r**2 - self.len1**2 - self.len2**2) / \
            (2 * self.len1 * self.len2)
        self.q2 = math.acos(cos_q2)  # Angle for the second link
        sin_q2 = math.sqrt(1 - cos_q2**2)
        # Angle for the first link
        self.q1 = phi - math.atan2((self.len2 * sin_q2),
                                   (self.len1 + self.len2 * cos_q2))

    def draw_arm(self):
        # Calculate the joint position based on the angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)

        # Draw the arm: base -> joint -> end effector
        pygame.draw.line(self.screen, (0, 0, 0), (self.base_x,
                         self.base_y), (joint_x, joint_y), 5)
        pygame.draw.line(self.screen, (0, 0, 0),
                         (joint_x, joint_y), (end_x, end_y), 5)

        print(math.degrees(self.q1), math.degrees(self.q2))

    def update_end_effector_position(self):
        # Calculate the end effector's position based on the current angles
        joint_x = self.base_x + self.len1 * math.cos(self.q1)
        joint_y = self.base_y + self.len1 * math.sin(self.q1)
        self.end_x = joint_x + self.len2 * math.cos(self.q1 + self.q2)
        self.end_y = joint_y + self.len2 * math.sin(self.q1 + self.q2)


# Create the GUI theme
sg.theme('BlueMono')

# Initialize variables
recording = True
final_img = None
frame = None
imgbytes = None
file_path = ""
height = 482
width = 642
color1 = int(0x0000ff)
color2 = int(0x00ff00)
color3 = int(0xff0000)
colorPalette = [(color1 >> 16, color1 % (2**16) >> 8, color1 % (2**8)),
                (color2 >> 16, color2 % (2**16) >> 8, color2 % (2**8)),
                (color3 >> 16, color3 % (2**16) >> 8, color3 % (2**8))]
granularity = 1
maxLines = 100
paperSize = (279, 215)

# Initialize the Pygame window
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Robot Arm Visualization")

# Initialize the arm
arm = Arm2Link(screen, 200, 200, 500, 300)

# Main tab for selecting data to send
tab1 = [[sg.Text('Capture mouse movements or upload a GCode file.')],

        [sg.Text('Upload image or GCode file:'), sg.Input(key='inputbox'),
         sg.FileBrowse(key='browse', file_types=(("Image Files", "*.png"),
                                                 ("GCode Files", "*.txt *.gcode *.mpt *.mpf *.nc")))],

        [sg.Text('Webcam output:', key='imgtext')],

        [sg.Image(filename='', key='image')],

        [sg.Text('Image Controls:\t'),
         sg.Button('Capture Image', key='capimg'), sg.Button('Clear Image', key='retake', disabled=True)],

        [sg.Text("Send Output:\t"),
         sg.Button("Send Image", key="sendimg", disabled=True),
         sg.Button("Send GCode File", key="sendGcode", disabled=True)]]

# Tab dedicated to the many OpenCV settings.
tab2 = [
    [sg.Text('Enter computer vision parameters', key='cv_text')],

    [sg.Text('Color Palette (6 digit hex)', size=(40, 1)),
     sg.Input(size=(13, 1), key='color1', default_text="0000FF"),
     sg.Input(size=(13, 1), key='color2', default_text="00FF00"),
     sg.Input(size=(13, 1), key='color3', default_text="FF0000")],

    [sg.Text('Granularity (float between 1 and 50)', size=(40, 1)),
     sg.Input(key='granularity', default_text="1")],

    [sg.Text('Max Lines (int between 1 and 1000)', size=(40, 1)),
     sg.Input(key='maxlines', default_text="100")],

    [sg.Text('Paper Size in mm (int in [10, 279], int in [10, 215])', size=(40, 1)),
     sg.Input(size=(21, 1), key='dim1', default_text="279"),
     sg.Input(size=(21, 1), key='dim2', default_text="215")],

    [sg.Button('Apply', key='apply')],
    [sg.Text('Robot Arm Visualization:')],
    [sg.Graph(canvas_size=(600, 400), graph_bottom_left=(0, 0), graph_top_right=(
        600, 400), background_color='white', key='GRAPH', enable_events=True)]

]
# Putting everything together into a single window.
layout = [
    [sg.TabGroup(
        [[sg.Tab('Main Interface', tab1), sg.Tab('OpenCV Settings', tab2)]])],
    [sg.Output(size=(80, 10), font='Verdana 10')],
    [sg.Button('Exit', key='exit')]
]


# Create the PySimpleGUI window
window = sg.Window('Robot Arm Interface', layout, location=(200, 0))

# Main event loop
while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'exit'):
        break

    if event == 'capimg':
        recording = False
        final_img = frame
        window['imgtext'].update('Image to use:')
        window['sendimg'].update(disabled=False)
        window['capimg'].update(disabled=True)
        window['retake'].update(disabled=False)

    elif event == 'retake':
        recording = True
        window['imgtext'].update('Webcam Output:')
        window['sendimg'].update(disabled=True)
        window['capimg'].update(disabled=False)
        window['retake'].update(disabled=True)
        window['inputbox'].update("")
        values['inputbox'] = ""

    elif event == 'sendimg':        # Routine for when "Send Image" button is pressed.
        print("Sending image to OpenCV...")
        #easycall.streamFromImage(final_img, colorPalette, granularity, maxLines, paperSize, reportDone,
                                 #easycall.giveCommand(reportSend), reportSent, easycall.serialStream(com, baud))
        gcode = vision.asGCode(final_img, colorPalette, granularity, maxLines, paperSize)
        gcodeFile = open("img.gcode", "w")
        gcodeFile.write(gcode)
        gcodeFile.close()

        stdout, stderr = ftp.executeGCodeSFTP("img.gcode")
        print(stdout)
    elif event == 'sendGcode':      # Routine for when "Send GCode File" button is pressed.
        print("Sending GCode...")
        #gcode = open(file_path).read()

        stdout, stderr = ftp.executeGCodeSFTP(file_path)
        print(stdout)
        #easycall.streamFromGcode(gcode, reportDone, easycall.giveCommand(reportSend), reportSent,
                                 #easycall.serialStream(com, baud))
    elif event == 'apply':          # Routine for when "Apply" button is pressed.
        print("Saved OpenCV Settings:")

        # Update all OpenCV settings
        color1 = int(values['color1'], 16)
        color2 = int(values['color2'], 16)
        color3 = int(values['color3'], 16)
        colorPalette = [(color1 >> 16, color1 % (2 ** 16) >> 8, color1 % (2 ** 8)),
                        (color2 >> 16, (color2 % (2 ** 16)) >> 8,
                         color2 % (2 ** 8)), (color3 >> 16, (color3 % (2 ** 16)) >> 8, color3 % (2 ** 8))]
        print("Color Palette: {}".format(colorPalette))
        granularity = float(values['granularity'])
        print("Granularity: {}".format(granularity))
        maxLines = int(values['maxlines'])
        print("Max Lines: {}".format(maxLines))
        paperSize = (float(values['dim1']), float(values['dim2']))
        print("Paper Size: {}".format(paperSize))

    

    # # Update arm visualization
    # mouse_pos = values['GRAPH']
    # if mouse_pos != (None, None):
    #     target_x, target_y = mouse_pos[0] - arm.base_x, 300 - mouse_pos[1]
    #     arm.calculate_angles(target_x, target_y)
    #     arm.draw_arm()

# Close the PySimpleGUI window and exit the program
window.close()
pygame.quit()
