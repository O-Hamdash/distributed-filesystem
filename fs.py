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
    def __init__(self, name, type, ip_address=None, id=None):
        self.id = id
        if self.id == None:
            self.id = generate_uid()
        self.name = name
        self.type = type
        self.ip_address = ip_address
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

# Returns path of the file if found, otherwise returns None
def search_file(file_system: FileSystemObject, file_name, current_path="", start_path="/"):
    if (start_path != "/") & (len(current_path) == 0):
        path_dirs = start_path.split('/')

        curr_fs_dir = file_system
        for dir in path_dirs:
            for fs_dir in curr_fs_dir.contents:
                if fs_dir.name == dir:
                    current_path = f"{current_path}/{dir}"
                    curr_fs_dir = fs_dir
                    break
        
        file_system = curr_fs_dir

    for item in file_system.contents:
        if item.type == "file" and item.name == file_name:
            return f"{current_path}/{file_name}"
        elif item.type == "folder":
            path = search_file(item, file_name, f"{current_path}/{item.name}")
            if path:
                return path
    return None

def search_local_file(file_system: FileSystemObject, file_name, current_path="", local_path="/"):
    if (local_path != "/") & (len(current_path) == 0):
        path_dirs = local_path.split('/')

        curr_fs_dir = file_system
        for dir in path_dirs:
            for fs_dir in curr_fs_dir.contents:
                if fs_dir.name == dir:
                    current_path = f"{current_path}/{dir}"
                    curr_fs_dir = fs_dir
                    break
        
        file_system = curr_fs_dir
    
    for item in file_system.contents:
        if item.type == "file" and item.name == file_name:
            return f"{current_path}/{file_name}"
    return None

def get_object_by_path(file_system: FileSystemObject, file_path):
    path_dirs = file_path.split('/')

    print(path_dirs)

    curr_fs_dir = file_system
    if len(path_dirs) > 2:
        for dir in path_dirs:
            found = False
            for fs_dir in curr_fs_dir.contents:
                if fs_dir.name == dir:
                    curr_fs_dir = fs_dir
                    found = True
                    break

            if not found:
                # If any directory in the path is not found, return None
                return None

    # The last item in path_dirs is the file name
    file_name = path_dirs[-1]

    # Search for the file in the current directory
    for item in curr_fs_dir.contents:
        if item.type == "file" and item.name == file_name:
            return item

    # If the file is not found in the current directory, return None
    return None

def get_file_id_by_path(file_system: FileSystemObject, file_path):
    path_dirs = file_path.split('/')

    curr_fs_dir = file_system
    for dir in path_dirs:
        found = False
        for fs_dir in curr_fs_dir.contents:
            if fs_dir.name == dir:
                curr_fs_dir = fs_dir
                found = True
                break

        if not found:
            # If any directory in the path is not found, return None
            return None

    # The last item in path_dirs is the file name
    file_name = path_dirs[-1]

    # Search for the file in the current directory
    for item in curr_fs_dir.contents:
        if item.type == "file" and item.name == file_name:
            return item.id

    # If the file is not found in the current directory, return None
    return None


def get_object_by_id(file_system: FileSystemObject, target_id):
    if file_system.id == target_id:
        return file_system

    for item in file_system.contents:
        result = get_object_by_id(item, target_id)
        if result:
            return result

    # If the ID is not found in the current object or its contents
    return None


def add(filesystem: FileSystemObject, path: str, type: str, ip_address=None):
    path_dirs = path.split('/')

    path_dirs.pop(0)

    to_add = path_dirs.pop()

    curr_fs_dir = filesystem
    for dir in path_dirs:
        found = False
        for fs_dir in curr_fs_dir.contents:
            if fs_dir.name == dir:
                curr_fs_dir = fs_dir
                found = True
                break

        if (found == False) & (len(path_dirs) > 0):
            print("The path provided does not exist")
            return
    
    for i in curr_fs_dir.contents:
        if (i.name == to_add) & (i.type == type):
            print(f"{type} with name {to_add} already exists in this location")
            return

    file = FileSystemObject(name=to_add, type=type, ip_address=ip_address)
    curr_fs_dir.contents.append(file)

    return file
        
def delete(filesystem: FileSystemObject, path: str):
    path_dirs = path.split('/')

    to_del = path_dirs.pop()

    curr_fs_dir = filesystem
    for dir in path_dirs:
        for fs_dir in curr_fs_dir.contents:
            if fs_dir.name == dir:
                curr_fs_dir = fs_dir
                break

    success = False
    i = -1
    for item in curr_fs_dir.contents:
        i += 1
        if item.name == to_del:
            curr_fs_dir.contents.pop(i)
            success = True

    if not success:
        print(f"no such item: {path}")

""" if __name__ == "__main__":
    try:
        # Load and deserialize from the file
        with open(fs_backup_file, "r") as file:
            loaded_data = json.load(file)
            file_system_root = FileSystemObject.from_dict(loaded_data)
    except FileNotFoundError:
        file_system_root = FileSystemObject(name="/", type="folder")
        file_system_root.contents.append(FileSystemObject(name="folder1", type="folder"))
        file_system_root.contents[0].contents.append(FileSystemObject(name="folder2", type="folder"))
        file_system_root.contents[0].contents.append(FileSystemObject(name="folder3", type="folder"))

        file_system_root.editable = False

    add(file_system_root, "/folder1", "folder")
    add(file_system_root, "/folder1/folder2", "folder")
    add(file_system_root, "/folder1/folder3", "folder")

    add(file_system_root, "/folder1/folder3/file1.txt", "file")
    add(file_system_root, "/folder1/folder2/file1.txt", "file")
    add(file_system_root, "/file1.txt", "file")

    delete(file_system_root, "/")
    add(file_system_root, "/folder1", "folder")


    # Serialize and save to a file
    with open(fs_backup_file, "w") as file:
        serialized_data = file_system_root.to_dict()
        json.dump(serialized_data, file) """