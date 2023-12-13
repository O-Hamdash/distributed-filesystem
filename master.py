import time
from collections import defaultdict
from threading import RLock, Thread
import zmq

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

def receive_client():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:50002")

    while True:
        # Wait for next request from client
        message = socket.recv_pyobj()
        print("Received request: %s" % message)

        client_ip = message['src_ip']   #Where to use this?
        socket.connect("tcp://"+ client_ip +":50002")
        if message['op'] == 'upload':
            #TODO: Omar's Data Keeper search
            #reply_string = "UUUUU"
            #socket.send_string(reply_string)
            reply_json = generate_json("upload_details", dst_ip=dst_ip, port=port)
            socket.send_pyobj(reply_json)
        elif message['op'] == 'download':
            #TODO: Omar's Data Keeper search
            #reply_string = "DDDDD"
            #socket.send_string(reply_string)
            reply_json = generate_json("download_details", dst_ip=dst_ip, file_id=file_id)
            #...

def main():
    threads = []

    client_connection_thread = Thread(target=receive_client)
    threads.append(client_connection_thread)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

main()