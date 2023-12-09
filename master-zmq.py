import multiprocessing
import time
import zmq
from threading import Thread

master_ip = "192.168.56.10"

storage_ips = set()

def listen_for_ips():
    context = zmq.Context()
    master_receiver = context.socket(zmq.PULL)
    master_receiver.bind(f"tcp://*:50000")
    
    while True:
        print("Waiting for address from storage...")
        address = master_receiver.recv_pyobj()
        print(f"Received address: {address}")
        
        storage_ips.add(address.get("ip"))
        print(storage_ips)

def request_storage_status(storage_ip="192.168.56.101"):
    context = zmq.Context()

    #  Socket to talk to storage
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://" + storage_ip + ":52000")
    
    message = "storage"
    socket.send_string(message)
    reply = socket.recv_string()

    print(f"available storage: {reply}")

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

if __name__ == "__main__":
    processes = []

    ip_process = Thread(target=listen_for_ips)
    processes.append(ip_process)
    ip_process.start()

    test_receiver = Thread(target=test)
    processes.append(test_receiver)
    test_receiver.start()

    storage_status = Thread(target=request_storage_status)
    processes.append(storage_status)
    storage_status.start()

    for p in processes:
        p.join()
