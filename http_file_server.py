from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from os.path import join, isfile
from os import rename, remove, rmdir, listdir, fstat
from random import choices
from string import ascii_lowercase, digits
from shutil import copyfileobj
import argparse, hashlib, sys, contextlib, daemon
from daemon import pidfile

class HTTPFileServer(HTTPServer):
    def __init__(self, store_path: str = '.', block_size: int = 512*1024*1024, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.store_path = store_path
        self.block_size = block_size

class HTTPFileRequest(BaseHTTPRequestHandler):

    def _response(self, code: int, body: str):
        self.send_response(code)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body.encode())
    
    def do_GET(self):
        h = self.path[1:]
        if not h.isalnum():
            self._response(400, 'Bad hash passed\n')
            return
        
        file_path = join(self.server.store_path, h[:2], h)
        if not isfile(file_path):
            self._response(404, f'File {h} not found\n')
            return
        
        with open(file_path, 'rb') as f:
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{h}"')
            fs = fstat(f.fileno())
            self.send_header('Content-Length', str(fs.st_size))
            self.end_headers()
            copyfileobj(f, self.wfile, self.server.block_size)
    
    def do_POST(self):
    
        store_path = self.server.store_path
        block_size = self.server.block_size
        
        # generate tmp file
        tmp_path = join(store_path, 'tmp')
        Path(tmp_path).mkdir(parents=True, exist_ok=True)
        tmp_path = join(tmp_path, ''.join(choices(ascii_lowercase + digits, k=16)))
        
        # get hash of file and write to temp file            
        with open(tmp_path, 'wb') as tmp_file:
            length = int(self.headers['content-length'])
            h = hashlib.md5()
            data = self.rfile.read(min(length, block_size))
            while length > 0:
                h.update(data)
                tmp_file.write(data)
                length -= len(data)
                data = self.rfile.read(min(length, block_size))
        
        # save file
        store_path = join(store_path, h.hexdigest()[:2])
        Path(store_path).mkdir(parents=True, exist_ok=True)
        store_path = join(store_path, h.hexdigest())
        
        if isfile(store_path):
            # file with such hash already exists
            remove(tmp_path)
            self._response(409, f'File {h.hexdigest()} already exists\n')
            return
            
        # move file to required directory and rename
        rename(tmp_path, store_path)
        self._response(200, f'{h.hexdigest()}\n')
        
    def do_DELETE(self):
        h = self.path[1:]
        if not h.isalnum():
            self._response(400, 'Bad hash passed\n')
            return
        
        dir_path = join(self.server.store_path, h[:2])
        file_path = join(dir_path, h)
        if not isfile(file_path):
            self._response(404, f'File {h} not found\n')
            return
        
        try:
            remove(file_path)
        except Exception:
            pass
        
        if len(listdir(dir_path)) == 0:
            # directory is empty and can be deleted
            try:
                rmdir(dir_path)
            except Exception:
                pass
        
        self._response(200, f'Deleted {h}\n')
        

def parse_args():
    parser = argparse.ArgumentParser(description='HTTP file server.')
    parser.add_argument('--port', type=int, default=8080,
                        help='server port')
    parser.add_argument('--store_path', metavar='-s', type=str, default='.',
                        help='path to file storage')
    parser.add_argument('--block_size', metavar='-b', type=int, default=512*1024*1024,
                        help='buffer size for reading file content')
    parser.add_argument('--pid_file', metavar='-p', default='/var/run/http_file_server.pid',
                        help='path to pidfile')
    args = parser.parse_args()
    return args.port, args.store_path, args.block_size, args.pid_file


if __name__ == '__main__':
    port, store_path, block_size, pid_file = parse_args()
    server = HTTPFileServer(store_path, block_size, ('localhost', port), HTTPFileRequest)

    daemon_context = daemon.DaemonContext(pidfile=pidfile.TimeoutPIDLockFile(pid_file))
    daemon_context.files_preserve = [server.fileno()]
    
    with daemon_context:
        server.serve_forever()
