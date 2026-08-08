from datetime import date


def _normalize(value: object) -> str:
    """Normalize text for PDF rendering."""
    text = str(value)
    replacements = {
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "₹": "Rs ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _pdf_string(value: object) -> str:
    normalized = _normalize(value)
    safe = normalized.encode("ascii", "replace").decode("ascii")
    safe = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return f"({safe})"


def create_solar_plan_pdf(plan) -> bytes:
    """Create a compact, dependency-free Liora solar-plan PDF."""
    lines = []

    def rect(x, y, width, height, color):
        lines.append(f"{color} rg {x} {y} {width} {height} re f")

    def text(x, y, size, value, color="0.90 0.96 0.96"):
        lines.append(f"BT /F1 {size} Tf {color} rg 1 0 0 1 {x} {y} Tm {_pdf_string(value)} Tj ET")

    def wrap_text(value, max_chars=28):
        words = str(value).split()
        if not words:
            return [""]

        wrapped = []
        line = words[0]

        for word in words[1:]:
            if len(line) + 1 + len(word) <= max_chars:
                line += " " + word
            else:
                wrapped.append(line)
                line = word

        wrapped.append(line)
        return wrapped

    def text_block(x, y, size, value, max_chars=28, color="0.90 0.96 0.96"):
        wrapped = wrap_text(value, max_chars)
        for index, line in enumerate(wrapped):
            text(x, y - index * (size + 2), size, line, color)
        return len(wrapped)

    # A4 page (595 x 842 points), using Liora's dark solar palette.
    rect(0, 0, 595, 842, "0.008 0.071 0.086")
    rect(0, 754, 595, 88, "0.043 0.059 0.071")
    rect(42, 687, 511, 48, "0.035 0.151 0.126")
    text(43, 800, 25, "LIORA", "0.0 1.0 0.78")
    text(43, 779, 10, "AI Powered. Human Inspired.", "0.44 0.85 0.77")
    text(350, 796, 11, "YOUR SOLAR PLAN", "0.0 0.80 1.0")
    text(350, 778, 9, f"Prepared {date.today().isoformat()}", "0.55 0.68 0.70")
    text(58, 710, 17, "Your personalised solar recommendation", "0.65 1.0 0.90")
    text(58, 693, 10, f"Designed for: {plan.city or 'Your home'}", "0.76 0.91 0.88")

    # Key result cards.
    card_y = 602
    for x in (42, 217, 392):
        rect(x, card_y, 161, 65, "0.043 0.11 0.12")
    text(57, 643, 9, "DAILY ENERGY NEED", "0.39 0.81 0.73")
    text(57, 618, 21, f"{plan.daily_kwh:.1f} kWh", "0.65 1.0 0.90")
    text(232, 643, 9, "RECOMMENDED SYSTEM", "0.39 0.81 0.73")
    text(232, 618, 21, f"{plan.system_kw:.1f} kW", "0.0 0.80 1.0")
    text(407, 643, 9, "ESTIMATED PAYBACK", "0.39 0.81 0.73")
    text(407, 618, 21, plan.payback, "1.0 0.87 0.35")

    text(42, 558, 15, "System at a glance", "0.0 1.0 0.78")
    left = [("Solar panels", plan.panel_type), ("Inverter", plan.inverter), ("Mounting", plan.mounting), ("Battery", plan.battery), ("Available roof area", f"{plan.roof_area:.0f} sq ft")]
    right = [("Daily generation", plan.daily_generation), ("Monthly generation", plan.monthly_generation), ("Monthly saving", plan.monthly_saving), ("Estimated installed cost", plan.installed_cost), ("Recommended system", f"{plan.system_kw:.1f} kW")]
    y = 529
    for label, value in left:
        text(48, y, 9, label, "0.47 0.66 0.67")
        row_lines = text_block(170, y, 10, value, max_chars=22, color="0.90 0.96 0.96")
        lines.append(f"0.0 0.8 0.65 RG 48 {y - 9} m 270 {y - 9} l S")
        y -= max(35, row_lines * 12 + 22)
    y = 529
    for label, value in right:
        text(316, y, 9, label, "0.47 0.66 0.67")
        row_lines = text_block(447, y, 10, value, max_chars=22, color="0.90 0.96 0.96")
        lines.append(f"0.0 0.8 0.65 RG 316 {y - 9} m 547 {y - 9} l S")
        y -= max(35, row_lines * 12 + 22)

    rect(42, 276, 511, 115, "0.032 0.125 0.101")
    text(58, 363, 15, "What this means for you", "0.65 1.0 0.90")
    text(58, 340, 10, "Your system is sized to cover a large part of your household's daytime energy use.")
    text(58, 320, 10, "A final site survey will confirm roof shade, structure and your exact local tariff.")
    text(58, 300, 10, "Liora recommends comparing final installer quotes before making a purchase decision.")

    text(42, 234, 15, "Next steps", "0.0 1.0 0.78")
    steps = ["1. Check that your roof has enough shade-free space.", "2. Request a site survey from a qualified solar installer.", "3. Compare warranty, generation and installation proposals."]
    y = 208
    for step in steps:
        text(52, y, 10, step, "0.82 0.92 0.91")
        y -= 21
    text(42, 68, 9, "LIORA SOLAR CALCULATOR  |  This plan is an estimate for guidance only.", "0.39 0.64 0.65")
    text(42, 50, 9, "A brighter, greener tomorrow starts with a clear plan.", "0.0 0.80 1.0")

    content = "\n".join(lines).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)
