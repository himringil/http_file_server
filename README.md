# Daemonized HTTP file server

Server allows to upload, download and delete files on server.
Files uploaded to 'store_path/ab/abcd1234...' where subdirectory 'ab' is first two letters of md5 hash and filename 'abcd1234...' is md5 hash.

## Usage

**Upload file**
```
curl http://localhost:8080 -d "@filename.txt" -X POST
```

If file with same hash already exists it return code `409 Conflict`.

**Download file with specified hash:**
```
curl http://localhost:8080/80322b14cfc2aac3b5bcd3585a11b9f4 -o result.txt
```
**Delete file with specified hash:**
```
curl http://localhost:8080/8d3267f1509d2353897400fd67b8862e -X DELETE
```
If hash not passed or have bad format (not alphanumeric) it return code  `400 Bad Request`.

If file with passed hash not exists it return code  `404 или Not Found`.