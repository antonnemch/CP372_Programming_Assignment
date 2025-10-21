# CP372 Socket Programming Assignment
# Adam Rak - 210700280
# Anton Nemchinski - 169035377

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
                if not msg:
                    continue

                lower = msg.lower()

                # ====== EXIT COMMAND ======
                if lower == "exit":
                    conn.send(b"Goodbye!")
                    raise SystemExit

                # ====== STATUS COMMAND ======
                elif lower == "status":
                    with lock:
                        response = "\n".join(
                            f"{c}: {info['connected']} - {info['disconnected'] or 'Active'}"
                            for c, info in clients_cache.items()
                        )
                    conn.send(response.encode())

                # ====== LIST COMMAND ======
                elif lower == "list":
                    try:
                        files = os.listdir(FILE_DIR)
                        if files:
                            conn.send("\n".join(files).encode())
                        else:
                            conn.send(b"No files found in server repository.")
                        file_mode = True
                    except Exception as e:
                        conn.send(f"Error listing files: {e}".encode())

                # ====== FILE REQUEST / NORMAL MESSAGE ======
                else:
                    file_path = os.path.join(FILE_DIR, msg)

                    # If client just listed files, check if this is a valid file name
                    if file_mode:
                        if os.path.isfile(file_path):
                            try:
                                file_size = os.path.getsize(file_path)
                                conn.sendall(f"FILE {msg} {file_size}\n".encode())
                                with open(file_path, "rb") as f:
                                    while True:
                                        blob = f.read(4096)
                                        if not blob:
                                            break
                                        conn.sendall(blob)
                            except Exception as e:
                                conn.send(f"Error sending file: {e}".encode())
                        else:
                            conn.send(f"File '{msg}' does not exist on the server.".encode())

                    else:
                        # Normal message → Echo with ACK
                        conn.send(f"{msg} ACK".encode())

                    file_mode = False  # reset mode after any message

    except SystemExit:
        pass  # exit cleanly after 'exit'
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
