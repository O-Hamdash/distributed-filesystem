import socket
import time
from collections import defaultdict
from threading import RLock, Thread

import zmq
import json

class FileSystemObject:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.ip_address = None
        self.date_added = None
        self.date_modified = None
        self.editable = True
        self.contents = []
    
    def __str__(self):
        return f"FileSystemObject(name={self.name}, type={self.type}, editable={self.editable})"

    def to_dict(self):
        return {
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
        instance = cls(data["name"], data["type"])
        instance.ip_address = data["ip_address"]
        instance.date_added = data["date_added"] if data["date_added"] else None
        instance.date_modified = data["date_modified"] if data["date_modified"] else None
        instance.editable = data["editable"]
        instance.contents = [cls.from_dict(obj_data) for obj_data in data["contents"]]
        return instance

file_system_root = FileSystemObject(name="root", type="folder")
file_system_root.contents.append(FileSystemObject(name="file1.txt", type="file"))
file_system_root.contents.append(FileSystemObject(name="folder1", type="folder"))
file_system_root.contents[1].contents.append(FileSystemObject(name="file2.txt", type="file"))


file_system_root.editable = False

# Serialize and save to a file
with open("file_system.json", "w") as file:
    serialized_data = file_system_root.to_dict()
    json.dump(serialized_data, file)

# Load and deserialize from the file
with open("file_system.json", "r") as file:
    loaded_data = json.load(file)
    loaded_file_system = FileSystemObject.from_dict(loaded_data)


print(loaded_file_system)