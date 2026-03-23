# Network Download Analyzer (SSL/TLS)

Measures network throughput over encrypted connections and provides actionable guidance for download scheduling.

## Quick Start

```bash
python setup.py
```

Choose test mode:
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

**Server** (`src/server.py`) - Listens on localhost:8000 with SSL/TLS, serves 20MB test file  
**Client** (`src/client.py`) - SSL/TLS downloads with precise throughput measurement  
**Analysis** (`src/analysis.py`) - Computes statistics and generates practical recommendations

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

- Python 3.8+
- `cryptography` (for SSL) - auto-installed
- `matplotlib` (optional, for charts)

## Features

✓ SSL/TLS-secured throughput measurement  
✓ Peak/off-peak hour detection  
✓ Download time estimates (100MB to 10GB)  
✓ Network quality assessment  
✓ Automatic file opening on Windows  
✓ Multi-format output (JSON/CSV/text/PNG)  
✓ Flexible test modes (1 min to 24 hours)
