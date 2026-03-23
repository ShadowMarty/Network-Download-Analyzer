# Network Download Analyzer (SSL/TLS)

A comprehensive network diagnostics tool that measures download throughput over encrypted SSL/TLS connections. Perfect for understanding network performance patterns and optimizing file transfer scheduling across different times of day.

## Overview

This project analyzes your network behavior over time by performing repeated SSL/TLS-encrypted downloads and identifying peak/off-peak performance patterns. It generates actionable insights for scheduling large file transfers, backups, and synchronizations to avoid congestion and maximize throughput.

**Core Features:**
- SSL/TLS-encrypted network throughput measurement
- Statistical analysis (mean, median, standard deviation, percentiles)
- Temporal performance pattern analysis (hourly grouping)
- Network quality assessment and stability metrics
- Multi-format output (JSON, CSV, text report, PNG visualization)
- Transfer time estimation for various file sizes

## Setup

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 setup.py
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
python setup.py
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
python setup.py
```

## Usage

After setup is complete, the analyzer will automatically start. Choose from the available test modes:

- **Quick Test** - 5 downloads, 10s apart (1 minute)
- **Short Intervals** - 12 downloads, 5min apart (1 hour)  
- **Standard 24-Hour** - 24 downloads, 1hr apart (24 hours)
- **Custom** - User-defined parameters

The analyzer will begin measuring your network performance. Results are saved to a timestamped directory (`results/`) with your test data and report.

## Understanding Your Report

The generated `network_report.txt` provides:

- **Throughput Metrics** — Mean, median, and variability of your download speed
- **Quality Rating** — EXCELLENT/VERY GOOD/GOOD/FAIR/POOR based on consistency
- **Per-Hour Analysis** — Shows which hours have faster/slower speeds
- **Transfer Estimates** — How long different file sizes will take at your speed
- **Real-World Suitability** — Whether your network supports 4K streaming, video calls, concurrent downloads, etc.
- **Recommendations** — Best times to transfer files and optimal strategies

## Why Use This?

Answers practical questions:
- **When should I download large files?** → Peak/off-peak hour analysis
- **How long will my file take?** → Accurate time estimates based on your network
- **Is my network stable?** → Throughput variability metrics
- **What's my network quality level?** → Simple EXCELLENT/VERY GOOD/GOOD/FAIR/POOR assessment

## Architecture

The analyzer consists of three main components:

- **Server** (`src/server.py`) — SSL/TLS server serving a 20MB test file to simulate real-world network conditions
- **Client** (`src/client.py`) — Performs encrypted downloads and measures throughput with nanosecond precision
- **Analysis Engine** (`src/analysis.py`) — Computes statistical metrics, identifies performance patterns, and generates reports

## Output

Each test creates a timestamped directory with:
- **download_log.json** - Raw results
- **download_log.csv** - Spreadsheet format  
- **network_report.txt** - Summary with recommendations and time estimates
- **throughput_chart.png** - Visual throughput graph

## Real-World Use Cases

| User | Use Case | Benefit |
|------|----------|---------|
| **IT Admin** | Schedule backups during peak hours | Reduce backup time 2-3x |
| **Remote Worker** | Sync large files at optimal times | Avoid video call disruption |
| **Content Creator** | Upload videos during stable hours | Reliable completion times |
| **Network Engineer** | Monitor 24-hour patterns | Identify bottlenecks |

## Requirements

- Python 3.8 or higher
- matplotlib (for visualization charts)
- cryptography (for SSL/TLS certificate handling)

## Key Capabilities

✓ SSL/TLS-secured throughput measurement  
✓ Hourly network performance analysis  
✓ File transfer time estimation (100MB to 100GB)  
✓ Network stability and quality metrics  
✓ Multi-format reporting (JSON, CSV, text, visualization)

## Network Metrics Explained

- **Mean Throughput** — Average download speed across all tests
- **Median Throughput** — Middle value of all speeds (less affected by outliers)
- **Standard Deviation** — How much your speeds vary; lower is more stable
- **Jitter** — Speed variability expressed as a percentage; <10% is excellent
- **P95/P99** — Speeds at which 95% and 99% of transfers perform at or above

## Project Structure

```
CN_Project/
├── src/
│   ├── client.py          # Download client with SSL/TLS encryption
│   ├── server.py          # SSL/TLS test server (20MB file)
│   └── analysis.py        # Statistics and report generation
├── data/
│   ├── testfile.bin       # 20MB binary test file
│   ├── server.crt         # SSL certificate (self-signed)
│   └── server.key         # SSL private key
├── results/               # Test results directory
├── README.md
├── requirements.txt
└── setup.py               # Installation and first-run setup
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 8000 already in use** | Kill existing process or use `setup.py` to configure a different port |
| **SSL certificate errors** | Run `setup.py` to regenerate self-signed certificates |
| **No matplotlib charts** | Install matplotlib: `pip install matplotlib` |
| **Connection refused** | Ensure server is running before starting client |

## Limitations

- Tests use a 20MB file; results apply best to files of similar size
- Local network loop (client-server on same machine) may not reflect ISP speeds
- Peak/off-peak analysis requires longer test duration (recommend 24-hour test)
- One-way transfer measurement; actual bidirectional usage may differ

## Contributors

| Name | GitHub |
|------|--------|
| Shreya S Mattimadu | [github.com/Shreya04M](https://github.com/Shreya04M) |
| Shivakumara G P | [github.com/shivakumara-gp](https://github.com/shivakumara-gp) |
| Shashank A | [github.com/ShadowMarty](https://github.com/ShadowMarty) |
