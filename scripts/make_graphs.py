#!/usr/bin/env python3
"""Create small SVG graphs from existing evidence logs only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "evidence" / "graphs"


@dataclass
class OomSeries:
    points: list[tuple[float, float]]
    process_missing_elapsed: float | None


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def parse_oom_monitor(path: Path) -> OomSeries:
    """Read monitor.sh output and keep only RSS change points."""
    rows: list[tuple[datetime, int]] = []
    process_missing_at: datetime | None = None

    for line in path.read_text().splitlines():
        parts = line.split()
        if parts and parts[0].startswith("2026-") and "process_missing" in line:
            process_missing_at = parse_iso(parts[0])
            continue
        if len(parts) < 6 or not parts[0].startswith("2026-"):
            continue
        try:
            timestamp = parse_iso(parts[0])
            rss_kb = int(parts[5])
        except (ValueError, IndexError):
            continue
        rows.append((timestamp, rss_kb))

    if not rows:
        return OomSeries([], None)

    base = rows[0][0]
    collapsed: list[tuple[float, float]] = []
    last_rss_kb: int | None = None
    for timestamp, rss_kb in rows:
        if rss_kb == last_rss_kb:
            continue
        elapsed = (timestamp - base).total_seconds()
        collapsed.append((elapsed, rss_kb / 1024))
        last_rss_kb = rss_kb

    missing_elapsed = None
    if process_missing_at is not None:
        missing_elapsed = (process_missing_at - base).total_seconds()

    return OomSeries(collapsed, missing_elapsed)


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


def point_xy(
    point: tuple[float, float],
    max_x: float,
    max_y: float,
    left: int,
    top: int,
    width: int,
    height: int,
) -> tuple[float, float]:
    x_value, y_value = point
    x = left + (x_value / (max_x or 1)) * width
    y = top + height - (y_value / (max_y or 1)) * height
    return x, y


def step_path(
    points: list[tuple[float, float]],
    max_x: float,
    max_y: float,
    left: int,
    top: int,
    width: int,
    height: int,
) -> str:
    """Build a stair-step path that matches sampled RSS changes."""
    if not points:
        return ""

    first_x, first_y = point_xy(points[0], max_x, max_y, left, top, width, height)
    parts = [f"M {first_x:.1f} {first_y:.1f}"]
    for point in points[1:]:
        x, y = point_xy(point, max_x, max_y, left, top, width, height)
        parts.append(f"H {x:.1f}")
        parts.append(f"V {y:.1f}")
    if len(points) == 1:
        parts.append(f"H {first_x + 1:.1f}")
    return " ".join(parts)


def svg_oom_graph(before: OomSeries, after: OomSeries, out_path: Path) -> None:
    """Write the OOM graph with limits and process_missing markers."""
    width, height = 980, 590
    left, top = 80, 60
    plot_width, plot_height = 700, 360
    max_x, max_y = 35.0, 300.0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>OOM RSS Growth from monitor.sh</title>",
        "<desc>Source values include 21620KB, 149640KB, 277620KB, process_missing, 128MB, and 256MB from existing evidence logs.</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="34" font-family="monospace" font-size="22" font-weight="bold">OOM RSS Growth from monitor.sh</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#333"/>',
        f'<text x="{left + plot_width // 2 - 140}" y="{top + plot_height + 48}" font-family="monospace" font-size="15">elapsed seconds from monitor start</text>',
        f'<text x="18" y="{top + plot_height // 2}" font-family="monospace" font-size="15" transform="rotate(-90 18,{top + plot_height // 2})">RSS MB</text>',
    ]

    for seconds in range(0, 36, 5):
        x = left + (seconds / max_x) * plot_width
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_height}" stroke="#eee"/>')
        lines.append(f'<text x="{x - 8:.1f}" y="{top + plot_height + 22}" font-family="monospace" font-size="12">{seconds}</text>')

    for value in [0, 64, 128, 192, 256, 300]:
        y = top + plot_height - (value / max_y) * plot_height
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#eee"/>')
        lines.append(f'<text x="30" y="{y + 4:.1f}" font-family="monospace" font-size="12">{value}</text>')

    for limit, color in [(128, "#868e96"), (256, "#495057")]:
        y = top + plot_height - (limit / max_y) * plot_height
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="{color}" stroke-dasharray="7 5"/>')
        lines.append(f'<text x="{left + plot_width + 18}" y="{y + 4:.1f}" font-family="monospace" font-size="13" fill="{color}">limit {limit}MB</text>')

    for label, color, series in [
        ("Before MEMORY_LIMIT=128", "#c92a2a", before),
        ("After MEMORY_LIMIT=256", "#1864ab", after),
    ]:
        path = step_path(series.points, max_x, max_y, left, top, plot_width, plot_height)
        if path:
            lines.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3"/>')
        for point in series.points:
            x, y = point_xy(point, max_x, max_y, left, top, plot_width, plot_height)
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        if series.process_missing_elapsed is not None:
            x = left + (series.process_missing_elapsed / max_x) * plot_width
            lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_height}" stroke="{color}" stroke-dasharray="4 4"/>')
            lines.append(f'<text x="{x + 5:.1f}" y="{top + 18}" font-family="monospace" font-size="12" fill="{color}">process_missing</text>')

    legend_x = left + plot_width + 18
    legend_y = top + 88
    for index, (label, color) in enumerate([
        ("Before MEMORY_LIMIT=128", "#c92a2a"),
        ("After MEMORY_LIMIT=256", "#1864ab"),
    ]):
        y = legend_y + index * 26
        lines.append(f'<rect x="{legend_x}" y="{y - 12}" width="16" height="4" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 24}" y="{y - 5}" font-family="monospace" font-size="13">{html.escape(label)}</text>')

    lines.extend(
        [
            f'<text x="{legend_x}" y="{legend_y + 76}" font-family="monospace" font-size="13">Before: run metadata survival 19s</text>',
            f'<text x="{legend_x}" y="{legend_y + 98}" font-family="monospace" font-size="13">After: run metadata survival 42s</text>',
            f'<text x="{legend_x}" y="{legend_y + 120}" font-family="monospace" font-size="13">process_missing marks monitor end</text>',
            f'<text x="{left}" y="{height - 42}" font-family="monospace" font-size="12">RSS values are sampled from monitor.sh. Repeated identical RSS samples were collapsed for readability.</text>',
            f'<text x="{left}" y="{height - 22}" font-family="monospace" font-size="12">Raw logs remain unchanged in evidence/oom/.</text>',
            "</svg>",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n")


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

    # OOM 그래프는 monitor.sh의 RSS 변화 지점과 process_missing 시점만 사용한다.
    oom_before = parse_oom_monitor(ROOT / "evidence" / "oom" / "before_monitor.log")
    oom_after = parse_oom_monitor(ROOT / "evidence" / "oom" / "after_monitor.log")
    svg_oom_graph(oom_before, oom_after, GRAPH_DIR / "01_oom_rss_growth.svg")

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
