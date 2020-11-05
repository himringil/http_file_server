# Daemonized HTTP file server

Server allows to upload, download and delete files on server.
Files uploaded to 'store_path/ab/abcd1234...' where subdirectory 'ab' is first two letters of md5 hash of file and filename 'abcd1234...' is md5 hash of file.

## Usage

**Run daemon**
```
sudo python3 http_file_server.py --port 8080 --store_path /home/user/store --block_size 1024 --pid_file /var/run/http_file_server.pid
```

**Upload file**
```
curl http://localhost:8080 --data-binary "@filename.txt" -X POST
```

**Download file with specified hash:**
```
curl http://localhost:8080/80322b14cfc2aac3b5bcd3585a11b9f4 -o result.txt
```

**Delete file with specified hash:**
```
curl http://localhost:8080/80322b14cfc2aac3b5bcd3585a11b9f4 -X DELETE
```

## Description

**Upload file**

Server reads input file by blocks with size block_size, compute hash and write input file to temporary file. Checks uniqueness of hash, moves temporary file to required directory and renames to md5-based name. Returns hash of new file.

Return codes:
- `200 OK` if file successfully uploaded.
- `409 Conflict` if file with same hash already exists.

**Download file with specified hash:**

Server gets hash passed in path. Checks it is alphanumerical. Checks file exists. Sets attachment header and returns file content.

Return codes:
- `200 OK` if file successfully downloaded.
- `400 Bad Request` if hash not passed or have bad format (not alphanumeric).
- `404 Not Found` if file with passed hash not exists.

**Delete file with specified hash:**

Server gets hash passed in path. Checks it is alphanumerical. Checks file exists. Deletes file. If file directory is empty, deletes it too.

Return codes:
- `200 OK` if file successfully deleted
- `400 Bad Request` if hash not passed or have bad format (not alphanumeric).
- `404 Not Found` if file with passed hash not exists.

