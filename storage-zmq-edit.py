import json
import multiprocessing
from threading import Thread
from threading import Lock
import time
import zmq
import socket
import fcntl
import struct
import psutil
import netifaces
import os

master_ip = "192.168.56.10"
CLIENT_FILE_RECV_PORT = "56000"
CLIENT_FILE_SEND_PORT = "55000"

def generate_json(op, src_ip=None, path=None, msg=None, dst_ip=None, port=None, file_id=None):
    # Create a dictionary with the function parameters
    params = {
        "op": op,
        "src_ip": src_ip,
        "path": path,
        "msg": msg,
        "dst_ip": dst_ip,
        "port": port,
        "file_id": file_id
    }

    # Convert the dictionary to a JSON string
    json_data = json.dumps(params)
    return json_data

##### PortManager begin
class PortManager:
    """
    Class to assign and release port numbers for a storage machine dynamically
    """
    def __init__(self):
        self.assigned_ports = set()             # set of assigned ports
        self.port_lock = Lock()                 # lock for atomic port management
        self.start_port = 55000                 # start port num
        self.end_port = self.start_port + 100   # end port num = start + limit
    
    def assign_port(self):
        """
        Tries to asssign a port between starting and ending port numbers.
        @return assigned port number if assigned a port, else -1
        """
        with self.port_lock:
            for port in range(self.start_port, self.end_port):
                if port not in self.assigned_ports:
                    self.assigned_ports.add(port)
                    return port
        return -1

    def release_port(self, port):
        """
        Tries to release a port that is registered to the assigned port set.
        """
        with self.port_lock:
            if port in self.assigned_ports:
                self.assigned_ports.remove(port)
##### PortManager end

# initiate the port manager
port_manager = PortManager()

