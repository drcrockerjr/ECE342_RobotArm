import pysftp
import paramiko.client as ssh
BOARD_IP = "10.162.177.236"
RUN_FOLDER = '/root/SCARA_robot/src'
SCRIPT_EXECUTE = "python3 ~/SCARA_robot/src/HPS_to_FPGA/CommandStreamTest.py"
def executeGCodeSFTP(gcodeFilePath):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # And authenticate with private key
    with pysftp.Connection(host=BOARD_IP, username='root', password='root', cnopts=cnopts) as sftp:
        sftp.chdir("/root/SCARA_robot/src/")
        sftp.put(gcodeFilePath, remotepath="/root/SCARA_robot/src/test.gcode")  # upload file to public/ on remote
        # print(sftp.execute("cd /root/SCARA_robot/src;python3 HPS_to_FPGA/CommandStreamTest.py"))
        #result = sftp.execute(SCRIPT_EXECUTE)
        #print(result)
    client = ssh.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())

    client.connect(hostname=BOARD_IP, port=22, username="root", password="root")
    stdin, stdout, stderr = client.exec_command("cd /root/SCARA_robot/src; python3 main.py")
    return (stdout.read().decode(), stderr.read().decode())

    #client.close()
if __name__ == "__main__":

    gcodeFile = "../GCode/test.gcode"
    result = executeGCodeSFTP(gcodeFile)
    print("STDOUT: ")
    print(result[0])
    print("STDERR: ")
    print(result[1])