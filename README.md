# CP372 – Socket Programming Assignment (Fall 2025)

This repository contains a simple TCP client–server system implemented in Python for **CP372 – Computer Networks**.

## Repository Structure
- Server.py      # Multi-threaded TCP server (handles up to 3 clients; cache; file repo)
- Client.py      # Interactive client + driver code to spawn multiple clients for testing
- Report.pdf     # Implementation details, tests (with screenshots), challenges, improvements

## Files

### Server.py
- Accepts multiple client connections (multi-threaded, configurable max; default 3).
- Auto-assigns names to clients: `Client01`, `Client02`, …
- Maintains an in-memory cache of connections (start/end timestamps).
- Echoes messages with `ACK`.
- Special commands:
  - `status` → returns the cache contents.
  - `list` → lists files available in the server’s repository.
  - `<filename>` → streams the requested file if present; handles not-found cases.
  - `exit` → cleanly disconnects the client.

### Client.py
- Connects to the server and sends its assigned name.
- Sends messages; receives echoed `ACK`.
- Supports `status`, `list`, `<filename>`, and `exit`.
- **Driver code** included to **spawn N clients** for testing (see top-of-file usage/help).

### Report.pdf
- Design & implementation overview.
- Challenges and how they were addressed.
- Test results with screenshots covering rubric items.
- Possible improvements.

## How to Run

1. **Start the server**
   python Server.py
2.	Start one or more clients
   python Client.py
  	Use the driver section in Client.py to spawn multiple clients automatically for demo/testing.

Notes
- Demo is mandatory; ensure both group members’ names appear in the code headers and in Report.pdf.
- Socket communication is TCP only, as per assignment requirements.
  
