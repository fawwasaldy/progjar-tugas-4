import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import logging

class HttpRequestHandler:
    def __init__(self):
        self.sessions = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.html': 'text/html'
        }

    def _create_response(self, code=404, message='Not Found', body=b'', headers={}):
        """Membuat respons HTTP standar."""
        response_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Ensure body is bytes
        if not isinstance(body, bytes):
            body = str(body).encode()

        resp = [
            f"HTTP/1.0 {code} {message}",
            f"Date: {response_date}",
            "Connection: close",
            "Server: MySimpleServer/1.0",
            f"Content-Length: {len(body)}"
        ]
        
        # Add custom headers
        for key, value in headers.items():
            resp.append(f"{key}: {value}")
        
        # Combine headers and body
        response_header_str = "\r\n".join(resp) + "\r\n\r\n"
        
        return response_header_str.encode() + body

    def handle_request(self, data):
        """Memproses data request yang masuk."""
        # Split headers and body
        if isinstance(data, bytes):
            if b'\r\n\r\n' in data:
                headers_bytes, body = data.split(b'\r\n\r\n', 1)
                headers = headers_bytes.decode('utf-8')
            else:
                headers = data.decode('utf-8')
                body = b''
        else:
            return self._create_response(400, 'Bad Request', 'Invalid request data type')

        request_lines = headers.split("\r\n")
        if not request_lines:
            return self._create_response(400, 'Bad Request', 'Empty request')
        
        request_line = request_lines[0]
        parts = request_line.split(" ")
        if len(parts) != 3:
            return self._create_response(400, 'Bad Request', 'Invalid request line')

        method, object_address, _ = parts
        logging.warning(f"Request received: {method} {object_address}")

        all_headers = {h.split(': ')[0]: h.split(': ')[1] for h in request_lines[1:] if ': ' in h}

        if method.upper() == 'GET':
            return self.http_get(object_address, all_headers)
        elif method.upper() == 'POST':
            return self.http_post(object_address, all_headers, body)
        elif method.upper() == 'DELETE':
            return self.http_delete(object_address, all_headers)
        else:
            return self._create_response(405, 'Method Not Allowed', f"Method {method} not supported.")

    def http_get(self, object_address, headers):
        """Menangani request GET."""
        # Menghapus slash di awal jika ada
        if object_address.startswith('/'):
            object_address = object_address[1:]

        # Jika path kosong, anggap sebagai root
        if not object_address:
            return self._create_response(200, 'OK', 'Welcome to the simple web server!')

        # Cek apakah path adalah direktori
        if os.path.isdir(object_address):
            try:
                file_list = os.listdir(object_address)
                response_body = f"<h1>Directory Listing for /{object_address}</h1><ul>"
                for item in file_list:
                    response_body += f"<li>{item}</li>"
                response_body += "</ul>"
                return self._create_response(200, 'OK', response_body, {'Content-Type': 'text/html'})
            except Exception as e:
                logging.error(f"Error listing directory {object_address}: {e}")
                return self._create_response(500, 'Internal Server Error', f'Could not list directory: {e}')
        
        # Cek apakah file ada
        elif os.path.exists(object_address):
            try:
                with open(object_address, 'rb') as f:
                    content = f.read()
                
                _, file_extension = os.path.splitext(object_address)
                content_type = self.types.get(file_extension.lower(), 'application/octet-stream')
                return self._create_response(200, 'OK', content, {'Content-Type': content_type})
            except Exception as e:
                logging.error(f"Error reading file {object_address}: {e}")
                return self._create_response(500, 'Internal Server Error', f'Could not read file: {e}')
        else:
            return self._create_response(404, 'Not Found', f'The requested resource /{object_address} was not found.')

    def http_post(self, object_address, headers, body):
        """Menangani request POST untuk unggah file."""
        if object_address != '/upload':
            return self._create_response(400, 'Bad Request', "Uploads are only allowed to the /upload endpoint.")

        filename = headers.get('Filename')
        if not filename:
            return self._create_response(400, 'Bad Request', "Header 'Filename' is missing.")

        # Pastikan direktori 'upload' ada
        upload_dir = 'upload'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        file_path = os.path.join(upload_dir, os.path.basename(filename))
        
        try:
            with open(file_path, 'wb') as f:
                f.write(body)
            return self._create_response(200, 'OK', f"File '{filename}' uploaded successfully.")
        except Exception as e:
            logging.error(f"Failed to save file '{filename}': {e}")
            return self._create_response(500, 'Internal Server Error', f"Error saving file: {e}")

    def http_delete(self, object_address, headers):
        """Menangani request DELETE."""
        if object_address.startswith('/'):
            object_address = object_address[1:]
        
        file_path = os.path.join('upload', object_address)

        if not os.path.exists(file_path):
            return self._create_response(404, 'Not Found', f"File '{object_address}' not found.")
        
        if not os.path.isfile(file_path):
            return self._create_response(400, 'Bad Request', f"Path '{object_address}' is not a file.")

        try:
            os.remove(file_path)
            return self._create_response(200, 'OK', f"File '{object_address}' has been deleted.")
        except Exception as e:
            logging.error(f"Failed to delete file '{object_address}': {e}")
            return self._create_response(500, 'Internal Server Error', f"Error deleting file: {e}")