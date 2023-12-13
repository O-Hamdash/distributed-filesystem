import time
import zmq
from threading import Thread

from shared import generate_json

from fs import *


fs_root = FileSystemObject("/", "folder")


master_ip = "192.168.56.10"
download_port = "50003"

storage_ips = set()

def listen_for_ips():
    context = zmq.Context()
    master_receiver = context.socket(zmq.PULL)
    master_receiver.bind(f"tcp://192.168.56.10:50000")
    
    while True:
        print("Waiting for address from storage...")
        address = master_receiver.recv_pyobj()
        print(f"Received address: {address}")
        
        storage_ips.add(address.get("ip"))
        print(storage_ips)


def get_most_available_storage_ip():
    largest_storage = 0
    chosen_node_ip = None

    for storage_ip in storage_ips:

        print(f"requesting available storage for {storage_ip}")
        context = zmq.Context()

        #  Socket to talk to storage
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://" + storage_ip + ":52000")
        
        message = "storage"
        socket.send_string(message)
        available_storage = int(socket.recv_string())

        if available_storage > largest_storage:
            chosen_node_ip = storage_ip

    return chosen_node_ip

def test():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        #  Wait for next request from client
        message = socket.recv()
        print("Received request: %s" % message)

        #  Do some 'work'
        time.sleep(1)

        #  Send reply back to client
        socket.send(b"World")

def master_to_storage_requester(message:dict):
    op = message["op"]

    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    if op == "upload":
        ############################
        ## TODO: generate file id ##
        ############################
        file_id = "1"

        ##############################################################################################
        ## TODO: save file to DB (let's do it like this for now and assume there will be no errors) ##
        ##############################################################################################

        dst_ip = get_most_available_storage_ip()
        socket.connect(f"tcp://{dst_ip}:50001")

        json = generate_json("port_request", file_id=file_id)
        socket.send_pyobj(json)
        reply = socket.recv_pyobj()
        
        port = reply["port"]

        #######################################################################
        ## TODO: integrate Burak's code to send the upload_details to client ##
        #######################################################################
    
    elif op == "download":
        ###############################
        ## TODO: get file id from DB ##
        ###############################

        file = get_object_by_path(fs_root, message["path"])

        file_id = str(file.id)

        ##################################
        ## TODO: get storage ip from DB ##
        ##################################
        storage_ip = file.ip_address

        dst_ip = message["src_ip"]

        socket.connect(f"tcp://{storage_ip}:50001")
        json = generate_json("download_details", dst_ip=dst_ip, file_id=file_id)



    requests = ["test1", "test2", "test3"]

    for req in requests:
        json = generate_json(req, path="/test/path.txt")
        socket.send_pyobj(json)
        reply = socket.recv_string()
        print(f"reply to {req}: {reply}")

if __name__ == "__main__":
    threads = []

    ip_listener = Thread(target=listen_for_ips)
    threads.append(ip_listener)

    test_receiver = Thread(target=test)
    threads.append(test_receiver)


    client_handler = Thread(target=master_to_storage_requester)
    threads.append(client_handler)

    for t in threads:
        t.start()

    for t in threads:
        t.join()
    
