# Project Setup and Menu - Initialize data, certificates, and run tests
# Creates test file, SSL certificates, server, and client with user menu
import os
import sys
import subprocess
import time

# Project initialization
def init_project():
    """Initialize project: directories, test file, certificate."""
    
    # Create required directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Generate 20 MB test file if not exists
    test_file = "data/testfile.bin"
    if not os.path.exists(test_file):
        print("\n[Setup] Creating 20 MB test file...")
        with open(test_file, "wb") as f:
            for _ in range(2):
                f.write(os.urandom(10 * 1024 * 1024))
        print(f"[Setup] ✓ Test file created: {os.path.getsize(test_file):,} bytes")
    else:
        print("[Setup] ✓ Test file exists")
    
    # Generate self-signed SSL certificate if not exists
    cert_file = "data/server.crt"
    if not os.path.exists(cert_file):
        print("[Setup] Generating SSL certificate & key...")
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime
            
            # Generate 2048-bit RSA private key
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            
            # Define certificate subject attributes
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Karnataka"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PESU"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            # Build and sign certificate (valid for 365 days)
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.now(datetime.timezone.utc)
            ).not_valid_after(
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"), x509.DNSName("127.0.0.1")
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Write certificate and private key to files
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            with open("data/server.key", "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            print(f"[Setup] ✓ SSL certificate & key generated")
        except ImportError:
            print("[Error] cryptography library required: pip install cryptography")
            sys.exit(1)
    else:
        print("[Setup] ✓ SSL certificate exists")

def show_menu():
    """Display test mode menu and return user selection."""
    print("\n" + "="*60)
    print("CHOOSE TEST MODE")
    print("="*60)
    print("\n[1] Quick Test (5 downloads, 10s intervals)")
    print("    └─ Best for: Quick verification\n")
    
    print("[2] Short Intervals (12 downloads, 5min intervals)")
    print("    └─ Best for: Quick hourly variation check\n")
    
    print("[3] Standard 24-Hour (24 downloads, 1hr intervals)")
    print("    └─ Best for: Full day of data collection\n")
    
    print("[4] Custom (user-defined parameters)")
    print("    └─ Best for: Specific test requirements\n")
    
    print("[0] Exit\n")
    
    while True:
        choice = input("Enter choice (0-4): ").strip()
        if choice in ['0', '1', '2', '3', '4']:
            return choice
        print("Invalid choice. Try again.")

def get_custom_params():
    """Get custom test parameters from user."""
    print("\n" + "="*60)
    print("CUSTOM TEST CONFIGURATION")
    print("="*60 + "\n")
    
    while True:
        try:
            count = int(input("Number of downloads (1-100): "))
            if 1 <= count <= 100:
                break
            print("Please enter a number between 1 and 100.")
        except ValueError:
            print("Invalid input. Enter a number.")
    
    while True:
        try:
            interval = int(input("Interval between downloads in seconds (5-7200): "))
            if 5 <= interval <= 7200:
                break
            print("Please enter a number between 5 and 7200.")
        except ValueError:
            print("Invalid input. Enter a number.")
    
    return count, interval

def launch_test(interval, count):
    """Launch server and client with specified parameters."""
    print("\n" + "="*60)
    print("LAUNCHING TEST")
    print("="*60)
    
    try:
        # Launch server
        print("\n[Launch] Starting SERVER...")
        subprocess.Popen(
            ["python", "src/server.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("[Launch] ✓ Server started (check terminal 1)")
        time.sleep(2)
        
        # Launch client
        print("[Launch] Starting CLIENT...")
        subprocess.Popen(
            ["python", "src/client.py", "--interval", str(interval), "--count", str(count)],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("[Launch] ✓ Client started (check terminal 2)")
        
        print("\n" + "="*60)
        print("✓ TEST RUNNING")
        print("="*60)
        print("\nTwo new terminal windows should have opened:")
        print("  • Terminal 1: SERVER (SSL/TLS listener)")
        print("  • Terminal 2: CLIENT (downloading files)")
        print("\nResults will be saved to: results/[timestamp]/")
        print("\nClose this window when done or press Ctrl+C.")
        print("="*60 + "\n")
        
        # Wait indefinitely
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n[Exit] Test interrupted by user.")
    except Exception as e:
        print(f"[Error] Failed to launch: {e}")
        sys.exit(1)

def main():
    print("\n" + "="*60)
    print("NETWORK DOWNLOAD ANALYZER - SETUP")
    print("="*60)
    
    # Initialize project
    print("\n[Setup] Initializing project...")
    init_project()
    print("[Setup] ✓ Project ready\n")
    
    # Show menu and get user choice
    choice = show_menu()
    
    if choice == '0':
        print("[Exit] Goodbye!")
        sys.exit(0)
    elif choice == '1':
        # Quick test
        print("\n[Config] Quick Test: 5 downloads × 20MB, 10s apart")
        launch_test(interval=10, count=5)
    elif choice == '2':
        # Short intervals
        print("\n[Config] Short Intervals: 12 downloads × 20MB, 5min apart")
        launch_test(interval=300, count=12)
    elif choice == '3':
        # Standard 24-hour
        print("\n[Config] Standard 24-Hour: 24 downloads × 20MB, 1hr apart")
        launch_test(interval=3600, count=24)
    elif choice == '4':
        # Custom
        count, interval = get_custom_params()
        print(f"\n[Config] Custom: {count} downloads × 20MB, {interval}s apart")
        launch_test(interval=interval, count=count)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Exit] Setup interrupted.")
        sys.exit(0)