# CLIENT_FILE_RECV_PORT = "56000"
# I assume that master port 50005 listens for the storage port notifications
# I assume master will give client's ip, id of the requested file as filename, and file's output name
# I assume client will be renaming the file after receiving the necessary data
def send_file_old(port_manager: PortManager, cli_addr: str, filename: str, out_filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()
    
    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port")
    else:
        send_file_socket = context.socket(zmq.REP)
        send_file_socket.bind(f"tcp://*:{port}")
        print(f"Storage {ip_addr}: Assigned port {port}")
    
    # notify master on port update
    """
    PORT UPDATE:
    if positive, then send string message: opened tcp://*:{port}
    if negative, then send string message: failed tcp://*, then exit
    """
    port_sender = context.socket(zmq.PUSH)
    port_sender.connect(f"tcp://{master_ip}:50005")
    if port > 0:
        port_sender.send_string(f"opened tcp://*:{port}")
    else:
        port_sender.send_string(f"failed tcp://*")
        return

    # no need to get a response from master, continue with client connection

    # wait for the client's connection signal
    """ I assume that client will be notified of assigned dynamic port 
    and will send a dummy message to notify storage side that it is connected """    
    msg = send_file_socket.recv_string()   # will block until a msg is received
    print(f"storage recv'd string: {msg}")

    # send file to client
    with open(filename, "rb") as file:
        file_data = file.read()
        send_file_socket.send_multipart([out_filename.encode(), file_data])
    print(f"send file to {cli_addr}:56000")

    port_manager.release_port(port)

    # send file upload notification to master will be done in request handler
    return True

def send_file(port_manager: PortManager, cli_addr: str, filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()
    
    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port")
    else:
        send_file_socket = context.socket(zmq.PUSH)
        send_file_socket.connect(f"tcp://*:{port}")
        print(f"Storage {ip_addr}: Assigned port {port}")
    
    """
    IMPORTANT: "download_details" and "port_request" are mismatching.
    When storage receives "download_details", it directly tries assigning a port.
    Therefore, "port_request" should not be used. 
    "port_response" will be used to return the assigned port to master side.
    For that purpose, master should listen (PULL) that from another port ( assumed 50005?)
    """
    # notify master on port update
    port_sender = context.socket(zmq.PUSH)
    port_sender.connect(f"tcp://{master_ip}:50005")
    if port > 0:
        port_sender.send_json(generate_json("port_reply", src_ip=get_ip_address(), port=port))
    else:
        # port = -1 if a port could not be assigned
        port_sender.send_json(generate_json("port_reply", src_ip=get_ip_address(), port=port))
        return False

    # send file to client
    with open(filename, "rb") as file:
        file_data = file.read()
        send_file_socket.send(file_data)
    print(f"Storage {ip_addr}: file sent through port {port}")

    port_manager.release_port(port)
    return True

def recv_file(port_manager: PortManager, filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()
    
    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port")
        return False
    else:
        recv_file_socket = context.socket(zmq.PULL)
        recv_file_socket.connect(f"tcp://*:{port}")
        print(f"Storage {ip_addr}: Assigned port {port}")
    
    # master will not be notified on port update

    # receive file data from client
    file_data = recv_file_socket.recv()
    print(f"Storage {ip_addr}:recv'd file")
    # create new file and write received file data on new file
    with open(f"{filename}", "wb") as file:
        file.write(file_data)
    
    port_manager.release_port(port)
    return True

# I assume master will give client's ip and an id for the incoming file as filename
def recv_file_old(port_manager: PortManager, filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()
    
    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port")
    else:
        recv_file_socket = context.socket(zmq.PULL)
        recv_file_socket.bind(f"tcp://*:{port}")
        print(f"Storage {ip_addr}: Assigned port {port}")
    
    # # notify master on port update
    # """
    # PORT UPDATE:
    # if positive, then send string message: opened tcp://*:{port}
    # if negative, then send string message: failed tcp://*, then exit
    # """
    # port_sender = context.socket(zmq.PUSH)
    # port_sender.connect(f"tcp://{cli_addr}:50005")
    # if port > 0:
    #     port_sender.send_string(f"opened tcp://*:{port}")
    # else:
    #     port_sender.send_string(f"failed tcp://*")
    #     return

    # receive file data from client
    print("listening to recv file")
    file_data = recv_file_socket.recv()
    print("recv'd file")

    # create new file and write received file data on new file
    with open(f"{filename}", "wb") as file:
        file.write(file_data)
    
    port_manager.release_port(port)
    return True

def get_ip_address(ifname='enp0s8'):
    try:
        addresses = netifaces.ifaddresses(ifname)
        ip_address = addresses[netifaces.AF_INET][0]['addr']
        return ip_address
    except (KeyError, IndexError) as e:
        print(f"Error getting IP address: {e}")
        return None

def send_ip():
    print("sending ip address to master")
    address = {"ip": "" + get_ip_address("enp0s8") + ""}
    print(f"sending ip: {address}")
    context = zmq.Context()
    ip_sender = context.socket(zmq.PUSH)
    ip_sender.connect(f"tcp://{master_ip}:50000")
    
    ip_sender.send_pyobj(address)
    print("Address sent successfully.")

def send_available_storage(path='/'):
    disk_usage = psutil.disk_usage(path)
    available_space = disk_usage.free
    return generate_json("")

def get_available_storage(path='/'):
    disk_usage = psutil.disk_usage(path)
    available_space = disk_usage.free
    return available_space

def test_master_storage_stringrequest():
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to hello world server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://" + master_ip + ":5555")

    #  Do 10 requests, waiting each time for a response
    for request in range(10):
        print("Sending request %s …" % request)

        ip_addresses = get_ip_address()
        if ip_addresses is not None:
            message = f"Hello from {ip_addresses}"
            try:
                socket.send(message.encode('utf-8'))

                # Get the reply.
                reply = socket.recv()
                print("Received reply %s [ %s ]" % (request, reply.decode('utf-8')))
            except zmq.error.ZMQError as e:
                print(f"Error sending/receiving ZMQ message: {e}")
        else:
            print("Failed to retrieve IP addresses. Request not sent.")

def request_handler():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:52000")

    while True:
        #  Wait for next request from server
        message = socket.recv_string()
        print("Received request: %s" % message)

        reply = "no reply"

        message_args = message.split()

        if message == "storage":
            reply = str(get_available_storage())
        elif message_args[0] == "testsendfile":
            print("received testsendfile, starting")
            send_file(port_manager, message_args[1], message_args[2], message_args[3])
            reply = "sendfile successful"
        elif message_args[0] == "testrecvfile":
            print("received testrecvfile, starting")
            recv_file(port_manager, message_args[1], message_args[2])
            reply = "recvfile successful"

        #  Send reply back to client
        socket.send_string(reply)

def request_handler_revised():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:50001")

    while True:
        #  Wait for next request from server
        json_message = socket.recv_json()
        print(f"Received request: {str(json_message)}")

        reply = None
        _op = json_message.get("op")

        if _op == "available_storage":
            storage = str(get_available_storage())
            reply = generate_json("available_storage_reply", src_ip=get_ip_address(), msg=storage)
        elif _op == "download_details":
            dst_ip = json_message.get("dst_ip")
            file_id = json_message.get("file_id")
            recv_file_process = Thread(target=send_file, args=(port_manager, dst_ip, file_id))
            recv_file_process.start()
            recv_file_process.join()
            # IMPORTANT: "download_success": dummy message to reply master for download???
            reply = generate_json("download_success")
        # IMPORTANT: "port_request" changed to "upload_request" for naming convention
        elif _op == "upload_request":
            file_id = json_message.get("file_id")
            recv_file(port_manager, file_id)

            reply = generate_json("upload_success",src_ip=get_ip_address(), file_id=file_id)

        #  Send reply back to client
        socket.send_json(reply)

if __name__ == "__main__":
    processes = []

    ip_process = Thread(target=send_ip)
    ip_process.start()
    processes.append(ip_process)

    request_handler_process = Thread(target=request_handler)
    processes.append(request_handler_process)
    request_handler_process.start()

    # test_process = Thread(target=test_master_storage_stringrequest)
    # processes.append(test_process)
    # test_process.start()

    for p in processes:
        p.join()