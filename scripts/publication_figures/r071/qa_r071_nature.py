"""Validate the Nature-format R071 main-figure exports and build a contact sheet."""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = ROOT / "results" / "figures"
EXPECTED_MM = (183.0, 168.0)
EXPECTED_PX = tuple(round(value / 25.4 * 600) for value in EXPECTED_MM)
STEMS = [
    "r071_figure1_evidence_provenance_atlas",
    "r071_figure2_hybrid_benchmark_residuals",
    "r071_figure3_stress_phase_mechanism_map",
    "r071_figure4_locked_ews_evaluation",
    "r071_figure5_axonal_scenario_map",
    "r071_figure6_disease_axis_hypothesis_map",
]
EXPECTED_PANELS = {
    STEMS[0]: "abcdefghi",
    STEMS[1]: "abcdefghi",
    STEMS[2]: "abcdefghi",
    STEMS[3]: "abcdefghij",
    STEMS[4]: "abcdefghij",
    STEMS[5]: "abcdefghi",
}
EXPECTED_SIZE_MM = {
    STEMS[0]: (183.0, 150.0),
    STEMS[3]: (183.0, 154.0),
    **{stem: EXPECTED_MM for stem in (STEMS[1], STEMS[2], STEMS[5])},
    STEMS[4]: (183.0, 154.0),
}


def edge_ink_fraction(image: Image.Image, width: int = 3) -> float:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, background).convert("L")
    edges = Image.new("L", rgb.size)
    draw = ImageDraw.Draw(edges)
    draw.rectangle((0, 0, rgb.width - 1, width - 1), fill=255)
    draw.rectangle((0, rgb.height - width, rgb.width - 1, rgb.height - 1), fill=255)
    draw.rectangle((0, 0, width - 1, rgb.height - 1), fill=255)
    draw.rectangle((rgb.width - width, 0, rgb.width - 1, rgb.height - 1), fill=255)
    edge_pixels = sum(1 for value in ImageChops.multiply(difference, edges).getdata() if value > 8)
    total_edge_pixels = 2 * width * (rgb.width + rgb.height - 2 * width)
    return edge_pixels / total_edge_pixels


def inspect_figure(stem: str) -> dict:
    paths = {suffix: FIG_DIR / f"{stem}.{suffix}" for suffix in ("png", "pdf", "svg", "tiff")}
    missing = [suffix for suffix, path in paths.items() if not path.exists()]
    if missing:
        return {"stem": stem, "pass": False, "missing": missing}

    with Image.open(paths["png"]) as png:
        png_size = png.size
        png_bbox = ImageChops.difference(png.convert("RGB"), Image.new("RGB", png.size, "white")).getbbox()
        edge_fraction = edge_ink_fraction(png)

    with Image.open(paths["tiff"]) as tiff:
        tiff_size = tiff.size
        compression = tiff.tag_v2.get(259)

    pdf = fitz.open(paths["pdf"])
    page = pdf[0]
    pdf_mm = (page.rect.width / 72 * 25.4, page.rect.height / 72 * 25.4)
    fonts = sorted({font[3] for font in page.get_fonts(full=True)})
    pdf.close()

    root = ET.parse(paths["svg"]).getroot()
    text_values = ["".join(node.itertext()).strip() for node in root.iter() if node.tag.endswith("text")]
    expected_panels = EXPECTED_PANELS[stem]
    expected_mm = EXPECTED_SIZE_MM[stem]
    expected_px = tuple(round(value / 25.4 * 600) for value in expected_mm)
    panel_labels = [letter for letter in expected_panels if letter in text_values]

    dimensions_ok = all(abs(actual - expected) <= 2 for actual, expected in zip(png_size, expected_px))
    pdf_size_ok = all(math.isclose(actual, expected, abs_tol=0.15) for actual, expected in zip(pdf_mm, expected_mm))
    result = {
        "stem": stem,
        "png_px": png_size,
        "tiff_px": tiff_size,
        "pdf_mm": [round(value, 3) for value in pdf_mm],
        "pdf_fonts": fonts,
        "svg_text_nodes": len(text_values),
        "panel_labels": panel_labels,
        "tiff_compression_tag": compression,
        "edge_ink_fraction": round(edge_fraction, 6),
        "nonblank_bbox": png_bbox,
    }
    result["pass"] = all([
        dimensions_ok,
        tiff_size == png_size,
        pdf_size_ok,
        compression == 5,
        png_bbox is not None,
        len(text_values) > 12,
        panel_labels == list(expected_panels),
        bool(fonts),
        edge_fraction < 0.02,
    ])
    return result


def build_contact_sheet() -> Path:
    thumb_size = (1080, 992)
    margin = 32
    title_height = 36
    sheet = Image.new(
        "RGB",
        (2 * thumb_size[0] + 3 * margin, 3 * (thumb_size[1] + title_height) + 4 * margin),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for index, stem in enumerate(STEMS):
        row, column = divmod(index, 2)
        x = margin + column * (thumb_size[0] + margin)
        y = margin + row * (thumb_size[1] + title_height + margin)
        with Image.open(FIG_DIR / f"{stem}.png") as source:
            preview = source.convert("RGB")
            preview.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        draw.text((x, y), f"Figure {index + 1}", fill="black")
        sheet.paste(preview, (x, y + title_height))
    output = FIG_DIR / "r071_nature_main_figures_contact_sheet.png"
    sheet.save(output, dpi=(150, 150))
    return output


def main() -> int:
    results = [inspect_figure(stem) for stem in STEMS]
    contact_sheet = build_contact_sheet()
    report = {
        "status": "pass" if all(result["pass"] for result in results) else "fail",
        "expected_mm": EXPECTED_MM,
        "expected_600dpi_px": EXPECTED_PX,
        "figures": results,
        "contact_sheet": str(contact_sheet.relative_to(ROOT)).replace("\\", "/"),
    }
    report_path = FIG_DIR / "r071_nature_qa.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
