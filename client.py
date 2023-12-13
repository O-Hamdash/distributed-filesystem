import zmq
import socket
import psutil
import netifaces
from threading import RLock, Thread

master_ip = "192.168.56.10"

#JSON generator
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

def get_ip_address(ifname='enp0s8'):
    try:
        addresses = netifaces.ifaddresses(ifname)
        ip_address = addresses[netifaces.AF_INET][0]['addr']
        return ip_address
    except (KeyError, IndexError) as e:
        print(f"Error getting IP address: {e}")
        return None
    
def connect_master():
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to hello world server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://" + master_ip + ":50002")

    print("Now, I am requesting a JSON...")
    ip_addresses = get_ip_address()
    if ip_addresses is not None:
        message_json = generate_json("upload", src_ip=ip_addresses, path="/folder1/file.txt")
        try:
            socket.send_pyobj(message_json)
            
            reply = socket.recv_string()
            print("Received reply: %s" % reply)
        except zmq.error.ZMQError as e:
            print(f"Error sending/receiving ZMQ message: {e}")
    else:
        print("Failed to retrieve IP addresses. Request not sent.")

if __name__ == "__main__":
    threads = []

    test_process = Thread(target=connect_master)
    threads.append(test_process)

    for t in threads:
        t.start()

    for t in threads:
        t.join()