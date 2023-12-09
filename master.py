import time
from collections import defaultdict
from threading import RLock, Thread
import zmq

masterIP = "139.179.202.21"

def initializeClientSocket():
    context = zmq.Context()
    clientSocket = context.socket(zmq.REP)

    clientSocket.bind("tcp://*:5555")

    return clientSocket

def masterClientCommunication(clientSocket):
    while True:
        message = clientSocket.recv()
        print("Received request: %s" % message)

        #Do some 'work'
        time.sleep(1)

        if message == "UPLOAD":
            clientSocket.send(b"UUUUU")
        elif message == "DOWNLOAD":
            clientSocket.send("DDDDD")

def main():
    print("TRYING THINGS...")
    socketTemp = initializeClientSocket()
    masterClientCommunication(socketTemp)
    print(socketTemp)

main()