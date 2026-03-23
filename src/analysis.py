import json, os, statistics, datetime

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

def compute_stats(records: list[dict]) -> dict:
    """Compute statistics from download records."""
    successful = [r for r in records if r.get("success")]
    if not successful:
        return {}
    
    throughputs = [r["throughput_mbps"] for r in successful]
    durations = [r["duration_sec"] for r in successful]
    total_bytes = sum(r["bytes_received"] for r in successful)
    
    return {
        "total_attempts": len(records),
        "successful": len(successful),
        "failed": len(records) - len(successful),
        "throughput_mbps": {
            "mean": round(statistics.mean(throughputs), 6),
            "median": round(statistics.median(throughputs), 6),
            "stdev": round(statistics.stdev(throughputs), 6) if len(throughputs) > 1 else 0.0,
            "min": round(min(throughputs), 6),
            "max": round(max(throughputs), 6),
        },
        "duration_sec": {
            "mean": round(statistics.mean(durations), 4),
            "min": round(min(durations), 4),
            "max": round(max(durations), 4),
        },
        "total_bytes_rx": total_bytes,
        "throughputs": throughputs,
    }

def print_stats(stats: dict, records: list[dict] = None) -> None:
    """Print statistics to console with per-download breakdown."""
    if not stats:
        print("No data to display.")
        return
    
    print("\n" + "="*50)
    print("THROUGHPUT ANALYSIS SUMMARY")
    print("="*50)
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successful: {stats['successful']}, Failed: {stats['failed']}")
    print(f"Total bytes: {stats['total_bytes_rx']:,}")
    print()
    
    t = stats['throughput_mbps']
    print(f"Mean:    {t['mean']:.6f} MB/s")
    print(f"Median:  {t['median']:.6f} MB/s")
    print(f"Std-Dev: {t['stdev']:.6f} MB/s")
    print(f"Min:     {t['min']:.6f} MB/s")
    print(f"Max:     {t['max']:.6f} MB/s")
    print()
    
    d = stats['duration_sec']
    print(f"Mean duration: {d['mean']:.4f}s")
    print(f"Min duration:  {d['min']:.4f}s")
    print(f"Max duration:  {d['max']:.4f}s")
    
    # Per-download breakdown
    if records:
        successful = [r for r in records if r.get("success")]
        if len(successful) <= 12:  # Per-download mode for <= 12 tests
            print()
            print("Per-Download Breakdown:")
            print("-" * 50)
            for i, record in enumerate(successful, 1):
                marker = " <-- BUSIEST" if abs(record['throughput_mbps'] - t['max']) < 0.0001 else ""
                marker = marker or (" <-- SLOWEST" if abs(record['throughput_mbps'] - t['min']) < 0.0001 else "")
                print(f"  Download {i}: {record['throughput_mbps']:.6f} MB/s{marker}")
    
    print("="*50 + "\n")

def save_chart(records: list[dict], stats: dict, session_dir: str = None) -> str:
    """Generate and save throughput chart."""
    if not HAS_MATPLOTLIB:
        print("✓ Chart: Matplotlib not available")
        return None
    
    successful = [r for r in records if r.get("success")]
    if not successful:
        return None
    
    output_path = os.path.join(session_dir, "throughput_chart.png") if session_dir else "throughput_chart.png"
    
    try:
        timestamps = [datetime.datetime.fromisoformat(r["timestamp"]) for r in successful]
        throughputs = [r["throughput_mbps"] for r in successful]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9))
        fig.suptitle("Network Download Analyzer", fontsize=14, fontweight="bold")
        
        # Chart 1: Throughput over time
        ax1.plot(timestamps, throughputs, marker="o", linewidth=2, color="#2196F3", markersize=6)
        ax1.axhline(y=stats["throughput_mbps"]["mean"], color="orange", linestyle="--", 
                    linewidth=2, label=f'Mean: {stats["throughput_mbps"]["mean"]:.4f} MB/s')
        ax1.set_ylabel("Throughput (MB/s)", fontsize=10)
        ax1.set_xlabel("Time", fontsize=10)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.set_title("Throughput Over Time", fontsize=11, fontweight="bold")
        
        # Chart 2: Per-download performance
        downloads = list(range(1, len(throughputs) + 1))
        max_throughput = max(throughputs)
        colors = ["#F44336" if tp == max_throughput else "#4CAF50" for tp in throughputs]
        
        ax2.bar(downloads, throughputs, color=colors, edgecolor="white", width=0.7)
        ax2.set_xlabel("Download Number", fontsize=10)
        ax2.set_ylabel("Throughput (MB/s)", fontsize=10)
        ax2.set_title("Per-Download Throughput (Red = Fastest)", fontsize=11, fontweight="bold")
        ax2.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout(pad=2.0)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"✓ Chart saved: throughput_chart.png")
        return output_path
    except Exception as e:
        print(f"✗ Chart error: {e}")
        return None

