# TCP Socket Network Download Analyzer - Statistical Analysis and Reporting
# Computes throughput metrics via raw TCP connections, generates charts and reports
import json, os, statistics, datetime
try:
    import matplotlib
    matplotlib.use("Agg") # Save charts without GUI
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def compute_stats(records: list[dict]) -> dict:
    """Compute statistics from TCP download records."""
    successful = [r for r in records if r.get("success")]
    if not successful:
        return {}
    
    throughputs = [r["throughput_mbps"] for r in successful]
    first_ts = datetime.datetime.fromisoformat(successful[0]["timestamp"])
    last_ts = datetime.datetime.fromisoformat(successful[-1]["timestamp"])
    test_duration = (last_ts - first_ts).total_seconds()
    
    # Simple period grouping
    period_buckets = {}
    for r in successful:
        ts = datetime.datetime.fromisoformat(r["timestamp"])
        key = ts.hour if test_duration >= 3600 else len(period_buckets)
        if key not in period_buckets:
            period_buckets[key] = []
        period_buckets[key].append(r["throughput_mbps"])
    
    period_avg = {k: round(statistics.mean(v), 4) for k, v in period_buckets.items()}
    
    return {
        "total_attempts": len(records),
        "successful": len(successful),
        "failed": len(records) - len(successful),
        "throughput_mbps": {
            "mean": round(statistics.mean(throughputs), 4),
            "median": round(statistics.median(throughputs), 4),
            "stdev": round(statistics.stdev(throughputs), 4) if len(throughputs) > 1 else 0.0,
            "min": round(min(throughputs), 4),
            "max": round(max(throughputs), 4),
        },
        "period_avg_mbps": period_avg,
        "best_period": max(period_avg, key=period_avg.get) if period_avg else None,
        "bucket_type": "hour" if test_duration >= 3600 else "download",
        "test_duration_sec": test_duration,
    }


def print_stats(stats: dict, records: list[dict] = None) -> None:
    """Print concise TCP throughput analysis to console."""
    if not stats:
        print("No data to display.")
        return
    
    t = stats['throughput_mbps']
    print("\n" + "="*60)
    print("TCP THROUGHPUT ANALYSIS")
    print("="*60)
    print(f"Attempts: {stats['total_attempts']} | Success: {stats['successful']} | Failed: {stats['failed']}")
    print(f"Mean: {t['mean']:.4f} MB/s | Median: {t['median']:.4f} | Std Dev: {t['stdev']:.4f}")
    print(f"Range: {t['min']:.4f} - {t['max']:.4f} MB/s")
    print("="*60 + "\n")


def save_chart(records: list[dict], stats: dict, session_dir: str = None) -> str:
    """Generate TCP throughput visualization chart."""
    if not HAS_MATPLOTLIB or not records:
        return None
    
    successful = [r for r in records if r.get("success")]
    output_path = os.path.join(session_dir, "throughput_chart.png") if session_dir else "throughput_chart.png"
    
    try:
        timestamps = [datetime.datetime.fromisoformat(r["timestamp"]) for r in successful]
        throughputs = [r["throughput_mbps"] for r in successful]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.suptitle("TCP Network Performance Analysis", fontsize=14, fontweight="bold")
        
        # Timeline: actual throughput over time
        ax1.plot(timestamps, throughputs, marker="o", linewidth=2, color="#2196F3", markersize=5)
        ax1.axhline(y=stats["throughput_mbps"]["mean"], color="orange", linestyle="--", 
                    linewidth=2, label=f'Mean: {stats["throughput_mbps"]["mean"]:.4f} MB/s')
        ax1.set_ylabel("Throughput (MB/s)", fontsize=10)
        ax1.set_xlabel("Download Time", fontsize=10)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.set_title("TCP Throughput Over Time", fontsize=11, fontweight="bold")
        
        # Period bars: average per time period
        period_avg = stats.get("period_avg_mbps", {})
        if period_avg and len(period_avg) > 1:
            periods = sorted(period_avg.keys())
            avgs = [period_avg[k] for k in periods]
            best = stats.get("best_period")
            colors = ["#F44336" if k == best else "#4CAF50" for k in periods]
            ax2.bar(range(len(periods)), avgs, color=colors, edgecolor="white", width=0.8)
            ax2.set_xlabel(f"Time Period ({stats['bucket_type']})", fontsize=10)
            ax2.set_title("Average TCP Throughput by Period (Red = Peak)", fontsize=11, fontweight="bold")
            ax2.set_xticks(range(len(periods)))
            ax2.set_xticklabels([str(k) for k in periods], fontsize=8)
        else:
            ax2.plot(range(len(throughputs)), throughputs, marker="^", color="#2196F3", linewidth=2)
            ax2.set_xlabel("Download Sequence", fontsize=10)
            ax2.set_title("Individual TCP Download Performance", fontsize=11, fontweight="bold")
        
        ax2.set_ylabel("Throughput (MB/s)", fontsize=10)
        ax2.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"✓ Chart saved: throughput_chart.png")
        return output_path
    except Exception as e:
        print(f"✗ Chart error: {e}")
        return None


