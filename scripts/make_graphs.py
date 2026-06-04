#!/usr/bin/env python3
"""Create SVG graphs from existing evidence logs only."""

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
    first_rss_kb: int
    last_rss_kb: int


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def parse_oom_monitor(path: Path) -> OomSeries:
    """Read monitor.sh output and keep RSS change points only."""
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
            rows.append((parse_iso(parts[0]), int(parts[5])))
        except (ValueError, IndexError):
            continue

    if not rows:
        return OomSeries([], None, 0, 0)

    base = rows[0][0]
    points: list[tuple[float, float]] = []
    last_seen_rss: int | None = None
    for timestamp, rss_kb in rows:
        if rss_kb == last_seen_rss:
            continue
        points.append(((timestamp - base).total_seconds(), rss_kb / 1024))
        last_seen_rss = rss_kb

    missing_elapsed = None
    if process_missing_at is not None:
        missing_elapsed = (process_missing_at - base).total_seconds()

    return OomSeries(points, missing_elapsed, rows[0][1], rows[-1][1])


def parse_cpu_log(path: Path) -> list[tuple[float, float]]:
    """Read CpuWorker load values from app logs."""
    timestamp_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})")
    load_patterns = [
        re.compile(r"Current Load: ([0-9.]+)%"),
        re.compile(r"Peak reached \(([0-9.]+)%\)"),
        re.compile(r"Cooldown complete \(([0-9.]+)%\)"),
        re.compile(r"CPU Threshold Violated! \(([0-9.]+)%\)"),
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
    return [((timestamp - base).total_seconds(), value) for timestamp, value in rows]


def point_xy(
    point: tuple[float, float],
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    left: float,
    top: float,
    width: float,
    height: float,
) -> tuple[float, float]:
    x_value, y_value = point
    x = left + ((x_value - min_x) / (max_x - min_x or 1)) * width
    y = top + height - ((y_value - min_y) / (max_y - min_y or 1)) * height
    return x, y


def polyline_points(
    rows: list[tuple[float, float]],
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    left: float,
    top: float,
    width: float,
    height: float,
) -> str:
    return " ".join(
        f"{x:.1f},{y:.1f}"
        for x, y in (
            point_xy(point, min_x, max_x, min_y, max_y, left, top, width, height)
            for point in rows
        )
    )


def text(x: float, y: float, value: str, size: int = 13, fill: str = "#212529", weight: str = "normal") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="monospace" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(value)}</text>'
    )


def draw_axes(
    lines: list[str],
    left: float,
    top: float,
    width: float,
    height: float,
    max_x: float,
    max_y: float,
    x_ticks: list[int],
    y_ticks: list[int],
    y_label: bool = False,
) -> None:
    """Draw shared axis and grid elements."""
    lines.append(f'<line x1="{left}" y1="{top + height}" x2="{left + width}" y2="{top + height}" stroke="#343a40"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + height}" stroke="#343a40"/>')

    for tick in x_ticks:
        x = left + (tick / max_x) * width
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + height}" stroke="#edf2f7"/>')
        lines.append(text(x - 8, top + height + 20, str(tick), 11, "#495057"))

    for tick in y_ticks:
        y = top + height - (tick / max_y) * height
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + width}" y2="{y:.1f}" stroke="#edf2f7"/>')
        lines.append(text(left - 38, y + 4, str(tick), 11, "#495057"))

    if y_label:
        lines.append(
            f'<text x="18" y="{top + height / 2:.1f}" font-family="monospace" '
            f'font-size="13" fill="#212529" transform="rotate(-90 18,{top + height / 2:.1f})">RSS MB</text>'
        )


def draw_oom_panel(
    lines: list[str],
    title: str,
    series: OomSeries,
    limit_mb: int,
    color: str,
    left: float,
    top: float,
    width: float,
    height: float,
    show_y_label: bool,
) -> None:
    """Draw one OOM panel using the same scale as the other panel."""
    max_x, max_y = 35.0, 300.0
    draw_axes(lines, left, top, width, height, max_x, max_y, [0, 10, 20, 30, 35], [0, 50, 100, 150, 200, 250, 300], show_y_label)

    lines.append(text(left, top - 18, title, 15, "#212529", "bold"))
    limit_y = top + height - (limit_mb / max_y) * height
    lines.append(f'<line x1="{left}" y1="{limit_y:.1f}" x2="{left + width}" y2="{limit_y:.1f}" stroke="#868e96" stroke-dasharray="6 5"/>')
    lines.append(text(left + width - 86, limit_y - 7, f"limit {limit_mb}MB", 12, "#495057"))

    if series.points:
        lines.append(
            f'<polyline points="{polyline_points(series.points, 0, max_x, 0, max_y, left, top, width, height)}" '
            f'fill="none" stroke="{color}" stroke-width="3"/>'
        )
        for point in series.points:
            x, y = point_xy(point, 0, max_x, 0, max_y, left, top, width, height)
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')

    if series.process_missing_elapsed is not None:
        x = left + (series.process_missing_elapsed / max_x) * width
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + height}" stroke="{color}" stroke-dasharray="4 4"/>')
        lines.append(text(min(x + 6, left + width - 96), top + 18, "process_missing", 11, color))

    lines.append(text(left + 6, top + height - 12, f"RSS {series.first_rss_kb}KB -> {series.last_rss_kb}KB", 12, color))


