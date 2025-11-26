"""Minimal TCP file transfer client without UI."""
import argparse
import socket
import struct
from pathlib import Path

BUFFER_SIZE = 4096


def send_file(host: str, port: int, file_path: Path) -> None:
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = file_path.name
    name_bytes = filename.encode("utf-8")
    if len(name_bytes) > 65535:
        raise ValueError("Filename is too long (must be <= 65535 bytes when UTF-8 encoded)")

    file_size = file_path.stat().st_size
    header = struct.pack("!H", len(name_bytes)) + name_bytes + struct.pack("!Q", file_size)

    with socket.create_connection((host, port)) as sock:
        print(f"[*] Connected to {host}:{port}")
        sock.sendall(header)

        sent = 0
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)
                sent += len(chunk)

        print(f"[+] Sent '{filename}' ({sent} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple TCP file send client")
    parser.add_argument("host", help="Server host/IP")
    parser.add_argument("port", type=int, help="Server port")
    parser.add_argument("file", type=Path, help="Path to the file to send")

    args = parser.parse_args()
    send_file(args.host, args.port, args.file)


if __name__ == "__main__":
    main()
