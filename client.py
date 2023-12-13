import zmq
import netifaces
import os
import time

master_ip = "192.168.56.10"

# json generator
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
        return str(ip_address)
    except (KeyError, IndexError) as e:
        print(f"Error getting IP address: {e}")
        return None

def upload(file_path):
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{master_ip}:50002")

    local_ip = get_ip_address()
    file_path = "/" + file_path
    json = generate_json("upload", src_ip=local_ip, path=file_path)
    client_socket.send_pyobj(json)

    reply = client_socket.recv_pyobj()
    client_socket.close()

    if reply["op"] == "upload_details":
        dst_ip = reply["dst_ip"]
        port = reply["port"]

        upload_socket = context.socket(zmq.PUSH)
        upload_socket.connect(f"tcp://{dst_ip}:{port}")

        with open(file_path[1:], "rb") as file:
            file_data = file.read()
            upload_socket.send(file_data)

        upload_socket.close()
    else:
        print("Some error happened on master or storage side.")

def download(file_name):
    context = zmq.Context()

    download_socket = context.socket(zmq.PULL)
    download_socket.bind(f"tcp://{local_ip}:50003")

    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{master_ip}:50002")

    local_ip = get_ip_address()
    json = generate_json("download", src_ip=local_ip, path=file_name)
    client_socket.send_pyobj(json)

    reply = client_socket.recv_string()
    client_socket.close()

    print("Storage node is contacted for downloading.")
        
    file_data = download_socket.recv()

    # file_path = os.path.join(dst_path, file_name)
    with open(file_name, "wb") as file:
        file.write(file_data)

    download_socket.close()

    """ if reply["op"] == "download_error":
        print("File doesn't exist in any of the storage nodes.")
    elif reply["op"] == "download_success":
        print("Storage node is contacted for downloading.")
        
        download_socket = context.socket(zmq.PULL)
        download_socket.bind(f"tcp://{local_ip}:50003")
        file_data = download_socket.recv()

        # file_path = os.path.join(dst_path, file_name)
        with open(file_name, "wb") as file:
            file.write(file_data)

        download_socket.close()
    else:
        print("Some error happened on master or storage side.") """

if __name__ == "__main__":
    upload("test.txt")
    print("Test uploaded")
    time.sleep(10)
    download("test.txt")
    print("Test downloaded")
    time.sleep(10)
    download("test2.txt")
    print("Error")