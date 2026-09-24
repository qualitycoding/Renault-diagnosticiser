"""Self-contained HTML report (D-011, D-016)."""
import csv
import html as _html


def mask_vin(vin: str | None) -> str:
    if not vin:
        return "unknown"
    if len(vin) <= 4:
        return "*" * len(vin)
    return "*" * (len(vin) - 4) + vin[-4:]


def _e(value) -> str:
    return _html.escape(str(value), quote=True)


def _dtc_row(d, descriptions) -> str:
    desc = ""
    if descriptions:
        desc = descriptions.get(d.code, "")
    status_txt = f"0x{d.status:02X}" if d.status is not None else ""
    return (f"<tr><td>{_e(d.code)}</td><td>{_e(status_txt)}</td>"
           f"<td>{_e(d.source)}</td><td>{_e(desc)}</td></tr>")


def _generic_section(generic, show_vin, descriptions) -> str:
    if generic is None:
        return "<section><h2>Generic OBD</h2><p>not read</p></section>"
    vin_display = generic.vin if show_vin else mask_vin(generic.vin)
    rows = "".join(_dtc_row(d, descriptions) for d in (generic.stored + generic.pending))
    readiness_rows = "".join(
        f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in sorted(generic.readiness.items()))
    return f"""<section>
<h2>Generic OBD</h2>
<p>VIN: {_e(vin_display)}</p>
<p>MIL: {_e(generic.mil_on)}</p>
<p>DTC count: {_e(generic.dtc_count)}</p>
<p>Protocol: {_e(generic.protocol)}</p>
<table><caption>Codes</caption><thead><tr><th>Code</th><th>Status</th><th>Source</th><th>Description</th></tr></thead>
<tbody>{rows}</tbody></table>
<table><caption>Readiness monitors</caption><thead><tr><th>Monitor</th><th>State</th></tr></thead>
<tbody>{readiness_rows}</tbody></table>
</section>"""


def _ecu_section(ecus, descriptions) -> str:
    parts = []
    for e in ecus:
        rows = "".join(_dtc_row(d, descriptions) for d in e.dtcs)
        extra = ""
        if e.protocol == "kwp":
            extra = f"<p>KWP DTC count: {_e(e.kwp_dtc_count)} raw: {_e(e.kwp_raw)}</p>"
        err = f"<p class='error'>{_e(e.error)}</p>" if e.error else ""
        parts.append(f"""<article>
<h3>{_e(e.ecu)}</h3>
<p>present: {_e(e.present)} protocol: {_e(e.protocol)} session_ok: {_e(e.session_ok)}</p>
{extra}{err}
<table><thead><tr><th>Code</th><th>Status</th><th>Source</th><th>Description</th></tr></thead>
<tbody>{rows}</tbody></table>
</article>""")
    return "<section><h2>ECUs</h2>" + "".join(parts) + "</section>"


def _warnings_section(warnings) -> str:
    items = "".join(f"<li>{_e(w)}</li>" for w in warnings)
    return f"<section><h2>Warnings</h2><ul>{items}</ul></section>"


def _svg_for_column(name, xs, ys, width=600, height=150) -> str:
    if not ys:
        return ""
    ymin, ymax = min(ys), max(ys)
    span = (ymax - ymin) or 1.0
    xmin, xmax = min(xs), max(xs)
    xspan = (xmax - xmin) or 1.0
    points = []
    for x, y in zip(xs, ys):
        px = ((x - xmin) / xspan) * (width - 20) + 10
        py = height - 10 - ((y - ymin) / span) * (height - 20)
        points.append(f"{px:.1f},{py:.1f}")
    polyline = " ".join(points)
    return (f'<figure><figcaption>{_e(name)}</figcaption>'
           f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
           f'<polyline fill="none" stroke="black" points="{polyline}"/></svg></figure>')


def _log_section(log_path) -> str:
    with open(log_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return ""
    fieldnames = reader.fieldnames or []
    numeric_cols = [c for c in fieldnames if c not in ("timestamp_utc", "elapsed_s")]
    figures = []
    for col in numeric_cols:
        try:
            xs = [float(r["elapsed_s"]) for r in rows]
            ys = [float(r[col]) for r in rows if r[col] != ""]
            xs = xs[:len(ys)]
        except (ValueError, KeyError):
            continue
        if ys:
            figures.append(_svg_for_column(col, xs, ys))
    return "<section><h2>Logged data</h2>" + "".join(figures) + "</section>" if figures else ""


_STYLE = """
body { font-family: sans-serif; margin: 1.5em; }
table { border-collapse: collapse; margin-bottom: 1em; }
th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: left; }
.error { color: #b00; }
"""


def render_html(scan, log_path=None, *, show_vin=False, descriptions=None) -> str:
    adapter = scan.adapter or {}
    log_html = _log_section(log_path) if log_path else ""
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Renault Scenic diagnostic report</title>
<style>{_STYLE}</style>
</head>
<body>
<h1>Renault Scenic diagnostic report</h1>
<p>Created: {_e(scan.created_utc)} — tool version: {_e(scan.tool_version)}</p>
<section><h2>Adapter</h2><p>version: {_e(adapter.get('version'))} voltage: {_e(adapter.get('voltage_v'))}</p></section>
{_generic_section(scan.generic, show_vin, descriptions)}
{_ecu_section(scan.ecus, descriptions)}
{log_html}
{_warnings_section(scan.warnings)}
</body>
</html>"""
    return body
