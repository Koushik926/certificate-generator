"""Certificate template renderer using ReportLab.

Renders a professional A4-landscape certificate with:
- Decorative border and accent bar
- Event name + recipient name
- Certificate ID + issue date
- Optional template style variant (modern/classic)
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from app.config import settings

STYLE_ACCENT = {
    "modern": colors.HexColor("#1a56db"),   # blue
    "classic": colors.HexColor("#8b4513"),   # saddle brown
}

STYLE_BORDER = {
    "modern": 4,
    "classic": 8,
}


def _draw_border(c: rl_canvas.Canvas, w: float, h: float, style: str) -> None:
    """Draw a double-line border with corner embellishments."""
    margin = 20 * mm
    thick = STYLE_BORDER.get(style, 4)
    accent = STYLE_ACCENT.get(style, colors.black)

    c.setStrokeColor(accent)
    c.setLineWidth(thick)
    c.rect(margin, margin, w - 2 * margin, h - 2 * margin)

    inner = margin + 6 * mm
    c.setLineWidth(1)
    c.rect(inner, inner, w - 2 * inner, h - 2 * inner)


def _draw_header(c: rl_canvas.Canvas, w: float, event_name: str, style: str) -> None:
    """Draw the header band and event name."""
    accent = STYLE_ACCENT.get(style, colors.black)
    header_y = w * 0.82

    # Accent bar
    c.setFillColor(accent)
    c.rect(30 * mm, header_y, w - 60 * mm, 3 * mm, fill=1, stroke=0)

    # Event label
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, header_y + 10 * mm, "CERTIFICATE OF COMPLETION")

    # Event name
    c.setFillColor(colors.HexColor("#1f2937"))
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, header_y - 2 * mm, f"Event: {event_name}")


def _draw_body(c: rl_canvas.Canvas, w: float, recipient_name: str, style: str) -> None:
    """Draw the recipient name and decorative line."""
    accent = STYLE_ACCENT.get(style, colors.black)
    body_y = w * 0.55

    # Decorative line
    c.setStrokeColor(accent)
    c.setLineWidth(1)
    line_w = 120 * mm
    c.line(
        (w - line_w) / 2, body_y + 8 * mm,
        (w + line_w) / 2, body_y + 8 * mm,
    )

    # Recipient name
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(w / 2, body_y - 2 * mm, recipient_name)

    # Subtext
    c.setFillColor(colors.HexColor("#6b7280"))
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(w / 2, body_y - 14 * mm, "Has successfully completed the program")


def _draw_footer(c: rl_canvas.Canvas, w: float, cert_id: str, issue_date: str, style: str) -> None:
    """Draw certificate ID and issue date."""
    accent = STYLE_ACCENT.get(style, colors.black)
    footer_y = 28 * mm

    c.setFillColor(colors.HexColor("#6b7280"))
    c.setFont("Helvetica", 8)
    c.drawString(30 * mm, footer_y, f"ID: {cert_id}")
    c.drawRightString(w - 30 * mm, footer_y, f"Issued: {issue_date}")

    # Small logo placeholder
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(w / 2, footer_y, "AEREO")


def generate_certificate(
    recipient_name: str,
    job_id: str,
    cert_id: str,
    issue_date: str,
    event_name: str,
    template_style: str = "modern",
    output_dir: str = "./generated_certs",
) -> str:
    """Generate a certificate PDF and return its file path."""
    os.makedirs(output_dir, exist_ok=True)

    width, height = A4  # 595 x 842 pt
    # A4 landscape
    if width < height:
        width, height = height, width

    safe_name = "".join(c if c.isalnum() else "_" for c in recipient_name)[:50]
    filename = f"{safe_name}_{cert_id}.pdf"
    path = Path(output_dir) / filename

    c = rl_canvas.Canvas(str(path), pagesize=(width, height))

    _draw_border(c, width, height, template_style)
    _draw_header(c, width, event_name, template_style)
    _draw_body(c, width, recipient_name, template_style)
    _draw_footer(c, width, cert_id, issue_date, template_style)

    c.showPage()
    c.save()

    return str(path)