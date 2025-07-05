import socket
import logging
from concurrent.futures import ProcessPoolExecutor
from http import HttpRequestHandler

def handle_client_data(client_data, address):
    """Fungsi untuk memproses data dari klien di process terpisah."""
    logging.info(f"Processing request from {address}")
    try:
        # Create a new handler instance for each process
        handler = HttpRequestHandler()
        
        if client_data:
            response = handler.handle_request(client_data)
            return response
    except Exception as e:
        logging.error(f"Error processing request from {address}: {e}")
        return b"HTTP/1.1 500 Internal Server Error\r\n\r\nInternal Server Error"
    
    return b"HTTP/1.1 400 Bad Request\r\n\r\nBad Request"

def start_server():
    """Memulai server utama dengan Process Pool."""
    host = '0.0.0.0'
    port = 8889 # Port berbeda untuk process pool
    max_workers = 20
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(10)
        logging.warning(f"Server (Process Pool) started on http://{host}:{port}")

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            while True:
                connection, client_address = server_socket.accept()
                logging.info(f"Connection from {client_address}")
                
                try:
                    # Receive data in main process
                    full_data = b''
                    while True:
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        full_data += chunk
                        if len(chunk) < 4096:
                            break
                    
                    if full_data:
                        # Submit data processing to worker process
                        future = executor.submit(handle_client_data, full_data, client_address)
                        response = future.result()  # Get the response
                        connection.sendall(response)
                    
                except Exception as e:
                    logging.error(f"Error handling client {client_address}: {e}")
                finally:
                    connection.close()
                    logging.info(f"Connection from {client_address} closed.")
                    
    except Exception as e:
        logging.error(f"Server failed to start: {e}")
    finally:
        server_socket.close()
        logging.warning("Server shut down.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_server()