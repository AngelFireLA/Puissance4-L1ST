import socket
import threading

def receive_messages(sock):
    """Continuously receive messages from the server."""
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if data:
                # You can add message parsing here.
                print("Received:", data.strip())
            else:
                break
        except Exception as e:
            print("Receive error:", e)
            break

def main():
    server_ip = input("Enter server IP address: ")  # e.g., 'localhost' or a remote IP
    port = 12345
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, port))
    print("Connected to game server.")

    # Start a thread to listen for messages from the server.
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    # Main loop: type messages (in your game these will be moves or commands)
    try:
        while True:
            message = input("Enter your move (or 'exit' to quit): ")
            if message.lower() == 'exit':
                break
            client_socket.sendall(message.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        client_socket.close()
        print("Disconnected.")

if __name__ == '__main__':
    main()
