# Network Download Analyzer - SSL/TLS Client
# Performs encrypted downloads at regular intervals and measures throughput
import socket, ssl, time, os, json, csv, datetime, sys
import analysis

# Configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_FILE = "testfile.bin"

# Directory setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# Session management
def get_session_dir() -> str:
    """Create timestamped results directory."""
    now = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    session_dir = os.path.join(RESULTS_DIR, now)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir

# SSL/TLS setup
def build_ssl_context() -> ssl.SSLContext:
    """Create SSL context with proper certificate verification for lab environment."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # For single-machine lab testing: disable hostname check (not critical for internal testing)
    # but keep certificate verification enabled (REQUIRED for security)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    # Load the self-signed certificate from the data directory
    # This ensures the certificate is cryptographically verified
    cert_path = os.path.join(PROJECT_ROOT, "data", "server.crt")
    ctx.load_verify_locations(cafile=cert_path)
    return ctx

# Core download logic
def download_file(host: str, port: int, filename: str, ssl_ctx: ssl.SSLContext) -> dict:
    """Download file via SSL/TLS and measure throughput."""
    result = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hour": datetime.datetime.now().hour,
        "success": False,
        "bytes_received": 0,
        "duration_sec": 0.0,
        "throughput_mbps": 0.0,
        "error": None,
    }

    try:
        # Step 1: Create socket and establish connection
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(30)
        raw_sock.connect((host, port))
        # Step 2: Wrap socket with SSL/TLS
        sock = ssl_ctx.wrap_socket(raw_sock, server_hostname=host)
        
        # Step 3: Send HTTP GET request
        request = f"GET /{filename} HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())
        
        # Step 4: Receive data with high-precision timing
        start_time = time.perf_counter()
        response = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            response += chunk
        end_time = time.perf_counter()
        
        # Step 5: Parse HTTP response
        if b"\r\n\r\n" not in response:
            result["error"] = "Invalid HTTP response"
            return result
        
        headers, body = response.split(b"\r\n\r\n", 1)
        if b"200" not in headers.split(b"\r\n")[0]:
            result["error"] = "HTTP error"
            return result
        
        # Step 6: Calculate throughput metrics
        duration = end_time - start_time
        bytes_rx = len(body)
        mbps = (bytes_rx / (1024 * 1024)) / duration if duration > 0 else 0
        
        result.update({
            "success": True,
            "bytes_received": bytes_rx,
            "duration_sec": round(duration, 4),
            "throughput_mbps": round(mbps, 6),
        })
        sock.close()
        
    except Exception as e:
        result["error"] = str(type(e).__name__)
    
    return result

# Logging functions
def append_log(result: dict, json_path: str, csv_path: str) -> None:
    """Log download result to JSON and CSV."""
    # Append to JSON-lines format (one record per line)
    with open(json_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")
    
    # Append to CSV (write header if file is new)
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=result.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(result)

# Scheduler - runs downloads at regular intervals
def run_scheduler(host: str, port: int, filename: str, interval: int, total: int) -> None:
    """Run scheduled downloads at regular intervals."""
    ssl_ctx = build_ssl_context()
    session_dir = get_session_dir()
    log_json = os.path.join(session_dir, "download_log.json")
    log_csv = os.path.join(session_dir, "download_log.csv")
    records = []
    
    # Print session header
    print(f"\n{'='*60}")
    print("█ CLIENT - Scheduled Test Mode")
    print(f"{'='*60}")
    print(f"Server:    {host}:{port}")
    print(f"Mode:      SSL/TLS Encryption")
    print(f"Tests:     {total} downloads × 20 MB")
    print(f"Interval:  {interval}s ({interval//60} min)")
    print(f"Start:     {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Download loop with timing synchronization
    for i in range(1, total + 1):
        tick_start = time.perf_counter()
        time_str = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{time_str}] Download {i}/{total}...", end=" ", flush=True)

        result = download_file(host, port, filename, ssl_ctx)
        records.append(result)
        append_log(result, log_json, log_csv)

        if result["success"]:
            print(f"[OK] {result['bytes_received']:,}B {result['throughput_mbps']:.4f} MB/s")
        else:
            print(f"[FAIL] {result['error']}")

        # Intermediate analysis and reporting every 6 downloads
        if i == total:
            analysis.analyze_and_report(records, session_dir)

        # Sleep until next scheduled download
        if i < total:
            sleep_for = max(0, interval - (time.perf_counter() - tick_start))
            print(f"  Next in {sleep_for:.0f}s\n")
            time.sleep(sleep_for)
    
    _show_completion(session_dir)

# Quick test - rapid downloads without waiting (1+ minute tests)
def run_quick_test(host: str, port: int, filename: str, count: int, interval: int = 10) -> None:
    """Run multiple downloads quickly for testing."""
    ssl_ctx = build_ssl_context()
    session_dir = get_session_dir()
    log_json = os.path.join(session_dir, "download_log.json")
    log_csv = os.path.join(session_dir, "download_log.csv")
    records = []
    
    # Print session header
    print(f"\n{'='*60}")
    print("█ CLIENT - Quick Test Mode")
    print(f"{'='*60}")
    print(f"Server:    {host}:{port}")
    print(f"Mode:      SSL/TLS Encryption")
    print(f"Tests:     {count} downloads × 20 MB")
    print(f"Interval:  {interval} seconds between each")
    print(f"Start:     {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Back-to-back downloads with fixed sleep intervals
    for i in range(1, count + 1):
        time_str = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{time_str}] Download {i}/{count}...", end=" ", flush=True)
        
        result = download_file(host, port, filename, ssl_ctx)
        result["hour"] = (i - 1) % 24  # Simulate 24-hour spread for variety
        records.append(result)
        append_log(result, log_json, log_csv)

        if result["success"]:
            print(f"[OK] {result['bytes_received']:,}B {result['throughput_mbps']:.4f} MB/s")
        else:
            print(f"[FAIL] {result['error']}")

        if i < count:
            time.sleep(interval)
    
    analysis.analyze_and_report(records, session_dir)
    _show_completion(session_dir)

# Results completion and file display
def _show_completion(session_dir: str) -> None:
    """Show completion message and auto-open results."""
    end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*60}")
    print("█ TEST COMPLETE")
    print(f"{'='*60}")
    print(f"End Time:  {end_time}")
    print(f"Results:   {session_dir}")
    print(f"\nFiles generated:")
    print(f"  • download_log.json     - Machine-readable results")
    print(f"  • download_log.csv      - Spreadsheet format")
    print(f"  • network_report.txt    - Full analysis report")
    print(f"  • throughput_chart.png  - Visualization")
    print(f"{'='*60}")
    
    # Auto-open files on Windows (best-effort)
    try:
        report_path = os.path.join(session_dir, "network_report.txt")
        chart_path = os.path.join(session_dir, "throughput_chart.png")
        
        if os.path.exists(report_path):
            print(f"\nOpening: {report_path}")
            os.startfile(report_path)
        
        if os.path.exists(chart_path):
            print(f"Opening: {chart_path}")
            os.startfile(chart_path)
    except Exception as e:
        print(f"\nNote: Could not auto-open files ({e})")
    
    input("\nPress Enter to close this window...")

# Entry point
if __name__ == "__main__":
    # Parse command-line parameters (interval and count)
    interval = 10  # Default for quick test
    count = 5      # Default for quick test
    
    if "--interval" in sys.argv:
        idx = sys.argv.index("--interval")
        if idx + 1 < len(sys.argv):
            interval = int(sys.argv[idx + 1])
    
    if "--count" in sys.argv:
        idx = sys.argv.index("--count")
        if idx + 1 < len(sys.argv):
            count = int(sys.argv[idx + 1])
    
    # Determine test mode: quick test or scheduled test
    if interval == 10 and count == 5:
        run_quick_test(DEFAULT_HOST, DEFAULT_PORT, DEFAULT_FILE, count, interval)
    else:
        run_scheduler(DEFAULT_HOST, DEFAULT_PORT, DEFAULT_FILE, interval, count)
