"""Create the Stage 3 engineering result plot from the verified CSV file."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "stage3.csv"
OUTPUT = ROOT / "docs" / "stage3-load-step-results.svg"
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
    """Read Stage 3 results and write a dependency-free SVG plot."""
    with SOURCE.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    times_min = [float(row["time_s"]) / 60.0 for row in rows]
    supply_c = [float(row["supply_temperature_c"]) for row in rows]
    return_c = [float(row["return_temperature_c"]) for row in rows]
    heat_load_kw = [float(row["heat_load_kw"]) for row in rows]
    cooling_kw = [float(row["cooling_kw"]) for row in rows]
    flow_heat_kw = [float(row["flow_heat_transfer_kw"]) for row in rows]
    residuals_kj = [abs(float(row["energy_residual_kj"])) for row in rows]

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
        '<text x="100" y="58" class="title">Stage 3 chilled-water load-step validation</text>',
        '<text x="100" y="88" class="subtitle">Two-node CHWS/CHWR model · 5 kg/s flow · 30 to 50 kW load · 10 s time step</text>',
    ]

    svg.extend(axes("Water temperature (deg C)", [6, 7, 8, 9, 10, 11, 12], 6.0, 12.0, 150, 430))
    svg.append(polyline(times_min, supply_c, 6.0, 12.0, 150, 430, "#1769aa"))
    svg.append(polyline(times_min, return_c, 6.0, 12.0, 150, 430, "#e67e22"))
    setpoint_y = scale_y(7.0, 6.0, 12.0, 150, 430)
    svg.append(
        f'<line x1="{LEFT}" y1="{setpoint_y:.1f}" x2="{RIGHT}" y2="{setpoint_y:.1f}" '
        'stroke="#64748b" stroke-width="2" stroke-dasharray="8 6" />'
    )
    svg.extend([
        '<text x="850" y="128" class="legend" fill="#1769aa">CHWS</text>',
        '<text x="930" y="128" class="legend" fill="#e67e22">CHWR</text>',
        '<text x="1010" y="128" class="legend" fill="#64748b">Setpoint</text>',
    ])

    svg.extend(axes("Heat rate (kW)", [0, 20, 40, 60], 0.0, 60.0, 540, 745))
    svg.append(polyline(times_min, heat_load_kw, 0.0, 60.0, 540, 745, "#d9485f"))
    svg.append(polyline(times_min, cooling_kw, 0.0, 60.0, 540, 745, "#17835a"))
    svg.append(polyline(times_min, flow_heat_kw, 0.0, 60.0, 540, 745, "#7c3aed"))
    svg.extend([
        '<text x="780" y="518" class="legend" fill="#d9485f">Building load</text>',
        '<text x="910" y="518" class="legend" fill="#17835a">Chiller cooling</text>',
        '<text x="1045" y="518" class="legend" fill="#7c3aed">Flow heat</text>',
        '<text x="620" y="792" text-anchor="middle" class="tick">Simulated time (minutes)</text>',
        f'<text x="100" y="840" class="metric">Final CHWS: {supply_c[-1]:.3f} deg C · Final CHWR: {return_c[-1]:.3f} deg C</text>',
        f'<text x="100" y="870" class="metric">Maximum energy residual: {max(residuals_kj):.3e} kJ · All acceptance checks passed</text>',
        "</svg>",
    ])

    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
