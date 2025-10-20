import socket
import threading
import os
import datetime

HOST = '127.0.0.1'
PORT = 65432
MAX_CLIENTS = 3
FILE_DIR = 'server_files'

clients_cache = {}
lock = threading.Lock()

def handle_client(conn, addr, client_name):
    try:
        with lock:
            clients_cache[client_name] = {
                'address': addr,
                'connected': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'disconnected': None
            }
        conn.send(f"Welcome {client_name}!".encode())

        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    break

                if data.lower() == "exit":
                    conn.send("Goodbye!".encode())

                    break
                elif data.lower() == "status":
                    with lock:
                        response = "\n".join([f"{c}: {info['connected']} - {info['disconnected'] or 'Active'}"
                                          for c, info in clients_cache.items()])
                    conn.send(response.encode())
                elif data.lower() == "list":
                    try:
                        files = os.listdir(FILE_DIR)
                        conn.send("\n".join(files).encode())
                    except Exception as e:
                        conn.send(f"Error listing files: {str(e)}".encode())
                elif os.path.exists(os.path.join(FILE_DIR, data)):
                    try:
                        file_path = os.path.join(FILE_DIR, data)
                        file_size = os.path.getsize(file_path)
                        # Send header first: "FILE <name> <size>"
                        header = f"FILE {data} {file_size}\n".encode()
                        conn.send(header)
                        # Then send the file content
                        with open(file_path, "rb") as f:
                            conn.sendall(f.read())
                    except Exception as e:
                        conn.send(f"Error sending file: {str(e)}".encode())
                else:
                    # Regular message, echo with ACK
                    conn.send(f"{data} ACK\n".encode())
            except ConnectionError:
                break
            except Exception as e:
                print(f"Error handling client {client_name}: {e}")
                try:
                    conn.send(f"Error: {str(e)}\n".encode())
                except:
                    break
    finally:
        # Always update the cache and close the connection
        with lock:
            if client_name in clients_cache:
                clients_cache[client_name]['disconnected'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.close()

    with lock:
        clients_cache[client_name]['disconnected'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.close()

def main():
    # Create file repository directory if it doesn't exist
    os.makedirs(FILE_DIR, exist_ok=True)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print("Server started...")

    while True:
        conn, addr = server_socket.accept()
        with lock:
            active_clients = sum(1 for info in clients_cache.values() if info['disconnected'] is None)
            next_client_number = len(clients_cache) + 1
        if active_clients >= MAX_CLIENTS:
            conn.send("Server full, try again later.".encode())
            conn.close()
            continue
        client_name = f"Client{next_client_number:02}"
        threading.Thread(target=handle_client, args=(conn, addr, client_name)).start()

if __name__ == "__main__":
    main()
