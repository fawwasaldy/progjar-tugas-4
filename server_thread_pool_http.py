import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpRequestHandler # <-- Impor disesuaikan

def handle_client(connection, address, handler):
    """Fungsi untuk menangani koneksi dari satu klien."""
    logging.info(f"Connection from {address}")
    try:
        # Menerima data secara lengkap
        full_data = b''
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                break
            full_data += chunk
            # Jika request relatif kecil, kita bisa asumsikan selesai setelah paket pertama
            if len(chunk) < 4096:
                break
        
        if full_data:
            response = handler.handle_request(full_data)
            connection.sendall(response)
    except Exception as e:
        logging.error(f"Error handling client {address}: {e}")
    finally:
        connection.close()
        logging.info(f"Connection from {address} closed.")

def start_server():
    """Memulai server utama dengan Thread Pool."""
    host = '0.0.0.0'
    port = 8885
    max_workers = 20
    
    # Inisialisasi handler request dari file http.py
    handler = HttpRequestHandler()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(10)
        logging.warning(f"Server (Thread Pool) started on http://{host}:{port}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while True:
                connection, client_address = server_socket.accept()
                executor.submit(handle_client, connection, client_address, handler)
    except Exception as e:
        logging.error(f"Server failed to start: {e}")
    finally:
        server_socket.close()
        logging.warning("Server shut down.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_server()