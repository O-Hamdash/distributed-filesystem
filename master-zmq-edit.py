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
    socket.connect("tcp://" + storage_ip + ":50001")
    
    filename = "test.txt"
    message = generate_json("download_details", dst_ip=client_ip, file_id=filename)
    # message = f"testsendfile {client_ip} {filename} {out_filename}"    # filename was already decided by master
    socket.send_pyobj(message)
    print(f"sent message: {message}")

    # I assume master sends info to client so that client can connect to storage port
    # client connects to storage's dynamic port and sends dummy message
    download_socket = context.socket(zmq.PULL)
    download_socket.bind("tcp://" + "192.168.56.10" + f":50003")
    
    # storage sends file 
    file_data = download_socket.recv()
    print("file has been received")
    with open(f"downloadad_file.txt", "wb") as file:
        file.write(file_data)
    print("created and wrote file")

    message = socket.recv_pyobj()
    print(f"recvd {message}")


def test_recv_file():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    time.sleep(5)

    print("sending testrecvfile")
    storage_ip="192.168.56.101"
    client_ip="192.168.56.10"
    socket.connect("tcp://" + storage_ip + ":50001")

    filename = "uploaded_file.txt"
    message = generate_json("port_request", dst_ip=client_ip, file_id=filename)
    socket.send_pyobj(message)

    port_recv_socket = context.socket(zmq.PULL)
    port_recv_socket.bind(f"tcp://*:50005")
    message = port_recv_socket.recv_pyobj()
    print(f"received: {message}")
    port = message.get("port")

    file_push_socket = context.socket(zmq.PUSH)
    file_push_socket.connect("tcp://" + "192.168.56.101" + f":{port}")
    
    with open("downloadad_file.txt", "rb") as file:
        file_data = file.read()
    print("sending file")
    file_push_socket.send(file_data)

    message = socket.recv_pyobj()
    print(f"recvd {message}")


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
