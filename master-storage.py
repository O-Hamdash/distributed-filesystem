import socket
import time
from collections import defaultdict
from threading import RLock, Thread

import zmq
import json
import os

persistent_dir = "./data/"
last_id_file = persistent_dir + "id"
fs_backup_file = persistent_dir + "backup.json"
os.makedirs(persistent_dir, exist_ok=True)

def generate_uid():
    last_generated_id = 0
    try:
        with open(last_id_file, "r") as file:
            last_generated_id = int(file.read())
    except FileNotFoundError:
        pass
    
    last_generated_id += 1
    
    with open(last_id_file, "w") as file:
        file.write(str(last_generated_id))
    
    return last_generated_id


class FileSystemObject:
    id_lock = RLock()

    def __init__(self, name, type, id=None):
        print("init", name)
        self.id = id
        if self.id == None:
            with FileSystemObject.id_lock:
                self.id = generate_uid()
        self.name = name
        self.type = type
        self.ip_address = None
        self.date_added = None
        self.date_modified = None
        self.editable = True
        self.contents = []
    
    def __str__(self):
        return f"FileSystemObject(id={self.id}, name={self.name}, type={self.type}, editable={self.editable})"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "ip_address": self.ip_address,
            "date_added": str(self.date_added),  # Convert datetime to string
            "date_modified": str(self.date_modified),  # Convert datetime to string
            "editable": self.editable,
            "contents": [obj.to_dict() for obj in self.contents],  # Recursively convert contents
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls(data["name"], data["type"], data["id"])
        instance.ip_address = data["ip_address"]
        instance.date_added = data["date_added"] if data["date_added"] else None
        instance.date_modified = data["date_modified"] if data["date_modified"] else None
        instance.editable = data["editable"]
        instance.contents = [cls.from_dict(obj_data) for obj_data in data["contents"]]
        return instance


if __name__ == "__main__":
    file_system_root = FileSystemObject(name="root", type="folder")
    file_system_root.contents.append(FileSystemObject(name="file1.txt", type="file"))
    file_system_root.contents.append(FileSystemObject(name="folder1", type="folder"))
    file_system_root.contents[1].contents.append(FileSystemObject(name="file2.txt", type="file"))


    file_system_root.editable = False

    # Serialize and save to a file
    with open(fs_backup_file, "w") as file:
        serialized_data = file_system_root.to_dict()
        json.dump(serialized_data, file)

    # Load and deserialize from the file
    with open(fs_backup_file, "r") as file:
        loaded_data = json.load(file)
        loaded_file_system = FileSystemObject.from_dict(loaded_data)


    print(loaded_file_system)
    for i in loaded_file_system.contents:
        print(i)