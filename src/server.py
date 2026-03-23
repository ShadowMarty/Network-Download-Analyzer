import socket
import ssl
import threading
import os

# Get absolute paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

HOST = "0.0.0.0"
PORT = 8000
FILE = os.path.join(PROJECT_ROOT, "data", "testfile.bin")
CERT_FILE = os.path.join(PROJECT_ROOT, "data", "server.crt")
KEY_FILE = os.path.join(PROJECT_ROOT, "data", "server.key")

def handle_client(ssl_socket, addr):
    """Handle incoming client request over SSL/TLS connection."""
    try:
        # Read HTTP request until we get complete headers (empty line = \r\n\r\n)
        request = b""
        while b"\r\n\r\n" not in request:
            data = ssl_socket.recv(65536)
            if not data:
                return
            request += data
        
        print(f"[Client] {addr[0]}:{addr[1]}")
        
        # Send file or 404 Not Found
        try:
            with open(FILE, "rb") as f:
                body = f.read()
            # HTTP/1.1 200 OK with Content-Length header
            response = b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body
        except FileNotFoundError:
            # Return 404 if test file doesn't exist
            response = b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
        
        # Send HTTP response over SSL/TLS
        ssl_socket.sendall(response)
    except Exception as e:
        print(f"[Error] {addr[0]}:{addr[1]} - {e}")
    finally:
        ssl_socket.close()

def create_ssl_context():
    """Create SSL/TLS context - loads pre-generated certificates."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    return ctx

if __name__ == "__main__":
    # Initialize SSL
    ssl_ctx = create_ssl_context()
    if ssl_ctx is None:
        print("[Error] Failed to initialize SSL/TLS")
        exit(1)
    
    # Create TCP server socket
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR: allows immediate restart after crash (socket in TIME_WAIT)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
    except OSError as e:
        print(f"[Error] Failed to bind {HOST}:{PORT}")
        print(f"  Is port already in use? Try a different port.")
        exit(1)
    
    # Listen with backlog of 5 pending connections
    server_socket.listen(5)
    print("\n" + "="*60)
    print("█ SERVER (SSL/TLS Enabled)")
    print("="*60)
    print(f"Status: ✓ Listening on {HOST}:{PORT}")
    print(f"Mode:   SSL/TLS Encryption (HTTPS)")
    print(f"File:   data/testfile.bin (20 MB)")
    print("="*60)
    print("Waiting for client connections...\n")
    
    try:
        while True:
            try:
                # Accept client connection (blocks until client connects)
                client_socket, client_addr = server_socket.accept()
                
                # Wrap raw TCP socket with SSL/TLS encryption
                try:
                    ssl_socket = ssl_ctx.wrap_socket(client_socket, server_side=True)
                    # Thread-per-client pattern: handle each client concurrently
                    thread = threading.Thread(target=handle_client, args=(ssl_socket, client_addr), daemon=True)
                    thread.start()
                except ssl.SSLError as e:
                    # Graceful failure: log SSL issue but continue accepting others
                    print(f"[SSL Error] {client_addr[0]}:{client_addr[1]}")
                    client_socket.close()
            except Exception as e:
                print(f"[Error] Accept failed: {type(e).__name__}")
                
    except KeyboardInterrupt:
        print("\n[Shutdown]")
    except Exception as e:
        print(f"[Error] Server error: {e}")
    finally:
        server_socket.close()
