
import multiprocessing
import time
import zmq
import socket
import fcntl
import struct
import psutil
import netifaces

master_ip = "192.168.56.10"

def get_ip_address(ifname):
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

def test():
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to hello world server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://" + master_ip + ":5555")

    #  Do 10 requests, waiting each time for a response
    for request in range(10):
        print("Sending request %s …" % request)

        ip_addresses = get_ip_address('enp0s8')
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

        if str(message) == "storage":
            reply = get_available_storage()

        #  Send reply back to client
        socket.send_string(str(reply))

if __name__ == "__main__":
    processes = []

    ip_process = multiprocessing.Process(target=send_ip)
    ip_process.start()
    processes.append(ip_process)

    request_handler_process = multiprocessing.Process(target=request_handler)
    processes.append(request_handler_process)
    request_handler_process.start()

    for p in processes:
        p.join()