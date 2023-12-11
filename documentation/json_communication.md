# JSON Communication
This documentation lists all details related to communications and messages used in this project
## General JSON Format
All messages and requests in the system will be in JSON format, there will be no string requests. This is to unify the request form so that it would be easier to deal with.

The format of all JSON messages will be:
```
{
	"op": "...",
	"src_ip": "...",
	"path": "...",
	"msg": "...",
	"dst_ip": "...",
	"port": "...",
	"file_id": "..."
}
```
These 7 fields will be enough for all communications on the system. A function called `generate_json()` will be used to generate this json message as a python dictionary and return it. The definition of the function will be:
`def generate_json(op, src_ip=None, path=None, msg=None, dst_ip=None, port=None, file_id=None)`

So everything except the op parameter will be `None` by default. When calling the function to generate a json for a specific communication, the necessary parameters for the operation can be set to the desired value. For example, `generate_json("upload", src_ip=get_ip_address(), path="/folder1/file.txt")` will generate the json that the client will use to upload file.txt. After that, the master will recieve it and will understand from the op value what other parameters the json contains (which ones are not `None`).

## Operations
Below are all the operations supported by the system.
### 1. Upload
This will be used by the client to signal to the master that it wants to  upload a file. The json generator function will be called as so: `generate_json("upload", src_ip=get_ip_address(), path="/folder1/file.txt")`
### 2. Download
Same as upload, it will be used by the client and the json generator will be called as so: `generate_json("download", src_ip=get_ip_address(), path="/folder1/file.txt")`
### 3. Available_storage
This will be used by the master to ask all storage nodes to send their available storage. The json generator will be called as so: `generate_json("available_storage")`
### 4. Available_storage_reply
This will be used by the storage nodes to reply with their available storage space. The json generator: `generate_json("available_storage_reply", src_ip=get_ip_address(), msg=str(get_available_storage()))`
### 5. Port_request
This will be called by the master node to the storage node or to the client in order for it to create a port for file upload . The json generator: `generate_json("port_request", file_id=chosen_file_id_by_master)`
### 6. Port_reply
This will be the reply to the master sent by the storage node. The json generator: `generate_json("port_reply", src_ip=get_ip_address(), port=generated_port)`
### 7. Upload_details
This will be used by the master to send the upload details to the client. Json generator: `generate_json("upload_details",dst_ip=chosen_storage_ip , port=port_generated_by_storage)`
### 8. Upload_success
This will be used by the storage to notify the master that it received the file. Json generator: `generate_json("upload_success",src_ip=get_ip_address(), file_id=chosen_file_id_by_master)`
### 9. Download_details
This will be sent from the master to the storage node when the client wants to download a file. The json generator: `generate_json("download_details", dst_ip=ip_of_client_requesting_download, file_id=id_of_file_to_download)`
### 10. Download_error
This will be sent from the master to the client in case of an incorrect filename. The json will be: `generate_json("download_error")`