def svg_oom_graph(before: OomSeries, after: OomSeries, out_path: Path) -> None:
    """Write a two-panel OOM graph with unclipped labels."""
    width, height = 1100, 560
    top = 92
    panel_w, panel_h = 430, 295
    before_left, after_left = 78, 610

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>OOM RSS Growth from monitor.sh</title>",
        "<desc>Source values include 21620KB, 149640KB, 21580KB, 277620KB, process_missing, 128MB, and 256MB from existing evidence logs.</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        text(60, 38, "OOM RSS Growth from monitor.sh", 22, "#212529", "bold"),
    ]

    draw_oom_panel(lines, "Before: MEMORY_LIMIT=128MB", before, 128, "#c92a2a", before_left, top, panel_w, panel_h, True)
    draw_oom_panel(lines, "After: MEMORY_LIMIT=256MB", after, 256, "#1864ab", after_left, top, panel_w, panel_h, False)

    lines.extend(
        [
            text(405, 438, "elapsed seconds from monitor start", 13, "#212529"),
            '<rect x="344" y="464" width="20" height="4" fill="#c92a2a"/>',
            text(372, 469, "Before RSS", 12, "#212529"),
            '<rect x="494" y="464" width="20" height="4" fill="#1864ab"/>',
            text(522, 469, "After RSS", 12, "#212529"),
            '<line x1="646" y1="464" x2="686" y2="464" stroke="#868e96" stroke-dasharray="6 5"/>',
            text(696, 469, "MEMORY_LIMIT", 12, "#212529"),
            text(78, 508, "Raw RSS samples from monitor.sh. Duplicate RSS values were collapsed for readability.", 12, "#495057"),
            text(78, 530, "Survival comparison is reported in the Before & After table. Raw logs remain unchanged in evidence/oom/.", 12, "#495057"),
            "</svg>",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n")


def svg_cpu_graph(before: list[tuple[float, float]], after: list[tuple[float, float]], out_path: Path) -> None:
    """Write the CPU graph with fixed ticks and threshold annotations."""
    width, height = 1000, 500
    left, top = 78, 70
    plot_w, plot_h = 800, 290
    max_x, max_y = 65.0, 60.0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>CPU Load from CpuWorker logs</title>",
        "<desc>Source values include 57.45, 10.00, CPU Threshold Violated, 50 guideline, and 10 target from existing evidence logs.</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        text(60, 36, "CPU Load from CpuWorker logs", 22, "#212529", "bold"),
    ]

    draw_axes(lines, left, top, plot_w, plot_h, max_x, max_y, [0, 10, 20, 30, 40, 50, 60], [0, 10, 20, 30, 40, 50, 60], False)
    lines.append(
        f'<text x="18" y="{top + plot_h / 2:.1f}" font-family="monospace" font-size="13" '
        f'fill="#212529" transform="rotate(-90 18,{top + plot_h / 2:.1f})">CpuWorker Load %</text>'
    )

    for value, label, color in [(10, "10% target", "#2b8a3e"), (50, "50% guideline", "#f08c00")]:
        y = top + plot_h - (value / max_y) * plot_h
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="{color}" stroke-dasharray="7 5"/>')
        lines.append(text(left + plot_w - 126, y - 7, label, 12, color))

    for label, color, rows in [
        ("Before: CPU_MAX_OCCUPY=100", "#c92a2a", before),
        ("After: CPU_MAX_OCCUPY=10", "#2b8a3e", after),
    ]:
        if rows:
            lines.append(
                f'<polyline points="{polyline_points(rows, 0, max_x, 0, max_y, left, top, plot_w, plot_h)}" '
                f'fill="none" stroke="{color}" stroke-width="3"/>'
            )
            for point in rows:
                x, y = point_xy(point, 0, max_x, 0, max_y, left, top, plot_w, plot_h)
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')

    if before:
        violation = before[-1]
        x, y = point_xy(violation, 0, max_x, 0, max_y, left, top, plot_w, plot_h)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" stroke="#c92a2a" stroke-dasharray="4 4"/>')
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#c92a2a" stroke="#7f1d1d" stroke-width="2"/>')
        lines.append(text(x + 10, max(y - 12, top + 14), "CPU Threshold Violated! (57.45%)", 12, "#c92a2a", "bold"))
        lines.append(text(x + 10, max(y + 7, top + 32), "violation / PID missing", 11, "#c92a2a"))

    lines.extend(
        [
            '<rect x="100" y="388" width="20" height="4" fill="#c92a2a"/>',
            text(128, 393, "Before: CPU_MAX_OCCUPY=100", 12, "#212529"),
            '<rect x="360" y="388" width="20" height="4" fill="#2b8a3e"/>',
            text(388, 393, "After: CPU_MAX_OCCUPY=10", 12, "#212529"),
            text(366, 430, "elapsed seconds from CpuWorker log start", 13, "#212529"),
            text(78, 466, "CPU values are app-internal CpuWorker load values. top/ps evidence is preserved in evidence/cpu/.", 12, "#495057"),
            "</svg>",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    # OOM graph uses monitor.sh RSS change points only.
    oom_before = parse_oom_monitor(ROOT / "evidence" / "oom" / "before_monitor.log")
    oom_after = parse_oom_monitor(ROOT / "evidence" / "oom" / "after_monitor.log")
    svg_oom_graph(oom_before, oom_after, GRAPH_DIR / "01_oom_rss_growth.svg")

    # CPU graph uses CpuWorker load values from app logs only.
    cpu_before = parse_cpu_log(ROOT / "evidence" / "cpu" / "before_app.log")
    cpu_after = parse_cpu_log(ROOT / "evidence" / "cpu" / "after_app.log")
    svg_cpu_graph(cpu_before, cpu_after, GRAPH_DIR / "02_cpu_load_growth.svg")

    print("Created graphs:")
    for path in sorted(GRAPH_DIR.glob("*.svg")):
        print(path)


if __name__ == "__main__":
    main()
