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
        socket.connect("tcp://" + storage_ip + ":50001")
        
        message = generate_json("available_storage")
        socket.send_pyobj(message)
        reply = socket.recv_pyobj()
        available_storage = int(reply["msg"])

        print(f"received available storage from {reply['src_ip']}: {reply['msg']}")

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

def master_to_storage_requester(message:dict, reply_socket:zmq.sugar.socket.Socket):
    op = message["op"]

    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    if op == "upload":
        dst_ip = get_most_available_storage_ip()

        file = add(fs_root, message["path"], type="file", ip_address=dst_ip)

        file_id = file.id

        socket.connect(f"tcp://{dst_ip}:50001")

        json = generate_json("port_request", file_id=file_id)
        socket.send_pyobj(json)

        port_recv_socket = context.socket(zmq.PULL)
        port_recv_socket.bind(f"tcp://*:50005")
        message = port_recv_socket.recv_pyobj()
        print(f"received: {message}")
        port = message.get("port")

        port_recv_socket.close()

        reply_socket.send_pyobj(generate_json("upload_details", dst_ip=dst_ip, port=port))

        ########################################################
        ## TODO: do something with the reply (upload_success) ##
        ########################################################
        reply = socket.recv_pyobj()

        print(f"upload reply: {reply}")

    elif op == "download":
        print(f"received download request from {message['src_ip']}")

        print(f"path from message {message['path']}")

        file = get_object_by_path(fs_root, message["path"])

        print(file)

        file_id = str(file.id)

        storage_ip = file.ip_address

        dst_ip = message["src_ip"]

        socket.connect(f"tcp://{storage_ip}:50001")
        json = generate_json("download_details", dst_ip=dst_ip, file_id=file_id)
        
        socket.send_pyobj(json)

        socket.recv_pyobj()

        reply_socket.send_string("success!")

    print(f"exiting {op}")
    socket.close()
    print("closed socket----------")

def client_request_handler():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{master_ip}:50002")

    while True:
        # Wait for next request from client
        message = socket.recv_pyobj()
        print("Received request: %s" % message)

        #master_to_storage_requester = Thread(target=master_to_storage_requester, args=(message,))
        #master_to_storage_requester.start()

        master_to_storage_requester(message, socket)

if __name__ == "__main__":
    threads = []

    ip_listener = Thread(target=listen_for_ips)
    threads.append(ip_listener)

    client_handler = Thread(target=client_request_handler)
    threads.append(client_handler)

    for t in threads:
        t.start()

    for t in threads:
        t.join()
    
