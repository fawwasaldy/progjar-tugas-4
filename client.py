import socket
import os
import sys
import logging
import argparse

def create_socket(destination_address='localhost', port=8885):
    """Menciptakan dan menghubungkan socket ke server."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.info(f"Connecting to {destination_address}:{port}")
        sock.connect(server_address)
        return sock
    except Exception as e:
        logging.error(f"Error creating socket: {e}")
        return None

def send_request(host, port, request_data):
    """Mengirim data request ke server dan menerima respons."""
    sock = create_socket(host, port)
    if not sock:
        print("Connection to server failed.")
        return
    
    try:
        if isinstance(request_data, str):
            request_data = request_data.encode()
            
        sock.sendall(request_data)
        
        # Menerima respons secara keseluruhan
        response_data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            
        print(response_data.decode(errors="ignore"))
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        sock.close()

def list_files(args):
    """Membangun dan mengirim request GET untuk melihat daftar file."""
    request = f"GET /{args.dir} HTTP/1.0\r\n\r\n"
    send_request(args.host, args.port, request)

def upload_file(args):
    """Membangun dan mengirim request POST untuk mengunggah file."""
    local_path = args.file
    if not os.path.exists(local_path):
        print(f"Error: Local file '{local_path}' not found.")
        return

    with open(local_path, "rb") as f:
        content = f.read()

    filename = os.path.basename(local_path)
    
    headers = [
        f"POST /upload HTTP/1.0",
        f"Filename: {filename}",
        f"Content-Length: {len(content)}",
        "\r\n"
    ]
    request_data = "\r\n".join(headers).encode() + content
    send_request(args.host, args.port, request_data)

def delete_file(args):
    """Membangun dan mengirim request DELETE untuk menghapus file."""
    remote_path = args.file
    request = f"DELETE /{remote_path} HTTP/1.0\r\n\r\n"
    send_request(args.host, args.port, request)

def main():
    """Fungsi utama untuk parsing argumen CLI dan menjalankan perintah."""
    parser = argparse.ArgumentParser(
        description="CLI Client for custom HTTP Server.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--host', default='localhost', help='Server host address (default: localhost)')
    parser.add_argument('--port', type=int, default=8885, help='Server port number (default: 8885)')

    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # Perintah untuk 'list'
    parser_list = subparsers.add_parser('list', help='List files in a directory on the server')
    parser_list.add_argument('dir', type=str, help='The directory on the server to list (e.g., "upload")')
    parser_list.set_defaults(func=list_files)

    # Perintah untuk 'upload'
    parser_upload = subparsers.add_parser('upload', help='Upload a file to the server')
    parser_upload.add_argument('file', type=str, help='The local path of the file to upload')
    parser_upload.set_defaults(func=upload_file)

    # Perintah untuk 'delete'
    parser_delete = subparsers.add_parser('delete', help='Delete a file on the server')
    parser_delete.add_argument('file', type=str, help='The path of the file to delete on the server')
    parser_delete.set_defaults(func=delete_file)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()