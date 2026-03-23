# TCP Socket Network Download Analyzer - Statistical Analysis and Reporting
# Computes throughput metrics via raw TCP connections, generates charts and reports
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
    """Compute statistics from TCP download records."""
    successful = [r for r in records if r.get("success")]
    if not successful:
        return {}
    
    throughputs = [r["throughput_mbps"] for r in successful]
    
    # Determine intelligent bucketing based on test duration
    if successful:
        first_ts = datetime.datetime.fromisoformat(successful[0]["timestamp"])
        last_ts = datetime.datetime.fromisoformat(successful[-1]["timestamp"])
        test_duration_sec = (last_ts - first_ts).total_seconds()
    else:
        test_duration_sec = 0
    
    # Smart time bucketing: choose scale based on test duration
    bucket_by = "download"  # default: per-download
    if test_duration_sec >= 3600:  # 1+ hour: group by hour
        bucket_by = "hour"
    elif test_duration_sec >= 600:  # 10+ min: group by 5-minute buckets
        bucket_by = "5min"
    # Tests under 10 minutes use per-download analysis (more useful than 30sec buckets)
    
    # Compute period-based averages
    period_buckets = {}
    for r in successful:
        ts = datetime.datetime.fromisoformat(r["timestamp"])
        if bucket_by == "hour":
            key = ts.hour
            label = f"{ts.hour:02d}:00"
        elif bucket_by == "5min":
            key = ts.minute // 5
            label = f"{ts.minute//5 * 5:02d}m"
        else:  # per-download
            key = len(period_buckets)
            label = f"#{key+1}"
        
        if key not in period_buckets:
            period_buckets[key] = {"label": label, "values": []}
        period_buckets[key]["values"].append(r["throughput_mbps"])
    
    period_avg = {k: round(statistics.mean(v["values"]), 6) for k, v in period_buckets.items()}
    best_period = max(period_avg, key=period_avg.get) if period_avg else None
    
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
        "period_avg_mbps": period_avg,
        "best_period": best_period,
        "bucket_type": bucket_by,
        "period_labels": {k: v["label"] for k, v in period_buckets.items()},
        "test_duration_sec": test_duration_sec,
    }


