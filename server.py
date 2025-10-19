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
    with lock:
        clients_cache[client_name] = {
            'address': addr,
            'connected': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'disconnected': None
        }
    conn.send(f"Welcome {client_name}!".encode())

    while True:
        data = conn.recv(1024).decode().strip()
        if not data:
            break

        if data.lower() == "exit":
            conn.send("Goodbye!".encode())
            break
        elif data.lower() == "status":
            response = "\n".join([f"{c}: {info['connected']} - {info['disconnected'] or 'Active'}"
                                  for c, info in clients_cache.items()])
            conn.send(response.encode())
        elif data.lower() == "list":
            files = os.listdir(FILE_DIR)
            conn.send("\n".join(files).encode())
        elif os.path.exists(os.path.join(FILE_DIR, data)):
            with open(os.path.join(FILE_DIR, data), "rb") as f:
                conn.sendall(f.read())
        else:
            conn.send((data + " ACK").encode())

    with lock:
        clients_cache[client_name]['disconnected'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print("Server started...")

    client_count = 0

    while True:
        conn, addr = server_socket.accept()
        if client_count >= MAX_CLIENTS:
            conn.send("Server full, try again later.".encode())
            conn.close()
            continue
        client_count += 1
        client_name = f"Client{client_count:02}"
        threading.Thread(target=handle_client, args=(conn, addr, client_name)).start()

if __name__ == "__main__":
    main()
