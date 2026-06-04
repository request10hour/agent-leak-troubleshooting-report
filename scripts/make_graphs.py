#!/usr/bin/env python3
"""Create small SVG graphs from existing evidence logs only."""

from __future__ import annotations

from datetime import datetime
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "evidence" / "graphs"


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def parse_oom_monitor(path: Path) -> list[tuple[float, float]]:
    """Read monitor.sh output and return elapsed seconds with RSS in MB."""
    rows: list[tuple[datetime, float]] = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 6 or not parts[0].startswith("2026-"):
            continue
        if "process_missing" in line:
            continue
        try:
            timestamp = parse_iso(parts[0])
            rss_mb = int(parts[5]) / 1024
        except (ValueError, IndexError):
            continue
        rows.append((timestamp, rss_mb))

    if not rows:
        return []

    base = rows[0][0]
    return [((ts - base).total_seconds(), rss) for ts, rss in rows]


def parse_cpu_log(path: Path) -> list[tuple[float, float]]:
    """Read CpuWorker log lines and return elapsed seconds with load percent."""
    timestamp_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})")
    load_patterns = [
        re.compile(r"Current Load: ([0-9.]+)%"),
        re.compile(r"Peak reached \(([0-9.]+)%\)"),
        re.compile(r"Cooldown complete \(([0-9.]+)%\)"),
    ]

    rows: list[tuple[datetime, float]] = []
    for line in path.read_text().splitlines():
        ts_match = timestamp_re.search(line)
        if not ts_match:
            continue

        value = None
        for pattern in load_patterns:
            match = pattern.search(line)
            if match:
                value = float(match.group(1))
                break
        if value is None:
            continue

        timestamp = datetime.strptime(
            f"{ts_match.group(1)}.{ts_match.group(2)}", "%Y-%m-%d %H:%M:%S.%f"
        )
        rows.append((timestamp, value))

    if not rows:
        return []

    base = rows[0][0]
    return [((ts - base).total_seconds(), value) for ts, value in rows]


def scale_points(
    series: list[tuple[float, float]],
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    left: int,
    top: int,
    width: int,
    height: int,
) -> str:
    points = []
    for x_value, y_value in series:
        x = left + ((x_value - min_x) / (max_x - min_x or 1)) * width
        y = top + height - ((y_value - min_y) / (max_y - min_y or 1)) * height
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def svg_graph(
    title: str,
    y_label: str,
    series: list[tuple[str, str, list[tuple[float, float]]]],
    out_path: Path,
    desc: str,
) -> None:
    """Write a simple line chart without external plotting libraries."""
    width, height = 900, 520
    left, top = 80, 60
    plot_width, plot_height = 720, 340

    all_points = [point for _, _, rows in series for point in rows]
    max_x = max((x for x, _ in all_points), default=1)
    max_y = max((y for _, y in all_points), default=1)
    max_y = max_y * 1.1

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<title>{html.escape(title)}</title>",
        f"<desc>{html.escape(desc)}</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="35" font-family="monospace" font-size="22" font-weight="bold">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#333"/>',
        f'<text x="{left + plot_width // 2 - 70}" y="{top + plot_height + 50}" font-family="monospace" font-size="15">elapsed seconds</text>',
        f'<text x="18" y="{top + plot_height // 2}" font-family="monospace" font-size="15" transform="rotate(-90 18,{top + plot_height // 2})">{html.escape(y_label)}</text>',
    ]

    for index in range(6):
        x = left + (plot_width / 5) * index
        seconds = (max_x / 5) * index
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_height}" stroke="#eee"/>')
        lines.append(f'<text x="{x - 12:.1f}" y="{top + plot_height + 22}" font-family="monospace" font-size="12">{seconds:.0f}</text>')

    for index in range(6):
        y = top + plot_height - (plot_height / 5) * index
        value = (max_y / 5) * index
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#eee"/>')
        lines.append(f'<text x="20" y="{y + 4:.1f}" font-family="monospace" font-size="12">{value:.1f}</text>')

    legend_y = top
    for label, color, rows in series:
        if rows:
            points = scale_points(rows, 0, max_x, 0, max_y, left, top, plot_width, plot_height)
            lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"/>')
            for x_value, y_value in rows:
                x = left + (x_value / (max_x or 1)) * plot_width
                y = top + plot_height - (y_value / (max_y or 1)) * plot_height
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
        lines.append(f'<rect x="{left + plot_width + 25}" y="{legend_y - 12}" width="16" height="4" fill="{color}"/>')
        lines.append(f'<text x="{left + plot_width + 48}" y="{legend_y - 5}" font-family="monospace" font-size="14">{html.escape(label)}</text>')
        legend_y += 26

    lines.append("</svg>")
    out_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    # OOM 그래프는 monitor.sh의 RSS 값을 그대로 사용한다.
    oom_before = parse_oom_monitor(ROOT / "evidence" / "oom" / "before_monitor.log")
    oom_after = parse_oom_monitor(ROOT / "evidence" / "oom" / "after_monitor.log")
    svg_graph(
        "OOM RSS Growth",
        "RSS MB",
        [
            ("Before MEMORY_LIMIT=128", "#c92a2a", oom_before),
            ("After MEMORY_LIMIT=256", "#1864ab", oom_after),
        ],
        GRAPH_DIR / "01_oom_rss_growth.svg",
        "Source values include 21620KB, 149640KB, and 277620KB from monitor logs.",
    )

    # CPU 그래프는 CpuWorker가 로그에 남긴 load 값만 사용한다.
    cpu_before = parse_cpu_log(ROOT / "evidence" / "cpu" / "before_app.log")
    cpu_after = parse_cpu_log(ROOT / "evidence" / "cpu" / "after_app.log")
    svg_graph(
        "CPU Load Growth",
        "CpuWorker Load %",
        [
            ("Before CPU_MAX_OCCUPY=100", "#c92a2a", cpu_before),
            ("After CPU_MAX_OCCUPY=10", "#2b8a3e", cpu_after),
        ],
        GRAPH_DIR / "02_cpu_load_growth.svg",
        "Source values include 57.45 and 10.00 from CpuWorker logs.",
    )

    print("Created graphs:")
    for path in sorted(GRAPH_DIR.glob("*.svg")):
        print(path)


if __name__ == "__main__":
    main()
