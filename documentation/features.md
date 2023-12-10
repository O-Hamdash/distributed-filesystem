# Features to Implement
## Upload Files
1. The client contacts the main server and asks for a storage node ip and port
2. The main server assings a node and sends back the ip/port to client
3. The client uploads the files to that storage node
4. The storage node notifies the server node that the trasfer is successful
5. The main server then assigns N nodes where the data will be replicated
6. The replication process is done peer to peer
## Download Files
1. The client requests a file
2. The main server assigns the task to one storage node
3. The storage node sets the ip address and port and informs the main server
4. The main server informs the client with the ip/port of the storage node
5. The client downloads the file
6. The storage node informs the main node if any errors happen
## Replication
1. After a file is uploaded to a storage node, the storage node asks the main server for the list of replication nodes
2. The main server decides who to replicate to based on available storage
3. The File is then replicated by peer-to-peer connection
4. The initial storage node sends the file to the next replication node with the replication list
5. The second node will do the same to the third node and so on...
6. At each storage node the status is reported to the main server
7. When the data reaches the final storage node, a message will be sent to the main server stating that the replication is completed
## Command Line Interface (CLI)
1. After running the .py script, the CLI will show
2. The ip address of the main server can be provided and then the connection will automatically be established
3. It will take commands like (ls, cd, pwd...)
4. For uploading the command put will be used, for download it will be get
## Browse Files
1. The client should be able to see a full tree of files available in the filesystem and run commands like ls and check directory sizes and so on...
## Search for Files
1. The client should be able to search for files by using the find command
## Multi User
1. Multiple users can login with different usernames and passwords
2. Each user will have their own files and they cannot see other user's files
3. There will be a shared user without a password that can be used by everyone
