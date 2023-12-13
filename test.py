import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)

print(type(socket))