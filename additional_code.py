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


# This will run on the master
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


# This will run on the client
def client_requester():
    local_ip = get_ip_address()
    
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{master_ip}:50002")

    requests = ["test1", "test2", "test3"]

    for req in requests:
        json = generate_json(req, src_ip=local_ip, path="/test/path.txt")
        socket.send_pyobj(json)
        reply = socket.recv_string()
        print(f"reply to {req}: {reply}")