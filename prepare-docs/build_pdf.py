"""Build the study guide locally without modifying the application or its dependencies."""

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "mannsahara-project-guide.pdf"
INK = colors.HexColor("#183641")
TEAL = colors.HexColor("#147D79")
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("GuideTitle", fontName="Helvetica-Bold", fontSize=35,
                          leading=40, textColor=INK, spaceAfter=22))
STYLES.add(ParagraphStyle("GuideSubtitle", fontSize=15, leading=22,
                          textColor=TEAL, spaceAfter=18))
STYLES.add(ParagraphStyle("GuideBody", fontSize=10, leading=13.3,
                          textColor=INK, spaceAfter=5, splitLongWords=True))
STYLES.add(ParagraphStyle("GuideH1", fontName="Helvetica-Bold", fontSize=23,
                          leading=28, textColor=TEAL, spaceAfter=17, keepWithNext=True))
STYLES.add(ParagraphStyle("GuideH2", fontName="Helvetica-Bold", fontSize=13,
                          leading=18, textColor=INK, spaceBefore=12,
                          spaceAfter=7, keepWithNext=True))
STYLES.add(ParagraphStyle("GuideH3", parent=STYLES["GuideH2"], fontSize=11,
                          leading=16, spaceBefore=9))
STYLES.add(ParagraphStyle("GuideBullet", parent=STYLES["GuideBody"],
                          leftIndent=12, firstLineIndent=-9))
STYLES.add(ParagraphStyle("GuideCode", fontName="Courier", fontSize=8,
                          leading=11, backColor=colors.HexColor("#F0F5F5"),
                          borderPadding=9, spaceBefore=5, spaceAfter=10))


def inline(text):
    text = text.translate(str.maketrans({"\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": " - ",
        "\u2192": " -> ", "\u2265": ">=", "\u2264": "<=", "\u2011": "-",
        "\u2248": "approx. ", "\u2260": "!=", "\u00d7": "x", "\u2010": "-"}))
    text = escape(text)
    codes = []

    def save_code(match):
        codes.append(match.group(1))
        return f"@@CODE{len(codes)-1}@@"

    text = re.sub(r"`([^`]+)`", save_code, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    for index, code in enumerate(codes):
        text = text.replace(f"@@CODE{index}@@", f'<font name="Courier" size="9">{code}</font>')
    return text


class Guide(BaseDocTemplate):
    def __init__(self):
        super().__init__(str(OUTPUT), pagesize=A4, leftMargin=21*mm,
                         rightMargin=21*mm, topMargin=23*mm, bottomMargin=22*mm,
                         title="MannSahara - Project understanding and viva guide",
                         author="MannSahara project documentation")
        self.addPageTemplates(PageTemplate("guide", [Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
            onPage=self.decorate))

    def decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setFillColor(TEAL)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(21*mm, A4[1]-14*mm, "MANNSAHARA / PROJECT PREPARATION")
            canvas.setStrokeColor(colors.HexColor("#D7E5E5"))
            canvas.line(21*mm, A4[1]-17*mm, A4[0]-21*mm, A4[1]-17*mm)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(21*mm, 12*mm, "Synthetic-only academic prototype | Source: 0774d26")
        canvas.drawRightString(A4[0]-21*mm, 12*mm, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "GuideH1":
            title = flowable.getPlainText()
            key = "chapter-" + str(self.seq.nextf("chapter"))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)
            self.notify("TOCEntry", (0, title, self.page, key))


def markdown(path):
    story, paragraph, code = [], [], None

    def flush():
        if paragraph:
            story.append(Paragraph(inline(" ".join(paragraph)), STYLES["GuideBody"]))
            paragraph.clear()

    for line in path.read_text().splitlines():
        if line.startswith("```"):
            flush()
            if code is None:
                code = []
            else:
                story.append(Preformatted("\n".join(code), STYLES["GuideCode"],
                                          maxLineLength=88))
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if line.startswith("# "):
            flush()
            story.extend([CondPageBreak(185*mm), Spacer(1, 5*mm),
                          Paragraph(inline(line[2:]), STYLES["GuideH1"])])
        elif line.startswith("## ") or line.startswith("### "):
            flush()
            level = 3 if line.startswith("### ") else 2
            story.append(Paragraph(inline(line[level+1:]), STYLES[f"GuideH{level}"]))
        elif re.match(r"^\s*(?:[-*]|\d+\.)\s", line):
            flush()
            story.append(Paragraph(inline(line.strip()), STYLES["GuideBullet"]))
        elif not line.strip() or line.strip() == "---":
            flush()
        else:
            paragraph.append(line.strip())
    flush()
    if code is not None:
        raise ValueError(f"Unclosed code block in {path}")
    return story


def main():
    story = [Spacer(1, 23*mm), Paragraph("MannSahara", STYLES["GuideTitle"]),
        Paragraph("Understand the project.<br/>Explain the code.<br/>Prepare for the viva.",
                  STYLES["GuideSubtitle"]), Spacer(1, 12*mm),
        Paragraph("CSE473 CA1 | Group 09 | SIH25092", STYLES["GuideH2"]),
        Paragraph("Ipsita Umang (12309971)<br/>Annamneendi Suresh Kumar (12317960)",
                  STYLES["GuideBody"]), Spacer(1, 12*mm),
        Paragraph("Study edition | 12 November 2026", STYLES["GuideBody"]),
        Paragraph("Based on application source commit 0774d26. Read the problem and solution first, "
                  "then trace the code and practise the viva answers aloud. All demonstration "
                  "scenarios must be invented. This project is a local academic prototype; "
                  "it is not a clinical or emergency service.", STYLES["GuideBody"]),
        PageBreak(), Paragraph("Reading map", STYLES["GuideH2"]),
        Paragraph("The contents are clickable. Chapter references name repository paths relative "
                  "to the project root. The editable Markdown files beside this PDF are its source. "
                  "Historical and current evidence are identified separately.", STYLES["GuideBody"])]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("Contents", fontName="Helvetica", fontSize=9,
        leading=11, textColor=INK, spaceBefore=0, rightIndent=20, alignment=TA_LEFT)]
    story.append(toc)
    for name in ("01-project-and-code.md", "02-viva-and-demo.md", "03-evidence-and-references.md"):
        story.extend(markdown(ROOT / name))
    Guide().multiBuild(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