def print_stats(stats: dict, records: list[dict] = None) -> None:
    """Print concise TCP throughput analysis to console."""
    if not stats:
        print("No data to display.")
        return
    
    t = stats['throughput_mbps']
    print("\n" + "="*60)
    print("TCP THROUGHPUT ANALYSIS (Raw Socket Measurements)")
    print("="*60)
    print(f"Attempts: {stats['total_attempts']} | Success: {stats['successful']} | Failed: {stats['failed']}")
    print(f"Mean: {t['mean']:.4f} MB/s | Median: {t['median']:.4f} | σ: {t['stdev']:.4f}")
    print(f"Range: {t['min']:.4f} - {t['max']:.4f} MB/s | Stability: {(1-t['stdev']/t['mean'])*100:.0f}%" if t['mean'] > 0 else "")
    
    # Per-download table for short tests
    if stats['bucket_type'] == "download" and records and len(records) <= 20:
        print("\n-- Per-Download Performance --")
        successful = [r for r in records if r.get("success")]
        for i, r in enumerate(successful, 1):
            marker = " ← PEAK" if r["throughput_mbps"] == t['max'] else (" ← SLOW" if r["throughput_mbps"] == t['min'] else "")
            print(f"  #{i:2d}  {r['throughput_mbps']:.4f} MB/s  {r['duration_sec']:.3f}s  {r['bytes_received']/1024/1024:.1f}MB{marker}")
    
    # ASCII chart for longer tests
    if len(stats['period_avg_mbps']) > 1:
        print(f"\n-- TCP Throughput Distribution ({stats['bucket_type']}) --")
        max_val = max(stats['period_avg_mbps'].values()) or 1
        for key in sorted(stats['period_avg_mbps'].keys()):
            val = stats['period_avg_mbps'][key]
            filled = int((val / max_val) * 35)
            bar = "█" * filled + "░" * (35 - filled)
            label = stats['period_labels'][key]
            marker = " ← PEAK" if key == stats['best_period'] else ""
            print(f"  {label:>8}  {bar}  {val:.4f} MB/s{marker}")
    
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
    """Write professional, compact TCP performance report with comprehensive analysis."""
    if not stats:
        return None
    
    output_path = os.path.join(session_dir, "network_report.txt") if session_dir else "network_report.txt"
    t = stats['throughput_mbps']
    
    # Compute quality metrics
    sorted_tp = sorted(stats.get('throughputs', [t['mean']]))
    p95 = sorted_tp[int(len(sorted_tp) * 0.95)] if len(sorted_tp) > 1 else t['mean']
    p99 = sorted_tp[int(len(sorted_tp) * 0.99)] if len(sorted_tp) > 1 else t['mean']
    jitter = t['stdev'] / t['mean'] * 100 if t['mean'] > 0 else 0
    stability = (1 - jitter/100) * 100
    efficiency = (t['median'] / t['max'] * 100) if t['max'] > 0 else 0
    quality = "EXCELLENT" if jitter < 10 else ("VERY GOOD" if jitter < 20 else ("GOOD" if jitter < 35 else ("FAIR" if jitter < 50 else "POOR")))
    
    # Activity requirements and dynamic status
    activities = {
        "4K/8K Video Streaming": 25,
        "HD 1080p Streaming": 5,
        "Large File Downloads": 0.5,
        "Concurrent Downloads": 10,
        "Cloud Backup": 10,
        "Video Calls": 1,
    }
    
    def get_status(required_speed: float) -> tuple:
        """Compare requirement to user's speed, return (symbol, ideal_speed_str)."""
        ideal = f"{required_speed} MB/s"
        if t['mean'] < required_speed * 0.5:
            return ("✗ Not possible", ideal)
        elif t['mean'] < required_speed * 0.7:
            return ("✗ Not suitable", ideal)
        elif t['mean'] < required_speed:
            return ("! Marginal", ideal)
        elif t['mean'] < required_speed * 1.5:
            return ("◐ Works", ideal)
        else:
            return ("✓ Supported", ideal)
    
    use_cases = [(app, get_status(req)[0], get_status(req)[1]) for app, req in activities.items()]
    
    # Time estimates
    t1mb = 1/t['mean']*1000
    t100mb = 100/t['mean']
    t1gb = 1024/t['mean']/60
    t10gb = 10240/t['mean']/3600
    t100gb = 102400/t['mean']/3600
    
    # Congestion & buffer analysis (based on jitter/variability)
    # Logic: Higher jitter (variability) requires larger buffers to absorb throughput spikes
    if t['stdev'] < t['mean']*0.1:
        congestion = "LOW"
        buffer_rec = "16KB sufficient (stable connection)"
    elif t['stdev'] < t['mean']*0.2:
        congestion = "LOW-MODERATE"
        buffer_rec = "64KB-256KB recommended (minor variability)"
    elif t['stdev'] < t['mean']*0.35:
        congestion = "MODERATE"
        buffer_rec = "512KB-1MB recommended (significant variability)"
    else:
        congestion = "HIGH"
        buffer_rec = "2-5MB recommended (high variability)"
    
    # Transfer scheduling advice
    if stats['successful'] > 1:
        period_avg = stats['period_avg_mbps']
        best_key = stats['best_period']
        worst_key = min(period_avg.keys(), key=lambda k: period_avg[k])
        variance = ((period_avg[best_key]/period_avg[worst_key] - 1)*100) if period_avg[worst_key] > 0 else 0
        if variance < 15:
            schedule_advice = "Network stable - transfer anytime"
        elif variance < 40:
            schedule_advice = f"Minor variation - flexible scheduling OK"
        else:
            schedule_advice = f"High variance - schedule during {stats['period_labels'].get(best_key, 'peak')}"
    else:
        schedule_advice = "Single period - extend test for scheduling recommendations"
    
    lines = [
        "=" * 79,
        "TCP SOCKET NETWORK PERFORMANCE REPORT",
        "=" * 79,
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Test Duration: {stats['test_duration_sec']:.1f}s | Protocol: TCP/SSL | Samples: {stats['successful']}/20MB",
        "",
        "THROUGHPUT METRICS (Raw TCP Socket Measurements)",
        "-" * 79,
        f"  Mean Throughput:      {t['mean']:.6f} MB/s  (arithmetic average)",
        f"  Median Throughput:    {t['median']:.6f} MB/s  (middle value)",
        f"  Std Deviation:        {t['stdev']:.6f} MB/s  (variability measure)",
        f"  Min / Max:            {t['min']:.6f} / {t['max']:.6f} MB/s",
        f"  P95 Performance:      {p95:.6f} MB/s  (95% of transfers ≥ this)",
        f"  P99 Performance:      {p99:.6f} MB/s  (99% of transfers ≥ this)",
        f"  Jitter Index:         {jitter:.1f}%  (speed variability coefficient)",
        f"  Stability Rating:     {quality}",
        "",
        "TEST SUMMARY",
        "-" * 79,
        f"  Total Attempts:       {stats['total_attempts']}",
        f"  Successful:           {stats['successful']}",
        f"  Failed:               {stats['failed']}",
        f"  Success Rate:         {(stats['successful']/stats['total_attempts']*100):.1f}%",
        "",
    ]
    
    # Per-period analysis - prominent placement
    if stats['successful'] > 1:
        period_avg = stats['period_avg_mbps']
        best_key = stats['best_period']
        best_label = stats['period_labels'].get(best_key, "N/A")
        best_val = period_avg[best_key]
        worst_key = min(period_avg.keys(), key=lambda k: period_avg[k])
        worst_label = stats['period_labels'].get(worst_key, "N/A")
        worst_val = period_avg[worst_key]
        variance = ((best_val/worst_val - 1)*100) if worst_val > 0 else 0
        
        lines.extend([
            f"PER-{stats['bucket_type'].upper()} ANALYSIS",
            "-" * 79,
        ])
        
        # Show all periods if not too many
        if len(period_avg) <= 12:
            for key in sorted(period_avg.keys()):
                val = period_avg[key]
                label = stats['period_labels'].get(key, str(key))
                is_peak = " ← PEAK" if key == best_key else (" ← LOW" if key == worst_key else "")
                lines.append(f"  {label:15} {val:.6f} MB/s{is_peak}")
            lines.append("")
        
        lines.extend([
            f"  Peak Period:          {best_label} ({best_val:.6f} MB/s)",
            f"  Lowest Period:        {worst_label} ({worst_val:.6f} MB/s)",
            f"  Variance:             {variance:.1f}% difference between periods",
            f"  Consistency:          {efficiency:.0f}% (median vs peak smoothness)",
            "",
        ])
    
    lines.extend([
        "TCP CONNECTION CHARACTERISTICS",
        "-" * 79,
        f"  Connection Quality:   {quality}",
        f"  Consistency Index:    {stability:.0f}% (higher = more stable)",
        f"  Network Congestion:   {congestion}",
        "",
        "REAL-WORLD APPLICATIONS & SUITABILITY",
        "-" * 79,
        f"  Your Network Speed: {t['mean']:.2f} MB/s",
        "",
    ])
    
    lines.extend([
        "TRANSFER TIME ESTIMATES (at mean speed)",
        "-" * 79,
        f"  1 MB:                 {t1mb:.0f}ms",
        f"  10 MB:                {10/t['mean']:.1f}s",
        f"  100 MB:               {t100mb:.0f}s ({t100mb/60:.1f}m)",
        f"  1 GB:                 {t1gb:.1f}m ({t1gb/60:.2f}h)",
        f"  10 GB:                {t10gb:.2f}h",
        f"  100 GB:               {t100gb:.1f}h ({t100gb/24:.1f} days)",
        "",
    ])
    
    # Add use cases with ideal speed requirements
    lines.append(f"  {'APPLICATION':<32} {'STATUS':<20} IDEAL SPEED")
    lines.append("  " + "-" * 70)
    for app, status, ideal in use_cases:
        lines.append(f"  {app:<32} {status:<20} {ideal}")
    
    lines.extend([
        "",
        "PRACTICAL USAGE SCENARIOS",
        "-" * 79,
    ])
    
    # Add detailed practical scenarios based on throughput category
    if t['mean'] >= 100:
        scenarios = [
            "• Enterprise Data Centers: Transfer massive databases in minutes",
            "• 4K/8K Content Production: Stream multiple 4K cameras simultaneously (no buffering)",
            "• Real-time Video Conferencing: 20+ HD participants with screen sharing",
            "• Cloud Backup: Backup 1TB server in ~2.8 hours without impacting network",
            "• Scientific Research: Transfer 50GB datasets in ~8 minutes",
        ]
    elif t['mean'] >= 50:
        scenarios = [
            "• Media Production Offices: 4K video editing with remote storage access",
            "• University Networks: Multiple HD video streams for lectures",
            "• Small Business Backup: 100GB nightly backup in ~33 minutes",
            "• Live Streaming: Single 4K stream or multiple HD streams",
            "• Remote Workstations: CAD/3D modeling with cloud rendering",
        ]
    elif t['mean'] >= 10:
        scenarios = [
            "• Office Downloads: Large files in minutes (feasible but noticeable)",
            "• HD Video Streaming: One stream reliable, 2+ leads to buffering",
            "• Regular File Sharing: Suitable for distributed team collaboration",
            "• Database Synchronization: For regional office backup schemes",
            "• Software Distribution: Team updates within reasonable time",
        ]
    else:
        scenarios = [
            "• Email & Web Browsing: Adequate for office use, not for large transfers",
            "• Basic Video Calls: HD acceptable for single users (not groups)",
            "• Document Collaboration: Cloud storage sync works at slow pace",
            "• Streaming: YouTube 720p possible but frequent buffering expected",
            "• Not Suitable: 4K content, large file transfer, or bandwidth-intensive tasks",
        ]
    
    for scenario in scenarios:
        lines.append(f"  {scenario}")
    
    lines.extend([
        "TRANSFER RECOMMENDATIONS",
        "-" * 79,
    ])
    
    # Simple, concise scheduling recommendations
    if stats['successful'] > 1:
        period_avg = stats['period_avg_mbps']
        best_key = stats['best_period']
        worst_key = min(period_avg.keys(), key=lambda k: period_avg[k])
        variance = ((period_avg[best_key]/period_avg[worst_key] - 1)*100) if period_avg[worst_key] > 0 else 0
        best_label = stats['period_labels'].get(best_key, "peak")
        if variance < 5:
            timing_rec = "Anytime - very consistent"
        elif variance < 15:
            timing_rec = "Flexible - minor variations"
        else:
            timing_rec = f"Schedule during {best_label}"
    else:
        timing_rec = "Extend test for timing analysis"
    
    # Inline split strategy and concurrent limits
    if t['mean'] >= 10:
        split_strategy = "No splitting needed"
    elif t['mean'] >= 2:
        split_strategy = "Split files larger than 1GB"
    else:
        split_strategy = "Split files into 100-500MB chunks"
    
    if t['mean'] >= 50:
        concurrent = "Unlimited parallel transfers"
    elif t['mean'] >= 10:
        concurrent = "Maximum 2-3 parallel transfers"
    else:
        concurrent = "Only single transfer recommended"
    
    error_recovery = "Recommended - unstable connection" if stats['failed'] > 0 else "Not required - stable"
    
    lines.extend([
        f"  Transfer Timing:      {timing_rec}",
        f"  File Split Strategy:  {split_strategy}",
        f"  Max Parallel Files:   {concurrent}",
        f"  Error Recovery:       {error_recovery}",
        "",
        "=" * 79,
    ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✓ Report saved: network_report.txt")
    return output_path


def analyze_and_report(records: list[dict], session_dir: str = None) -> dict:
    """Execute TCP analysis pipeline."""
    stats = compute_stats(records)
    if stats:
        stats['throughputs'] = [r['throughput_mbps'] for r in records if r.get('success')]
        print_stats(stats, records)
        return {
            "stats": stats,
            "chart_path": save_chart(records, stats, session_dir),
            "report_path": write_report(stats, session_dir)
        }
    return {"stats": {}, "chart_path": None, "report_path": None}
