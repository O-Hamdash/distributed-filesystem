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

##### PortManager begin
class PortManager:
    """
    Class to assign and release port numbers for a storage machine dynamically
    """
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)  # single socket is capable of binding to multiple ports
        self.assigned_ports = set()             # set of assigned ports
        self.port_lock = Lock()                 # lock for atomic port management
        self.start_port = 55000                 # start port num
        self.end_port = self.start_port + 100   # end port num = start + limit
    
    def __del__(self):
        self.context.destroy()
    
    def assign_port(self):
        """
        Tries to asssign a port between starting and ending port numbers.
        @return assigned port number if assigned a port, else -1
        """
        with self.port_lock:
            for port in range(self.start_port, self.end_port):
                if port not in self.assigned_ports:
                    # self.open_port(port)
                    self.assigned_ports.add(port)
                    return port
        return -1

    def release_port(self, port):
        """
        Tries to release a port that is registered to the assigned port set.
        """
        with self.port_lock:
            if port in self.assigned_ports:
                # self.close_port(port)
                self.assigned_ports.remove(port)
    
    # def open_port(self, port):
    #     endpoint = f"tcp://*:{port}"
    #     self.socket.bind(endpoint)
    #     print(f"Opened port {port}")

    # def close_port(self, port):
    #     endpoint = f"tcp://*:{port}"
    #     self.socket.unbind(endpoint)
    #     print(f"Closed port {port}")
##### PortManager end

# initiate the port manager
port_manager = PortManager()

# CLIENT_FILE_RECV_PORT = "56000"
# I assume that master port 50005 listens for the storage port notifications
# I assume master will give client's ip, id of the requested file as filename, and file's output name
# I assume client will be renaming the file after receiving the necessary data
def send_file(port_manager: PortManager, cli_addr: str, filename: str, out_filename: str):
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
        port_sender.close()
        return
    port_sender.close()

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

    # TODO notify master?

    port_manager.release_port(port)

    # send file upload notification to master will be done in request handler
    return True

# I assume master will give client's ip and an id for the incoming file as filename
def recv_file(port_manager: PortManager, cli_addr: str, filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()
    
    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port")
    
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
    port_sender.close()

    # connect to client file sending port
    print(f"{ip_addr}: Connecting to {cli_addr}")
    pull_socket = context.socket(zmq.PULL)
    pull_socket.bind(f"tcp://{cli_addr}:{CLIENT_FILE_SEND_PORT}")

    # receive file data from client
    file_data = pull_socket.recv()
    if str(file_data) == "error":
        # handle error
        pass
    
    # create new file and write received file data on new file
    with open(f"{filename}", "wb") as file:
        file.write(file_data)
    
    # TODO send file upload notification to master

    pull_socket.unbind()
    pull_socket.close()
    port_manager.release_port(port)
    context.destroy()
    return

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
            send_file(port_manager, master_ip, message_args[1], message_args[2])
            reply = "sendfile successful"

        #  Send reply back to client
        socket.send_string(reply)
        

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