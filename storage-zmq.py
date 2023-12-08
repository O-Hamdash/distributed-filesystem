
import zmq
import socket
import fcntl
import struct
import psutil
import netifaces

def get_ip_address(ifname):
    try:
        addresses = netifaces.ifaddresses(ifname)
        ip_address = addresses[netifaces.AF_INET][0]['addr']
        return ip_address
    except (KeyError, IndexError) as e:
        print(f"Error getting IP address: {e}")
        return None
    
context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://192.168.56.10:5555")

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