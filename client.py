# CP372 Socket Programming Assignment
# Adam Rak - 210700280
# Anton Nemchinski - 169035377

import socket
import argparse
import os
import sys
from typing import Tuple

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432
RECV_BUF = 4096  # (4 KiB)

def recv_exact(sock: socket.socket, nbytes: int) -> bytes:
    """Receive exactly nbytes or raise if the connection ends early."""
    data = bytearray()
    while len(data) < nbytes:
        chunk = sock.recv(nbytes - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before expected bytes arrived.")
        data.extend(chunk)
    return bytes(data)

def recv_line(sock: socket.socket) -> bytes:
    """Receive bytes until a single (\\n). Returns the line."""
    line = bytearray()
    while True:
        ch = sock.recv(1)
        if not ch:
            break
        if ch == b"\n":
            break
        line.extend(ch)
    return bytes(line)

def parse_file_header(header: bytes) -> Tuple[str, int]:
    """
    Parse b"FILE <name> <size>" -> (name, size).
    Raises ValueError if not a valid header.
    """
    parts = header.decode(errors="replace").strip().split()
    if len(parts) < 3 or parts[0].upper() != "FILE":
        raise ValueError("Not a FILE header")
    size = int(parts[-1])
    name = " ".join(parts[1:-1])
    return name, size

def save_file_safely(filename: str, data: bytes) -> str:
    """Save bytes into CWD"""
    filename = os.path.basename(filename)
    out_path = os.path.join(os.getcwd(), filename)
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path

def recv_text_reply(sock: socket.socket) -> str:
    """Read a short text reply"""
    data = sock.recv(RECV_BUF)
    return data.decode(errors="replace")

def receive_file_flow(sock: socket.socket, requested_name: str) -> None:
    """
    Handle both file downloads and text responses:
    1. For files: expects 'FILE name size' header followed by content
    2. For text: prints the text response
    """
    # First try to receive a line (either FILE header or text response)
    header = recv_line(sock)
    if not header:
        print("[error] Connection closed while waiting for response.")
        return

    # Try to parse as FILE header
    try:
        name, size = parse_file_header(header)
        print(f"[info] Receiving file: {name} ({size} bytes)")
        content = recv_exact(sock, size)
        path = save_file_safely(name or requested_name, content)
        print(f"[downloaded] {path} ({len(content)} bytes)")
        return
    except ValueError:
        # Not a file header, must be a text response
        text = header.decode(errors="replace")
        if text.strip():  # Only print non-empty responses
            print(text)

def run_client(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((host, port))
        except ConnectionRefusedError:
            print("[error] Connection refused. Is the server running?")
            return

        # Welcome banner (text)
        try:
            welcome = recv_text_reply(sock)
        except Exception:
            welcome = ""
        if welcome:
            print(welcome)

        awaiting_filename = False  # <-- NEW: only true immediately after 'list'

        # REPL loop
        while True:
            try:
                msg = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[info] Exiting client.")
                break

            if not msg:
                continue

            try:
                # Send every command as a line for framing
                sock.sendall((msg + "\n").encode())
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                print("[error] Server closed the connection.")
                break

            lower = msg.lower()

            if lower == "exit":
                # Expect a small text reply, then quit
                try:
                    reply = recv_text_reply(sock)
                except (ConnectionAbortedError, ConnectionResetError):
                    reply = "Disconnected by server."
                if reply:
                    print(reply)
                print("[info] Disconnected.")
                break

            elif lower == "list":
                # 'list' returns a text listing...
                reply = recv_text_reply(sock)
                print(reply)
                # ...and NOW it is file time: the very next user input is a filename
                awaiting_filename = True

            elif awaiting_filename:
                # Treat THIS input as a filename request. Server should reply:
                #   FILE <name> <size>\n  + content   (or)   text error line
                try:
                    receive_file_flow(sock, requested_name=msg)
                except (ConnectionAbortedError, ConnectionResetError):
                    print("Disconnected by server.")
                    break
                finally:
                    # Whether success or error, only the NEXT input after 'list' is a filename
                    awaiting_filename = False

            else:
                # Not exit/list and not file time → expect a text reply (ACK, status, errors, etc.)
                reply = recv_text_reply(sock)
                if reply.strip():
                    print(reply)

def run_many_clients(host: str, port: int, n: int) -> None:
    import threading
    threads = []
    for _ in range(n):
        t = threading.Thread(target=run_client, args=(host, port), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def main():
    parser = argparse.ArgumentParser(description="CP372 TCP Client")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port (default: 65432)")
    parser.add_argument("--clients", type=int, default=1, help="Spawn N clients (interactive).")
    args = parser.parse_args()

    if args.clients <= 1:
        run_client(args.host, args.port)
    else:
        run_many_clients(args.host, args.port, args.clients)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[info] Interrupted. Bye!")
        sys.exit(0)
