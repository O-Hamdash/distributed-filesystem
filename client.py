import zmq
import netifaces
import os
import time
from shared import *

master_ip = "192.168.56.10"

def upload(local_path, remote_path):
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{master_ip}:50002")

    local_ip = get_ip_address()
    file_path = remote_path
    json = generate_json("upload", src_ip=local_ip, path=file_path)
    client_socket.send_pyobj(json)

    reply = client_socket.recv_pyobj()
    client_socket.close()

    if reply["op"] == "upload_details":
        dst_ip = reply["dst_ip"]
        port = reply["port"]

        upload_socket = context.socket(zmq.PUSH)
        upload_socket.connect(f"tcp://{dst_ip}:{port}")

        with open(local_path, "rb") as file:
            file_data = file.read()
            upload_socket.send(file_data)

        upload_socket.close()
    elif reply['op'] == "upload_error":
        print(f"error uploading file '{remote_path}': {reply['msg']}")
        return
    else:
        print("Some error happened on master or storage side.")

def download(remote_path, local_path):
    context = zmq.Context()

    local_ip = get_ip_address()

    download_socket = context.socket(zmq.PULL)
    download_socket.bind(f"tcp://{local_ip}:50003")

    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{master_ip}:50002")

    json = generate_json("download", src_ip=local_ip, path=remote_path)
    client_socket.send_pyobj(json)

    reply = client_socket.recv_pyobj()

    if reply['op'] == "download_error":
        print(f"error downlaoding file '{remote_path}': {reply['msg']}")
        client_socket.close()
        download_socket.close()
        return

    client_socket.close()

    print("Storage node is contacted for downloading.")
        
    file_data = download_socket.recv()

    # file_path = os.path.join(dst_path, file_name)
    with open(local_path, "wb") as file:
        file.write(file_data)

    download_socket.close()

def mkdir(path):
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{master_ip}:50002")

    json = generate_json("mkdir", path=path)
    client_socket.send_pyobj(json)

    reply = client_socket.recv_pyobj()

    if reply['op'] == "mkdir_error":
        print(f"error creating directory '{path}': {reply['msg']}")
    
    client_socket.close()

if __name__ == "__main__":
    print("Welcome to the distributed file storage system!")
    while True:
        command = input("Enter your command: (Enter help to get the list of available commands)\n")
        args = command.split()
        if command == "help":
            print("Command Name => how to invoke the command")
            print("1. upload => upload <local_path> <remote_path> (remote_path must start with a \"/\" character)")
            print("2. download => download <remote_path> <local_path> (remote_path must start with a \"/\" character)")
            print("3. delete => delete <path> (path must start with a \"/\" character)")
            print("4. mkdir => mkdir <path (path must start with a \"/\" character)")
            print("5. ls => ls <path> (<path> is an optional input field. When it is given, it must start with a \"/\" character)")
            print("6. exit => exit")
        elif args[0] == "upload":
            if len(args) == 3:
                upload(args[1], args[2])
            else:
                print("Wrong number of arguments. upload command is called as the following:")
                print("upload <local_path> <remote_path>")
        elif args[0] == "download":
            if len(args) == 3:
                download(args[1], args[2])
            else:
                print("Wrong number of arguments. download command is called as the following:")
                print("download <remote_path> <local_path>")
        elif args[0] == "delete":
            if len(args) == 2:
                delete(args[1])
            else:
                print("Wrong number of arguments. delete command is called as the following:")
                print("delete <path>")
        elif args[0] == "mkdir":
            if len(args) == 2:
                mkdir(args[1])
            else:
                print("Wrong number of arguments. mkdir command is called as the following:")
                print("mkdir <path>")
        elif args[0] == "ls":
            if len(args) == 1:
                ls()
            elif len(args) == 2:
                ls(args[1])
            else:
                print("Wrong number of arguments. ls command is called as the following:")
                print("ls <path> (<path> is optional)")
        elif command == "exit":
            print("Exiting from the program. Good bye!")
            break
        else:
            print("Error: Invalid command.")