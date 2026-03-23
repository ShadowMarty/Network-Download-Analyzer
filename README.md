# Network Download Analyzer (SSL/TLS)

A comprehensive network diagnostics tool that measures download throughput over encrypted SSL/TLS connections. Perfect for understanding network performance patterns and optimizing file transfer scheduling across different times of day.

## Overview

This project analyzes your network behavior over time by performing repeated SSL/TLS-encrypted downloads and identifying peak/off-peak performance patterns. It generates actionable insights for scheduling large file transfers, backups, and synchronizations to avoid congestion and maximize throughput.

**Key Technical Features:**
- Encrypted downloads using SSL/TLS (self-signed certificates)
- Precision timing with `time.perf_counter()` for accuracy
- Per-hour grouping for peak/off-peak analysis  
- Comprehensive statistical analysis (mean, median, stdev, min/max)
- Multi-format reporting (JSON, CSV, text, PNG charts)
- Flexible test modes from 1 minute to 24 hours
- Automatic result opening on completion

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

Run the analyzer and choose a test mode:
- **Quick Test** - 5 downloads, 10s apart (1 minute)
- **Short Intervals** - 12 downloads, 5min apart (1 hour)  
- **Standard 24-Hour** - 24 downloads, 1hr apart (24 hours)
- **Custom** - User-defined parameters

## Why Use This?

Answers practical questions:
- **When should I download large files?** → Peak/off-peak hour analysis
- **How long will my file take?** → Accurate time estimates based on your network
- **Is my network stable?** → Throughput variability metrics
- **What's my network quality level?** → Simple EXCELLENT/VERY GOOD/GOOD/FAIR/POOR assessment

## How It Works

The analyzer consists of three main components:

- **Server** (`src/server.py`) — SSL/TLS server listening on `localhost:8000`, serves a 20MB test file to simulate real-world downloads
- **Client** (`src/client.py`) — Initiates encrypted downloads and measures precise throughput using high-resolution timing
- **Analysis Engine** (`src/analysis.py`) — Computes statistics (mean, median, standard deviation), evaluates network quality, groups data by hour, and generates recommendations

Data flows through the pipeline: download measurements → statistical analysis → identified patterns → actionable recommendations.

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

## Features

✓ SSL/TLS-secured throughput measurement  
✓ Peak/off-peak hour detection  
✓ Download time estimates (100MB to 10GB)  
✓ Network quality assessment  
✓ Automatic file opening on Windows  
✓ Multi-format output (JSON/CSV/text/PNG)  
✓ Flexible test modes (1 min to 24 hours)
