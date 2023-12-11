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
    context.destroy()

def test_send_file():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    # request_storage_status()
    print("HERE")

    time.sleep(4)

    # test send file from storage to client begin

    # I assume client sent request to master and master chose the specific storage machine
    # master sends request to storage
    print("sending testsendfile")
    storage_ip="192.168.56.101"
    client_ip="192.168.56.10"
    socket.connect("tcp://" + storage_ip + ":52000")
    
    filename = "test.txt"
    out_filename = "senttest.txt"
    message = f"testsendfile {client_ip} {filename} {out_filename}"    # filename was already decided by master
    port_recv_socket = context.socket(zmq.PULL)
    port_recv_socket.bind(f"tcp://*:50005")
    socket.send_string(message)

    # master receives storage's dynamic port
    message = port_recv_socket.recv_string()
    print(f"received: {message}, port is {message[-5:]}")

    # I assume master sends info to client so that client can connect to storage port
    # client connects to storage's dynamic port and sends dummy message
    notify_socket = context.socket(zmq.REQ)
    notify_socket.connect("tcp://" + "192.168.56.101" + f":{message[-5:]}")
    notify_socket.send_string("dummy msg")
    print("dummy msg sent, waiting for file")
    
    # storage sends file 
    msglist = notify_socket.recv_multipart()
    print("file has been received")
    with open(f"{msglist[0].decode()}", "wb") as file:
        file.write(msglist[1])
    print("created and wrote file")

    context.destroy()
    # test send file from storage to client end

def test_recv_file():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    time.sleep(5)

    print("sending testrecvfile")
    storage_ip="192.168.56.101"
    client_ip="192.168.56.10"
    socket.connect("tcp://" + storage_ip + ":52000")

    filename = "senttest.txt"
    message = f"testrecvfile {client_ip} {filename}"    # filename was already decided by master
    port_recv_socket = context.socket(zmq.PULL)
    port_recv_socket.bind(f"tcp://*:50005")
    socket.send_string(message)

    # master receives storage's dynamic port
    message = port_recv_socket.recv_string()
    print(f"received: {message}, port is {message[-5:]}")

    file_push_socket = context.socket(zmq.PUSH)
    file_push_socket.connect("tcp://" + "192.168.56.101" + f":{message[-5:]}")
    
    with open(filename, "rb") as file:
        file_data = file.read()
    print("sending file")
    file_push_socket.send(file_data)


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

    # storage_status = Thread(target=request_storage_status)
    # processes.append(storage_status)
    # storage_status.start()

    testsendfile = Thread(target=test_send_file)
    processes.append(testsendfile)
    testsendfile.start()

    testrecvfile = Thread(target=test_recv_file)
    processes.append(testrecvfile)
    testrecvfile.start()

    for p in processes:
        p.join()
