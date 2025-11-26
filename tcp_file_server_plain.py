"""Minimal TCP file transfer server without UI.

The server expects a simple binary protocol from the client:
- 2 bytes: big-endian unsigned short indicating the filename length (in bytes)
- filename bytes encoded in UTF-8
- 8 bytes: big-endian unsigned long long representing the file size
- file content bytes
"""
import argparse
import socket
import struct
from pathlib import Path
from typing import Optional

BUFFER_SIZE = 4096


def recv_exact(conn: socket.socket, size: int) -> Optional[bytes]:
    """Receive exactly ``size`` bytes or return ``None`` if the connection closes early."""
    data = bytearray()
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)


def handle_client(conn: socket.socket, addr, output_dir: Path) -> None:
    print(f"[*] Connection from {addr}")

    raw_name_len = recv_exact(conn, 2)
    if not raw_name_len:
        print("[!] Connection closed before receiving filename length")
        return

    name_len = struct.unpack("!H", raw_name_len)[0]
    name_bytes = recv_exact(conn, name_len)
    if not name_bytes:
        print("[!] Connection closed before receiving filename")
        return

    filename = Path(name_bytes.decode("utf-8", errors="replace")).name

    raw_size = recv_exact(conn, 8)
    if not raw_size:
        print("[!] Connection closed before receiving file size")
        return

    file_size = struct.unpack("!Q", raw_size)[0]

    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / filename

    received = 0
    with dest_path.open("wb") as f:
        while received < file_size:
            chunk = conn.recv(min(BUFFER_SIZE, file_size - received))
            if not chunk:
                print("[!] Connection closed during file transfer")
                return
            f.write(chunk)
            received += len(chunk)

    print(f"[+] Received '{filename}' ({file_size} bytes) -> {dest_path}")


def run_server(host: str, port: int, output_dir: Path) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1)
        print(f"[+] Listening on {host}:{port}, saving files to '{output_dir}'")
        while True:
            try:
                conn, addr = server.accept()
            except KeyboardInterrupt:
                print("\n[!] Server shutting down")
                break

            with conn:
                try:
                    handle_client(conn, addr, output_dir)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    print(f"[!] Error while handling client {addr}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple TCP file receive server")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=2501, help="Port to bind (default: 2501)")
    parser.add_argument(
        "--output-dir",
        default="received_files",
        type=Path,
        help="Directory to store incoming files (default: received_files)",
    )

    args = parser.parse_args()
    run_server(args.host, args.port, args.output_dir)


if __name__ == "__main__":
    main()
