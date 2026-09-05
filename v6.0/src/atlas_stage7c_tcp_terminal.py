"""Atlas 6.0 Stage 7C Wi-Fi TCP terminal for Windows.

Connect the PC to the ESP32 Wi-Fi network first:
    SSID: ATLAS_6_0
    Password: Atlas6Stage7

Then run this file from its own folder:
    py atlas_stage7c_tcp_terminal.py

The program sends a heartbeat every 100 ms. If this program, Wi-Fi, or TCP
fails during a TCP-started motion, the ESP32 firmware stops and disarms Atlas.
"""

from __future__ import annotations

import socket
import sys
import threading
import time


ATLAS_HOST = "192.168.4.1"
ATLAS_PORT = 3333
CONNECT_TIMEOUT_SECONDS = 5.0
HEARTBEAT_INTERVAL_SECONDS = 0.10


class AtlasTerminal:
    def __init__(self) -> None:
        self.socket: socket.socket | None = None
        self.stop_event = threading.Event()
        self.send_lock = threading.Lock()

    def connect(self) -> None:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        connection.settimeout(CONNECT_TIMEOUT_SECONDS)
        connection.connect((ATLAS_HOST, ATLAS_PORT))
        connection.settimeout(0.5)
        self.socket = connection

    def send_line(self, line: str) -> bool:
        connection = self.socket
        if connection is None or self.stop_event.is_set():
            return False

        payload = (line.rstrip("\r\n") + "\n").encode("ascii", errors="strict")
        try:
            with self.send_lock:
                connection.sendall(payload)
            return True
        except OSError as error:
            if not self.stop_event.is_set():
                print(f"\n[Connection lost while sending: {error}]")
            self.stop_event.set()
            return False

    def heartbeat_loop(self) -> None:
        while not self.stop_event.wait(HEARTBEAT_INTERVAL_SECONDS):
            if not self.send_line("ping"):
                return

    def receive_loop(self) -> None:
        connection = self.socket
        if connection is None:
            return

        pending = b""
        while not self.stop_event.is_set():
            try:
                chunk = connection.recv(4096)
            except socket.timeout:
                continue
            except OSError as error:
                if not self.stop_event.is_set():
                    print(f"\n[Connection lost while receiving: {error}]")
                self.stop_event.set()
                return

            if not chunk:
                print("\n[ESP32 closed the TCP connection]")
                self.stop_event.set()
                return

            pending += chunk
            while b"\n" in pending:
                raw_line, pending = pending.split(b"\n", 1)
                text = raw_line.rstrip(b"\r").decode("utf-8", errors="replace")
                if text == "PONG":
                    continue
                print(text)

    def close(self, request_stop: bool) -> None:
        connection = self.socket
        if request_stop and connection is not None and not self.stop_event.is_set():
            self.send_line("stop")
            time.sleep(0.15)

        self.stop_event.set()
        if connection is not None:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        self.socket = None


def main() -> int:
    terminal = AtlasTerminal()

    print("Atlas 6.0 Stage 7C TCP Terminal")
    print(f"Connecting to {ATLAS_HOST}:{ATLAS_PORT} ...")
    try:
        terminal.connect()
    except OSError as error:
        print(f"Connection failed: {error}")
        print("Check that the PC is connected to Wi-Fi ATLAS_6_0.")
        return 1

    print("Connected. Type help, status, config, arm, stop, or a V5 command.")
    print("Type quit to send STOP and close the terminal.")

    receive_thread = threading.Thread(
        target=terminal.receive_loop,
        name="atlas-receiver",
        daemon=True,
    )
    heartbeat_thread = threading.Thread(
        target=terminal.heartbeat_loop,
        name="atlas-heartbeat",
        daemon=True,
    )
    receive_thread.start()
    heartbeat_thread.start()

    terminal.send_line("status")

    try:
        while not terminal.stop_event.is_set():
            try:
                command = input("atlas> ").strip()
            except EOFError:
                command = "quit"

            if not command:
                continue
            if command.lower() in {"quit", "exit"}:
                break

            try:
                command.encode("ascii", errors="strict")
            except UnicodeEncodeError:
                print("Commands must use ASCII letters, numbers, spaces, '-' or '.'.")
                continue

            if not terminal.send_line(command):
                break

    except KeyboardInterrupt:
        print("\nCtrl+C received; requesting STOP.")
    finally:
        terminal.close(request_stop=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
