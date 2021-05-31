import minecraft_launcher_lib
import subprocess

def runMinecraft(username, uuid, version, directory, ram):
    if directory == '':
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
    else:
        minecraft_directory = directory
    minecraft_launcher_lib.install.install_minecraft_version(version,minecraft_directory)
    minecraft_launcher_lib.install.install_minecraft_version(version,minecraft_directory)

    options = {
    "username": username,
    "uuid": uuid,
    "token": "0x0",
    "jvmArguments": ram}

    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version,minecraft_directory,options)
    #subprocess.Popen(minecraft_command)

    #subprocess.Popen(minecraft_command, stdout = subprocess.PIPE, creationflags = subprocess.CREATE_NO_WINDOW)
    subprocess.call(minecraft_command, creationflags = subprocess.CREATE_NO_WINDOW)