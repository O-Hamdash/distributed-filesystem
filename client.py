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

    reply = client_socket.recv_string()
    client_socket.close()

    print("Storage node is contacted for downloading.")
        
    file_data = download_socket.recv()

    # file_path = os.path.join(dst_path, file_name)
    with open(local_path, "wb") as file:
        file.write(file_data)

    download_socket.close()

if __name__ == "__main__":
    upload("test.txt", "/test.txt")
    print("Test uploaded")
    time.sleep(5)
    download("/test.txt",  "test-received.txt")
    print("Test downloaded")
    time.sleep(5)
    download("/test2.txt", "test2.txt")
    print("Error")