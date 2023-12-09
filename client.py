import zmq
import os

main_server_address = "" # TODO Write the main server address

def askStorageNode(upload=True, file_name=None):
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(main_server_address)

    if upload:
        client_socket.send_string("GET STORAGE NODE") # TODO Change the message for consistency
    else:
        client_socket.send_string(f"GET FILE {file_name}")
    storage_node_address = client_socket.recv_string()

    client_socket.close()
    return storage_node_address

def upload(storage_node_address, file_name):
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{storage_node_address}")

    with open(file_name, "rb") as file:
        file_data = file.read()
        client_socket.send_string(f"UPLOAD {file_data}")
        response = client_socket.recv_string()
        print(response)

    client_socket.close()

def download(storage_node_address, file_name, destination_folder="."):
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)
    client_socket.connect(f"tcp://{storage_node_address}")

    client_socket.send_string(f"DOWNLOAD {file_name}")
    file_data = client_socket.recv_string()

    destination_path = os.path.join(destination_folder, file_name)
    with open(destination_path, "wb") as file:
        file.write(file_data)

    client_socket.close()

if __name__ == "__main__":
    active = True
    while active:
        print("1. Upload File")
        print("2. Download File")
        print("3. Exit")
        option = input("What do you want to do?")
        if option == 1:
            file_name = input("Enter file name: ")
            storage_node_address = askStorageNode()
            upload(storage_node_address, file_name)
        elif option == 2:
            file_name = input("Enter file name: ")
            storage_node_address = askStorageNode(False, file_name)
            download(storage_node_address, file_name)
        elif option == 3:
            active = False
            print("Good bye!")
        else:
            print("Invalid input")