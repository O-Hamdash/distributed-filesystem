import json
from threading import Thread
from threading import Lock
import time
import zmq
import psutil
import netifaces
import os

master_ip = "192.168.56.10"

def generate_json(op, src_ip=None, path=None, msg=None, dst_ip=None, port=None, file_id=None):
    return {
        "op": op, 
        "src_ip": str(src_ip), 
        "path": str(path), 
        "msg": str(msg), 
        "dst_ip": str(dst_ip), 
        "port": str(port), 
        "file_id": str(file_id)
    }

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

def send_file(port_manager: PortManager, cli_addr: str, filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()
    
    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port")
        return False
    else:
        send_file_socket = context.socket(zmq.PUSH)
        send_file_socket.connect(f"tcp://{cli_addr}:50003")
        print(f"Storage {ip_addr}: connected to tcp://{cli_addr}:50003 to send file")

    # send file to client
    try:
        with open(filename, "rb") as file:
            file_data = file.read()
            send_file_socket.send(file_data)
        print(f"Storage {ip_addr}: file sent through port {port}")
    except Exception as e:
        print(f"Storage {ip_addr}: received error {str(e)}")
        port_manager.release_port(port)
        return False
    
    port_manager.release_port(port)
    return True

def assign_port(port_manager: PortManager):
    ip_addr = get_ip_address()

    # open a port
    port = port_manager.assign_port()
    if port == -1:
        print(f"Storage {ip_addr}: Could not assign a port, sending port value as {port}")
    else:
        print(f"Storage {ip_addr}: Assigned port {port}")
    return port

def recv_file(port_manager: PortManager, port: int, filename: str):
    context = zmq.Context()
    ip_addr = get_ip_address()

    if port < 0:
        return
    else:
        recv_file_socket = context.socket(zmq.PULL)
        recv_file_socket.bind(f"tcp://*:{port}")

    # receive file data from client
    file_data = recv_file_socket.recv()
    print(f"Storage {ip_addr}: recv'd file")
    # create new file and write received file data on new file
    with open(f"{filename}", "wb") as file:
        file.write(file_data)
    
    port_manager.release_port(port)

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

def request_handler(port_manager: PortManager):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:50001")

    # port for pushing port response to master, assuming master will have some listener for it
    # if storage should ONLY send port_response AND NOT port_request PLUS a message for receiving the file, then delete this
    port_sender = context.socket(zmq.PUSH)
    port_sender.connect(f"tcp://{master_ip}:50005")

    while True:
        #  Wait for next request from server
        json_message = socket.recv_pyobj()
        print(f"Received request: {str(json_message)}")

        reply = None
        _op = json_message.get("op")

        if _op == "available_storage":
            storage = str(get_available_storage())
            reply = generate_json("available_storage_reply", src_ip=get_ip_address(), msg=storage)
        elif _op == "download_details":
            dst_ip = json_message.get("dst_ip")
            file_id = json_message.get("file_id")
            send_file_thread = Thread(target=send_file, args=(port_manager, dst_ip, file_id))
            send_file_thread.start()
            send_file_thread.join()
            reply = generate_json("filerecv")
        elif _op == "port_request":
            file_id = json_message.get("file_id")

            # assign a port
            port = assign_port(port_manager)
            # send port response to master. if port is not assigned, do not continue, else receive the file
            """IF RESPONSE SHOULD ONLY BE port_reply """
            # reply = generate_json("port_reply", src_ip=get_ip_address(), port=port)
            # if port > 0:
            #     recv_file_thread = Thread(target=recv_file, args=(port_manager, port, file_id))
            #     recv_file_thread.start()
            #     recv_file_thread.join()
            """IF RESPONSE SHOULD BE some response to notify that the file has been received, use this"""
            port_sender.send_pyobj(generate_json("port_reply", src_ip=get_ip_address(), port=port))
            if port > 0:
                recv_file_thread = Thread(target=recv_file, args=(port_manager, port, file_id))
                recv_file_thread.start()
                recv_file_thread.join()
                reply = generate_json("upload_success", src_ip=get_ip_address(), file_id=file_id)
        
        socket.send_pyobj(reply)

if __name__ == "__main__":

    # initiate the port manager
    port_manager = PortManager()

    threads = [
        Thread(target=send_ip),
        Thread(target=request_handler, args=(port_manager,))
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()