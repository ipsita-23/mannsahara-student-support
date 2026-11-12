"""Extract PDF checks and render every page into ignored review artifacts."""

import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
PDF = ROOT / "mannsahara-project-guide.pdf"
OUT = ROOT / "tmp" / "review"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(PDF)
    texts = [page.extract_text() for page in reader.pages]
    text = "\n".join(texts)
    required = ["problem", "solution", "viva", "SAFE_FALLBACK", "Chatbot",
                "0774d26", "context-fix-personal-life-001", "independent"]
    missing = [phrase for phrase in required if phrase.lower() not in text.lower()]
    assert not missing, f"Missing required coverage: {missing}"
    assert all(len(page.strip()) > 80 for page in texts), "Unexpected empty page"
    assert "\u25a0" not in text, "Possible unsupported glyph"
    (OUT / "extracted.txt").write_text(text)
    pdf = pdfium.PdfDocument(PDF)
    thumbs = []
    for index in range(len(pdf)):
        page = pdf[index]
        bitmap = page.render(scale=1.4)
        image = bitmap.to_pil().convert("RGB")
        image.save(OUT / f"page-{index + 1:02}.png")
        image.thumbnail((280, 396))
        tile = Image.new("RGB", (300, 426), "#e8eeee")
        tile.paste(image, ((300-image.width)//2, 6))
        ImageDraw.Draw(tile).text((12, 408), f"Page {index + 1}", fill="black")
        thumbs.append(tile)
        page.close()
    for first in range(0, len(thumbs), 12):
        batch = thumbs[first:first+12]
        sheet = Image.new("RGB", (1200, 426*((len(batch)+3)//4)), "white")
        for i, tile in enumerate(batch):
            sheet.paste(tile, ((i % 4)*300, (i//4)*426))
        sheet.save(OUT / f"contact-{first//12+1}.png")
    result = {"pages": len(reader.pages), "bytes": PDF.stat().st_size,
              "text_characters": len(text), "required_coverage": required,
              "pdf_outline_entries": len(reader.outline), "rendered_pages": len(thumbs)}
    (OUT / "checks.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
