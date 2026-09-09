"""Create the Stage 5A anti-windup comparison plot from verified CSV data."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "stage5.csv"
SUMMARY = ROOT / "results" / "stage5_summary.csv"
OUTPUT = ROOT / "docs" / "stage5-anti-windup-results.svg"
WIDTH = 1200
HEIGHT = 1050
LEFT = 100
RIGHT = 1140
PLOT_WIDTH = RIGHT - LEFT


def scale_x(time_min: float) -> float:
    """Map simulated minutes to an SVG x-coordinate."""
    return LEFT + time_min / 60.0 * PLOT_WIDTH


def scale_y(value: float, minimum: float, maximum: float, top: int, bottom: int) -> float:
    """Map an engineering value to an SVG y-coordinate."""
    return bottom - (value - minimum) / (maximum - minimum) * (bottom - top)


def polyline(
    x_values: list[float],
    y_values: list[float],
    minimum: float,
    maximum: float,
    top: int,
    bottom: int,
    colour: str,
) -> str:
    """Return one SVG polyline for a data series."""
    points = " ".join(
        f"{scale_x(x_value):.1f},{scale_y(y_value, minimum, maximum, top, bottom):.1f}"
        for x_value, y_value in zip(x_values, y_values)
    )
    return (
        f'<polyline points="{points}" fill="none" stroke="{colour}" '
        'stroke-width="3" stroke-linejoin="round" />'
    )


def axes(
    title: str,
    y_ticks: list[float],
    minimum: float,
    maximum: float,
    top: int,
    bottom: int,
) -> list[str]:
    """Return labelled axes, grid lines, and the overload interval."""
    elements = [
        f'<text x="{LEFT}" y="{top - 18}" class="panel-title">{title}</text>',
        f'<rect x="{scale_x(10):.1f}" y="{top}" width="{scale_x(20) - scale_x(10):.1f}" height="{bottom - top}" fill="#fee2e2" opacity="0.6" />',
        f'<line x1="{LEFT}" y1="{top}" x2="{LEFT}" y2="{bottom}" class="axis" />',
        f'<line x1="{LEFT}" y1="{bottom}" x2="{RIGHT}" y2="{bottom}" class="axis" />',
    ]
    for tick in y_ticks:
        y = scale_y(tick, minimum, maximum, top, bottom)
        elements.extend([
            f'<line x1="{LEFT}" y1="{y:.1f}" x2="{RIGHT}" y2="{y:.1f}" class="grid" />',
            f'<text x="{LEFT - 14}" y="{y + 5:.1f}" text-anchor="end" class="tick">{tick:g}</text>',
        ])
    for minute in range(0, 61, 10):
        x = scale_x(float(minute))
        elements.extend([
            f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 7}" class="axis" />',
            f'<text x="{x:.1f}" y="{bottom + 25}" text-anchor="middle" class="tick">{minute}</text>',
        ])
    for minute, label in ((10, "120 kW overload"), (20, "30 kW recovery")):
        x = scale_x(float(minute))
        elements.extend([
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" class="event" />',
            f'<text x="{x + 7:.1f}" y="{top + 17}" class="event-label">{label}</text>',
        ])
    return elements


def main() -> None:
    """Read Stage 5 evidence and write a dependency-free SVG plot."""
    with SOURCE.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    with SUMMARY.open(newline="", encoding="utf-8") as csv_file:
        summary = {row["controller"]: row for row in csv.DictReader(csv_file)}

    no_aw_rows = [row for row in rows if row["controller"] == "PI_NO_ANTI_WINDUP"]
    aw_rows = [row for row in rows if row["controller"] == "PI_ANTI_WINDUP"]
    no_aw_time = [float(row["time_s"]) / 60.0 for row in no_aw_rows]
    aw_time = [float(row["time_s"]) / 60.0 for row in aw_rows]

    no_aw = summary["PI_NO_ANTI_WINDUP"]
    aw = summary["PI_ANTI_WINDUP"]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        """<style>
            text { font-family: Arial, sans-serif; fill: #172033; }
            .title { font-size: 32px; font-weight: 700; }
            .subtitle { font-size: 16px; fill: #64748b; }
            .panel-title { font-size: 19px; font-weight: 700; }
            .tick { font-size: 13px; fill: #64748b; }
            .axis { stroke: #475569; stroke-width: 1.5; }
            .grid { stroke: #dce3ec; stroke-width: 1; }
            .event { stroke: #94a3b8; stroke-width: 1.5; stroke-dasharray: 6 5; }
            .event-label { font-size: 13px; fill: #64748b; }
            .legend { font-size: 14px; font-weight: 700; }
            .metric { font-size: 15px; }
        </style>""",
        '<rect width="1200" height="1050" fill="#f8fafc" />',
        '<text x="100" y="48" class="title">Stage 5A PI saturation and anti-windup recovery</text>',
        '<text x="100" y="77" class="subtitle">30 to 120 kW overload at 10 min · return to 30 kW at 20 min · 100 kW cooling limit · same two-node plant</text>',
        '<text x="830" y="108" class="legend" fill="#e67e22">Without anti-windup</text>',
        '<text x="1010" y="108" class="legend" fill="#1769aa">With anti-windup</text>',
    ]

    svg.extend(axes("CHWS temperature (deg C)", [4, 5, 6, 7, 8, 9, 10], 3.5, 10.5, 140, 380))
    svg.append(polyline(no_aw_time, [float(row["supply_temperature_c"]) for row in no_aw_rows], 3.5, 10.5, 140, 380, "#e67e22"))
    svg.append(polyline(aw_time, [float(row["supply_temperature_c"]) for row in aw_rows], 3.5, 10.5, 140, 380, "#1769aa"))
    setpoint_y = scale_y(7.0, 3.5, 10.5, 140, 380)
    svg.append(f'<line x1="{LEFT}" y1="{setpoint_y:.1f}" x2="{RIGHT}" y2="{setpoint_y:.1f}" stroke="#64748b" stroke-width="2" stroke-dasharray="8 6" />')

    svg.extend(axes("Applied cooling command (%)", [0, 25, 50, 75, 100], 0, 100, 470, 680))
    svg.append(polyline(no_aw_time, [100 * float(row["applied_cooling_fraction"]) for row in no_aw_rows], 0, 100, 470, 680, "#e67e22"))
    svg.append(polyline(aw_time, [100 * float(row["applied_cooling_fraction"]) for row in aw_rows], 0, 100, 470, 680, "#1769aa"))

    svg.extend(axes("Accumulated integral error (deg C s)", [0, 500, 1000, 1500, 2000], 0, 2000, 770, 950))
    svg.append(polyline(no_aw_time, [float(row["integral_error_c_s"]) for row in no_aw_rows], 0, 2000, 770, 950, "#e67e22"))
    svg.append(polyline(aw_time, [float(row["integral_error_c_s"]) for row in aw_rows], 0, 2000, 770, 950, "#1769aa"))
    svg.extend([
        '<text x="620" y="987" text-anchor="middle" class="tick">Simulated time (minutes)</text>',
        f'<text x="100" y="1018" class="metric">Saturation release: without {float(no_aw["saturation_release_time_s"]):.0f} s · with {float(aw["saturation_release_time_s"]):.0f} s | Recovery undershoot: without {float(no_aw["recovery_undershoot_c"]):.3f} deg C · with {float(aw["recovery_undershoot_c"]):.3f} deg C</text>',
        "</svg>",
    ])
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
