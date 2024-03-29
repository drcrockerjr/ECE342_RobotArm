import os

def filter_commands(curr_line):
    gcmd = 0

    if "G0" in curr_line:
        return gcmd
    gcmd += 1

    if "G1" in curr_line:
        return gcmd
    gcmd += 1

    if "G20" in curr_line:
        return gcmd
    gcmd += 1

    if "G21" in curr_line:
        return gcmd
    gcmd += 1

    if "G90" in curr_line:
        return gcmd
    gcmd += 1

    if "G91" in curr_line:
        return gcmd
    gcmd += 1

    if "M2" in curr_line:
        return gcmd
    gcmd += 1

    if "M6" in curr_line:
        return gcmd
    gcmd += 1

    if "M72" in curr_line:
        return gcmd
    gcmd += 1

    return gcmd

def process_movements(curr_line, usemm, useabsolute, prev_coord):
    tokens = curr_line.split("X")
    tokens = tokens[1].split()
    new_x_coord = float(tokens[0])

    if useabsolute == 1:
        print("A: ", end='')
        x_coord = new_x_coord
    elif useabsolute == 0:
        print("R: ", end='')
        x_coord = prev_coord[0] + new_x_coord

    if usemm == 0 and useabsolute == 1:
        x_coord = x_coord * 25.4

    tokens = curr_line.split("Y")
    tokens = tokens[1].split()
    new_y_coord = float(tokens[0])

    if useabsolute == 1:
        print("A: ", end='')
        y_coord = new_y_coord
    elif useabsolute == 0:
        print("R: ", end='')
        y_coord = prev_coord[1] + new_y_coord

    if usemm == 0 and useabsolute == 1:
        y_coord = y_coord * 25.4

    prev_coord[0] = x_coord
    prev_coord[1] = y_coord

    print("(", x_coord, ",", y_coord, ")")

    return prev_coord

def process_file(file_path):
    prev_coord = [0.0, 0.0]

    with open(file_path, 'r') as gcode_file:
        usemm = -1
        useabsolute = -1

        for curr_line in gcode_file:
            command_num = filter_commands(curr_line)

            if command_num < 2:
                prev_coord = process_movements(curr_line, usemm, useabsolute, prev_coord)
            elif command_num == 2:
                usemm = 0
                print("Using Inches")
            elif command_num == 3:
                usemm = 1
                print("Using Millimeters")
            elif command_num == 4:
                useabsolute = 1
                print("Using Absolute Positioning Mode")
            elif command_num == 5:
                useabsolute = 0
                print("Using Relative Positioning Mode")
            elif command_num == 6:
                print("End Program")
                return
            elif command_num == 7:
                print("Tool Change")
            elif command_num == 8:
                useabsolute = 1
                usemm = 1
                print("Restored Modal State")

def find_user_file():
    line_entered = input("Enter the complete file name: ")
    cwd = os.getcwd()

    for file_name in os.listdir(cwd):
        if file_name == line_entered:
            return file_name

    print("The file", line_entered, "was not found. Try again")
    return None

def main():
    file_name = find_user_file()
    if file_name:
        process_file(file_name)

if __name__ == "__main__":
    main()
