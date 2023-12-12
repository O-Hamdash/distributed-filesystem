
import zmq
import psutil
from threading import Thread

from shared import *



master_ip = "192.168.56.10"



def send_ip():
    print("sending ip address to master")
    address = {"ip": "" + get_ip_address("enp0s8") + ""}
    print(f"sending ip: {address}")
    context = zmq.Context()
    ip_sender = context.socket(zmq.PUSH)
    ip_sender.connect(f"tcp://{master_ip}:50000")
    
    ip_sender.send_pyobj(address)
    print("Address sent.")

def get_available_storage(path='/'):
    disk_usage = psutil.disk_usage(path)
    available_space = disk_usage.free
    return available_space

def test():
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
    local_ip = get_ip_address()
    socket.bind(f"tcp://{local_ip}:52000")

    while True:
        #  Wait for next request from server
        message = socket.recv_string()
        print("Received request: %s" % message)

        reply = "no reply"

        if str(message) == "storage":
            reply = get_available_storage()

        #  Send reply back to client
        socket.send_string(str(reply))


def client_request_handler():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://192.168.56.10:50002")

    while True:
        message = socket.recv_pyobj()
        
        if message["op"] == "test1":
            print(f"received test1 from {message['src_ip']}")
        elif message["op"] == "test2":
            print(f"received test2 from {message['src_ip']}")
        elif message["op"] == "test3":
            print(f"received test3 from {message['src_ip']}")

        socket.send_string("success")

if __name__ == "__main__":
    threads = []

    ip_sender = Thread(target=send_ip)
    threads.append(ip_sender)

    request_handler_process = Thread(target=request_handler)
    threads.append(request_handler_process)

    client_test = Thread(target=client_request_handler)
    threads.append(client_test)

    for t in threads:
        t.start()

    for t in threads:
        t.join()