def write_report(stats: dict, records: list[dict] = None, session_dir: str = None) -> str:
    """Write concise but practical analysis report with real-world recommendations."""
    if not stats:
        return None
    
    output_path = os.path.join(session_dir, "network_report.txt") if session_dir else "network_report.txt"
    
    mean_tp = stats['throughput_mbps']['mean']
    
    # Quick network quality assessment
    def quality_level(mbps):
        if mbps >= 100: return "EXCELLENT"
        elif mbps >= 50: return "VERY GOOD"
        elif mbps >= 10: return "GOOD"
        elif mbps >= 5: return "FAIR"
        else: return "POOR"
    
    # Group by hour if available
    hourly_stats = {}
    if records:
        successful = [r for r in records if r.get("success")]
        for record in successful:
            hour = record.get("hour", 0)
            if hour not in hourly_stats:
                hourly_stats[hour] = []
            hourly_stats[hour].append(record["throughput_mbps"])
    
    # Only use hourly analysis if data spans multiple distinct hours AND makes sense
    has_multi_hour_data = len(hourly_stats) > 1
    
    if has_multi_hour_data and len(hourly_stats) >= 2:
        hours_list = sorted(hourly_stats.keys())
        # Check if hours are realistic - should be consecutive or close
        # Handle midnight wrap: if hours are like [23, 0, 1], compute gap correctly
        gaps = []
        for i in range(len(hours_list)-1):
            gap = hours_list[i+1] - hours_list[i]
            if gap < 0:  # Midnight wrap
                gap = gap + 24
            gaps.append(gap)
        
        max_gap = max(gaps) if gaps else 0
        # Only show hourly analysis if all consecutive hours are 1-2 apart
        # This avoids spurious hour data from clock issues
        if max_gap > 2:
            has_multi_hour_data = False
    
    lines = [
        "=" * 70,
        "NETWORK DOWNLOAD ANALYZER - REPORT",
        "=" * 70,
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Quality: {quality_level(mean_tp)} ({mean_tp:.2f} MB/s average)",
        "",
        "THROUGHPUT METRICS",
        "-" * 70,
        f"  Mean:       {stats['throughput_mbps']['mean']:.4f} MB/s",
        f"  Median:     {stats['throughput_mbps']['median']:.4f} MB/s",
        f"  Std-Dev:    {stats['throughput_mbps']['stdev']:.4f} MB/s",
        f"  Min/Max:    {stats['throughput_mbps']['min']:.4f} / {stats['throughput_mbps']['max']:.4f} MB/s",
        f"  Stability:  {(1 - stats['throughput_mbps']['stdev']/mean_tp)*100:.0f}%" if mean_tp > 0 else "  Stability: N/A",
        "",
        "TEST RESULTS",
        "-" * 70,
        f"  Total attempts:  {stats['total_attempts']}",
        f"  Success rate:    {(stats['successful']/stats['total_attempts']*100):.0f}%",
        f"  Total data:      {stats['total_bytes_rx']/1024/1024:.2f} MB",
        "",
    ]
    
    # Hourly breakdown (only if data spans multiple hours)
    if hourly_stats and has_multi_hour_data:
        best_hour = max(hourly_stats.keys(), key=lambda h: statistics.mean(hourly_stats[h]))
        worst_hour = min(hourly_stats.keys(), key=lambda h: statistics.mean(hourly_stats[h]))
        
        lines.extend([
            "PEAK/OFF-PEAK ANALYSIS",
            "-" * 70,
            f"  Best hour:   {best_hour:02d}:00 ({statistics.mean(hourly_stats[best_hour]):.2f} MB/s)",
            f"  Worst hour:  {worst_hour:02d}:00 ({statistics.mean(hourly_stats[worst_hour]):.2f} MB/s)",
            f"  Peak variance: {(statistics.mean(hourly_stats[best_hour])/statistics.mean(hourly_stats[worst_hour]) - 1)*100:.0f}% difference",
            "",
        ])
    elif hourly_stats:
        # Single hour data - note that more testing needed for patterns
        current_hour = list(hourly_stats.keys())[0]
        lines.extend([
            "HOURLY ANALYSIS",
            "-" * 70,
            f"  Current hour ({current_hour:02d}:00): {statistics.mean(hourly_stats[current_hour]):.2f} MB/s average",
            f"  Note: Run longer tests (12+ hours) to identify peak/off-peak patterns",
            "",
        ])
    
    # Practical recommendations
    lines.extend([
        "PRACTICAL RECOMMENDATIONS",
        "-" * 70,
    ])
    
    if mean_tp >= 50:
        lines.extend([
            "✓ Your network is EXCELLENT for:",
            "  • 4K video streaming and large file transfers",
            "  • Real-time backups and cloud sync",
            "  • Multiple concurrent downloads",
            "  → No scheduling needed; proceed with large downloads anytime",
        ])
    elif mean_tp >= 10:
        lines.extend([
            "✓ Your network is GOOD for:",
            "  • HD streaming, software updates, and backups",
            "  • Standard cloud operations",
            "  → Large files (>5 GB): Schedule during identified peak hours",
        ])
    else:
        lines.extend([
            "⚠ Your network is LIMITED:",
            "  • Schedule large downloads during off-peak hours (shown above)",
            "  • Use compression for large transfers",
            "  • Avoid concurrent downloads during peak usage",
        ])
    
    lines.extend([
        "",
        "DOWNLOAD TIME ESTIMATES (at current speed)",
        "-" * 70,
        f"  100 MB:   {mean_tp and f'{100/mean_tp:.0f}s' or 'N/A'}",
        f"  1 GB:     {mean_tp and f'{1024/mean_tp:.1f}m' or 'N/A'}",
        f"  10 GB:    {mean_tp and f'{10240/mean_tp:.2f}h' or 'N/A'}",
        "",
        "ACTION ITEMS",
        "-" * 70,
    ])
    
    if hourly_stats and has_multi_hour_data:
        best_hour = max(hourly_stats.keys(), key=lambda h: statistics.mean(hourly_stats[h]))
        lines.append(f"  1. Schedule large downloads at {best_hour:02d}:00 (best performance hour)")
    
    action_num = 2 if (hourly_stats and has_multi_hour_data) else 1
    
    if stats['failed'] > 0:
        lines.append(f"  {action_num}. Investigate {stats['failed']} failed download(s) - may indicate instability")
        action_num += 1
    
    if stats['throughput_mbps']['stdev'] > mean_tp * 0.3:
        lines.append(f"  {action_num}. High variability detected - use conservative time estimates")
    
    lines.extend([
        "",
        "=" * 70,
        "End of Report",
        "=" * 70,
    ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✓ Report saved: network_report.txt")
    return output_path

def analyze_and_report(records: list[dict], session_dir: str = None) -> dict:
    """Run complete analysis pipeline. Returns stats and file paths."""
    stats = compute_stats(records)
    chart_path = None
    report_path = None
    
    if stats:
        print_stats(stats, records)
        chart_path = save_chart(records, stats, session_dir)
        report_path = write_report(stats, records, session_dir)
    
    return {
        "stats": stats,
        "chart_path": chart_path,
        "report_path": report_path
    }
