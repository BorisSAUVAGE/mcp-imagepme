"""Extraction du tableau de données d'un export Excel TVA d'ImagePME.

Le fichier contient un titre (cellule E1), puis une ligne "Date" listant les
périodes et, en dessous, une ligne par indicateur (échantillon, ICA, ICAC).
On le restitue sous forme de tableau Markdown, une ligne par période, pour
que Claude ait directement les chiffres sans avoir à ouvrir le fichier.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl


def tableau_tva(path: Path) -> str | None:
    """Renvoie le tableau Markdown du fichier, ou None si la mise en page
    n'est pas celle attendue."""
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]

    header_idx = next((i for i, r in enumerate(rows) if r and r[0] == "Date"), None)
    if header_idx is None:
        return None
    header = rows[header_idx]
    cols = [j for j in range(1, len(header)) if header[j] is not None]

    series = []
    for r in rows[header_idx + 1:]:
        if not r or r[0] is None:
            break
        series.append(r)
    if not cols or not series:
        return None

    title = next((str(v) for r in rows[:header_idx] for v in r if isinstance(v, str) and v.startswith("Données")), "")
    lines = [title.replace("\n", " — "), ""] if title else []
    lines.append("| Période | " + " | ".join(str(s[0]) for s in series) + " |")
    lines.append("|---" * (len(series) + 1) + "|")
    for j in cols:
        values = ["" if j >= len(s) or s[j] is None else str(s[j]) for s in series]
        lines.append(f"| {header[j]} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def _fmt_tdfc(header: str, value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if header.startswith(("Evolution", "Ratio", "Part")):
            return f"{value * 100:.1f} %"
        if header.startswith("BFR"):
            return f"{value:g}"
        return f"{round(value):,}".replace(",", " ")
    return str(value)


def tableau_tdfc(path: Path) -> str | None:
    """Renvoie le tableau Markdown d'un export Excel TDFC (une ligne par
    indicateur, colonnes vides retirées), ou None si la mise en page n'est
    pas celle attendue."""
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).active
    rows = [list(r) for r in ws.iter_rows(values_only=True) if any(v is not None for v in r)]

    header_idx = next((i for i, r in enumerate(rows) if r[0] == "Indicateurs"), None)
    if header_idx is None:
        return None
    header = [str(h) if h is not None else "" for h in rows[header_idx]]

    body = []
    for r in rows[header_idx + 1:]:
        if isinstance(r[0], str) and r[0].startswith("Source"):
            break
        body.append(r)
    cols = [j for j in range(1, len(header)) if any(j < len(r) and r[j] is not None for r in body)]
    if not body or not cols:
        return None

    lines = [str(r[0]) for r in rows[:header_idx] if r[0] and "IMAGEPME" not in str(r[0])]
    lines += ["", "| Indicateur | " + " | ".join(header[j] for j in cols) + " |",
              "|---" * (len(cols) + 1) + "|"]
    for r in body:
        label = str(r[0]).replace("\xa0", " ").strip()
        values = [_fmt_tdfc(header[j], r[j] if j < len(r) else None) for j in cols]
        if not any(values):
            label = f"**{label}**"
        lines.append(f"| {label} | " + " | ".join(values) + " |")
    lines.append("\nMontants en euros. Un indicateur absent ou marqué S est couvert par le secret statistique.")
    return "\n".join(lines)
