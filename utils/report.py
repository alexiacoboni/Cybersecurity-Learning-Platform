from __future__ import annotations

from datetime import datetime


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(title: str, lines: list[str]) -> bytes:
    text_lines = [title, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    text_lines.extend(lines)
    commands = ["BT", "/F1 12 Tf", "50 780 Td", "16 TL"]
    for line in text_lines:
        commands.append(f"({_pdf_escape(line[:95])}) Tj")
        commands.append("T*")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in pdf))
        pdf.append(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_offset = sum(len(part) for part in pdf)
    pdf.append(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.append(f"{offset:010d} 00000 n \n".encode())
    pdf.append(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    )
    return b"".join(pdf)