def write_report(stats: dict, session_dir: str = None) -> str:
    """Write TCP network performance report."""
    if not stats:
        return None
    
    output_path = os.path.join(session_dir, "network_report.txt") if session_dir else "network_report.txt"
    t = stats['throughput_mbps']
    
    lines = [
        "=" * 70,
        "TCP NETWORK PERFORMANCE REPORT",
        "=" * 70,
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Test Duration: {stats['test_duration_sec']:.1f} seconds",
        f"Protocol: TCP over SSL/TLS",
        "",
        "THROUGHPUT METRICS (MB/s)",
        "-" * 70,
        f"Mean Throughput:       {t['mean']:.4f} MB/s",
        f"Median Throughput:     {t['median']:.4f} MB/s",
        f"Standard Deviation:    {t['stdev']:.4f} MB/s",
        f"Minimum Speed:         {t['min']:.4f} MB/s",
        f"Maximum Speed:         {t['max']:.4f} MB/s",
        "",
        "TEST RESULTS",
        "-" * 70,
        f"Total Attempts:        {stats['total_attempts']}",
        f"Successful Downloads:  {stats['successful']}",
        f"Failed Downloads:      {stats['failed']}",
        f"Success Rate:          {(stats['successful']/stats['total_attempts']*100):.1f}%",
        "",
        "CONNECTION STABILITY",
        "-" * 70,
        f"Variability Index:     {(t['stdev']/t['mean']*100):.1f}% (lower is better)",
        f"Consistency:           {'Stable' if t['stdev']/t['mean'] < 0.15 else ('Moderate' if t['stdev']/t['mean'] < 0.35 else 'Variable')}",
        "",
        "TRANSFER TIME ESTIMATES (at mean speed)",
        "-" * 70,
        f"1 MB:                  {(1/t['mean']*1000):.0f} milliseconds",
        f"100 MB:                {(100/t['mean']):.1f} seconds",
        f"1 GB:                  {(1024/t['mean']/60):.1f} minutes",
        f"10 GB:                 {(10240/t['mean']/3600):.2f} hours",
        "",
        "REAL-WORLD USAGE",
        "-" * 70,
        f"Network Tier:          {'High Speed' if t['mean'] >= 50 else ('Medium' if t['mean'] >= 10 else 'Standard')}",
        f"Suitable for:          {'4K/8K Streaming' if t['mean'] >= 25 else ('HD Streaming' if t['mean'] >= 5 else ('Web/Email' if t['mean'] >= 1 else 'Limited'))}",
        f"Parallel Transfers:    {'Unlimited' if t['mean'] >= 50 else ('2-3 simultaneous' if t['mean'] >= 10 else 'Single only')}",
        "",
        "=" * 70,
    ]
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✓ Report saved: network_report.txt")
    return output_path


def analyze_and_report(records: list[dict], session_dir: str = None) -> dict:
    """Execute TCP analysis pipeline."""
    stats = compute_stats(records)
    if stats:
        print_stats(stats, records)
        return {
            "stats": stats,
            "chart_path": save_chart(records, stats, session_dir),
            "report_path": write_report(stats, session_dir)
        }
    return {"stats": {}, "chart_path": None, "report_path": None}

