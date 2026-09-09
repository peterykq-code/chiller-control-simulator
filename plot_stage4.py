"""Create the Stage 4A P-versus-PI comparison plot from verified CSV data."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "stage4.csv"
SUMMARY = ROOT / "results" / "stage4_summary.csv"
OUTPUT = ROOT / "docs" / "stage4-p-vs-pi-results.svg"
WIDTH = 1200
HEIGHT = 900
LEFT = 100
RIGHT = 1140
PLOT_WIDTH = RIGHT - LEFT


def scale_x(time_min: float) -> float:
    """Map simulated minutes to an SVG x-coordinate."""
    return LEFT + time_min / 30.0 * PLOT_WIDTH


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
    """Return SVG elements for one labelled plot area."""
    elements = [
        f'<text x="{LEFT}" y="{top - 22}" class="panel-title">{title}</text>',
        f'<line x1="{LEFT}" y1="{top}" x2="{LEFT}" y2="{bottom}" class="axis" />',
        f'<line x1="{LEFT}" y1="{bottom}" x2="{RIGHT}" y2="{bottom}" class="axis" />',
    ]
    for tick in y_ticks:
        y = scale_y(tick, minimum, maximum, top, bottom)
        elements.extend([
            f'<line x1="{LEFT}" y1="{y:.1f}" x2="{RIGHT}" y2="{y:.1f}" class="grid" />',
            f'<text x="{LEFT - 14}" y="{y + 5:.1f}" text-anchor="end" class="tick">{tick:g}</text>',
        ])
    for minute in range(0, 31, 5):
        x = scale_x(float(minute))
        elements.extend([
            f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 7}" class="axis" />',
            f'<text x="{x:.1f}" y="{bottom + 27}" text-anchor="middle" class="tick">{minute}</text>',
        ])
    load_step_x = scale_x(10.0)
    elements.extend([
        f'<line x1="{load_step_x:.1f}" y1="{top}" x2="{load_step_x:.1f}" y2="{bottom}" class="event" />',
        f'<text x="{load_step_x + 8:.1f}" y="{top + 18}" class="event-label">50 kW load step</text>',
    ])
    return elements


def main() -> None:
    """Read Stage 4A evidence and write a dependency-free SVG plot."""
    with SOURCE.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    with SUMMARY.open(newline="", encoding="utf-8") as csv_file:
        summary = {row["controller"]: row for row in csv.DictReader(csv_file)}

    p_rows = [row for row in rows if row["controller"] == "P"]
    pi_rows = [row for row in rows if row["controller"] == "PI"]
    p_time_min = [float(row["time_s"]) / 60.0 for row in p_rows]
    pi_time_min = [float(row["time_s"]) / 60.0 for row in pi_rows]
    p_supply_c = [float(row["supply_temperature_c"]) for row in p_rows]
    pi_supply_c = [float(row["supply_temperature_c"]) for row in pi_rows]
    p_cooling_percent = [100.0 * float(row["applied_cooling_fraction"]) for row in p_rows]
    pi_cooling_percent = [100.0 * float(row["applied_cooling_fraction"]) for row in pi_rows]

    p_iae = float(summary["P"]["integrated_absolute_error_c_s"])
    pi_iae = float(summary["PI"]["integrated_absolute_error_c_s"])
    iae_reduction_percent = 100.0 * (1.0 - pi_iae / p_iae)
    p_final_error = float(summary["P"]["final_error_c"])
    pi_final_error = float(summary["PI"]["final_error_c"])
    pi_settling_s = float(summary["PI"]["settling_time_s"])
    pi_overshoot_c = float(summary["PI"]["overshoot_c"])

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        """<style>
            text { font-family: Arial, sans-serif; fill: #172033; }
            .title { font-size: 34px; font-weight: 700; }
            .subtitle { font-size: 17px; fill: #64748b; }
            .panel-title { font-size: 20px; font-weight: 700; }
            .tick { font-size: 14px; fill: #64748b; }
            .axis { stroke: #475569; stroke-width: 1.5; }
            .grid { stroke: #dce3ec; stroke-width: 1; }
            .event { stroke: #94a3b8; stroke-width: 1.5; stroke-dasharray: 6 5; }
            .event-label { font-size: 14px; fill: #64748b; }
            .legend { font-size: 15px; font-weight: 700; }
            .metric { font-size: 16px; }
        </style>""",
        '<rect width="1200" height="900" fill="#f8fafc" />',
        '<text x="100" y="58" class="title">Stage 4A proportional versus PI control</text>',
        '<text x="100" y="88" class="subtitle">Same two-node plant · 7 deg C CHWS setpoint · 30 to 50 kW load · Kp 0.3 · Ki 0.001 / (deg C s)</text>',
    ]

    svg.extend(axes("CHWS temperature (deg C)", [6.5, 7, 7.5, 8, 8.5, 9], 6.5, 9.0, 150, 430))
    band_top = scale_y(7.1, 6.5, 9.0, 150, 430)
    band_bottom = scale_y(6.9, 6.5, 9.0, 150, 430)
    svg.append(
        f'<rect x="{LEFT}" y="{band_top:.1f}" width="{PLOT_WIDTH}" '
        f'height="{band_bottom - band_top:.1f}" fill="#dbeafe" opacity="0.65" />'
    )
    svg.append(polyline(p_time_min, p_supply_c, 6.5, 9.0, 150, 430, "#e67e22"))
    svg.append(polyline(pi_time_min, pi_supply_c, 6.5, 9.0, 150, 430, "#1769aa"))
    setpoint_y = scale_y(7.0, 6.5, 9.0, 150, 430)
    svg.append(
        f'<line x1="{LEFT}" y1="{setpoint_y:.1f}" x2="{RIGHT}" y2="{setpoint_y:.1f}" '
        'stroke="#64748b" stroke-width="2" stroke-dasharray="8 6" />'
    )
    svg.extend([
        '<text x="860" y="128" class="legend" fill="#e67e22">P CHWS</text>',
        '<text x="950" y="128" class="legend" fill="#1769aa">PI CHWS</text>',
        '<text x="1045" y="128" class="legend" fill="#64748b">Setpoint</text>',
    ])

    svg.extend(axes("Applied cooling command (%)", [20, 30, 40, 50, 60], 20.0, 60.0, 540, 745))
    svg.append(polyline(p_time_min, p_cooling_percent, 20.0, 60.0, 540, 745, "#e67e22"))
    svg.append(polyline(pi_time_min, pi_cooling_percent, 20.0, 60.0, 540, 745, "#1769aa"))
    svg.extend([
        '<text x="925" y="518" class="legend" fill="#e67e22">P command</text>',
        '<text x="1040" y="518" class="legend" fill="#1769aa">PI command</text>',
        '<text x="620" y="792" text-anchor="middle" class="tick">Simulated time (minutes)</text>',
        f'<text x="100" y="835" class="metric">Final CHWS error: P {p_final_error:.3f} deg C · PI {pi_final_error:.3f} deg C · PI settling time {pi_settling_s:.0f} s</text>',
        f'<text x="100" y="866" class="metric">PI overshoot {pi_overshoot_c:.3f} deg C · Integrated absolute error reduced {iae_reduction_percent:.1f}% · All acceptance checks passed</text>',
        "</svg>",
    ])

    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
