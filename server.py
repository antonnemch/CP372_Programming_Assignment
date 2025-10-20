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

        buffer = b""  # accumulate TCP stream here
        file_mode = False

        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            buffer += chunk

            # process all complete lines currently in buffer
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                msg = line.decode(errors="replace").strip()

                # handle one complete command line
                if not msg:
                    continue

                lower = msg.lower()

                if lower == "exit":
                    conn.send(b"Goodbye!")
                    # after replying, close connection
                    raise SystemExit

                elif lower == "status":
                    with lock:
                        response = "\n".join(
                            f"{c}: {info['connected']} - {info['disconnected'] or 'Active'}"
                            for c, info in clients_cache.items()
                        )
                    conn.send(response.encode())

                elif lower == "list":
                    try:
                        files = os.listdir(FILE_DIR)
                        conn.send("\n".join(files).encode())
                        file_mode = True
                    except Exception as e:
                        conn.send(f"Error listing files: {e}".encode())

                else:
                    file_path = os.path.join(FILE_DIR, msg)
                    if os.path.isfile(file_path) and file_mode:
                        try:
                            file_size = os.path.getsize(file_path)
                            # Send header first so client can exact-read
                            conn.sendall(f"FILE {msg} {file_size}\n".encode())
                            # Stream in chunks (don’t read whole file into RAM)
                            with open(file_path, "rb") as f:
                                while True:
                                    blob = f.read(4096)
                                    if not blob:
                                        break
                                    conn.sendall(blob)
                        except Exception as e:
                            conn.send(f"Error sending file: {e}".encode())
                    else:
                        conn.send(f"File {msg} does not exist, or your request didn't follow the list command".encode())
                    file_mode = False

    except SystemExit:
        pass  # deliberate exit path after 'exit'
    except ConnectionError:
        pass
    except Exception as e:
        print(f"Error handling client {client_name}: {e}")
        try:
            conn.send(f"Error: {e}\n".encode())
        except Exception:
            pass
    finally:
        with lock:
            if client_name in clients_cache:
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
