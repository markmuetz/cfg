#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Test extract-comments on an annotated, line-numbered LaTeX fixture.

Reuses analyse-citations' fixture manuscript, typeset with every line, every
5th line and no lines numbered; annotates it with PyMuPDF; checks that each
comment is found with its text, quote, reply and manuscript line numbers.
Needs pdflatex. Run: ~/bin/tests/extract_comments/test_extract_comments.py
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pymupdf

HERE = Path(__file__).parent
TOOL = HERE.parent.parent / "extract-comments"
TEX = (HERE.parent / "analyse_citations" / "citations_manuscript.tex").read_text()
BUILDS = {
    "every": TEX,
    "mod5": TEX.replace(r"\linenumbers", r"\linenumbers\modulolinenumbers[5]"),
    "plain": TEX.replace(r"\linenumbers", ""),
}


def annotate(pdf):
    """Add known comments; return nothing (the expectations are in the tests)."""
    doc = pymupdf.open(pdf)
    p1 = doc[0]

    h = p1.add_highlight_annot(p1.search_for("Zipser (1977)")[0])
    h.set_info(content="Check the year.", title="Referee 1")
    h.update()
    reply = p1.add_text_annot(h.rect.br, "Checked: fine.")
    reply.set_info(title="Author")
    reply.set_irt_xref(h.xref)
    reply.update()

    note = p1.add_text_annot(p1.search_for("Houze (1989, 2018)")[0].tl, "Is 1989 in the list?\nSecond line.")
    note.set_info(title="Referee 1")
    note.update()

    # One strike-out across two lines: its quads sit on different lines.
    a, b = p1.search_for("Cold pools organise"), p1.search_for("(hereafter RCEMIP)")
    s = p1.add_strikeout_annot(quads=[pymupdf.Rect(a[0]).quad, pymupdf.Rect(b[0]).quad])
    s.set_info(content="Rephrase.", title="Referee 1")
    s.update()

    bare = p1.add_highlight_annot(p1.search_for("Elsaesser et al. (2022)")[0])
    bare.update()

    # A highlight across a hyphenated line break: "cita-" / "tion.".
    c1, c2 = p1.search_for("is not a cita-")[0], p1.search_for("tion. As C13")[0]
    hy = p1.add_highlight_annot(quads=[c1.quad, pymupdf.Rect(c2.x0, c2.y0, c2.x0 + 18, c2.y1).quad])
    hy.set_info(content="Hyphenated.")
    hy.update()

    # Freehand pen strokes (an iPad drawing): left out unless --drawings.
    ink = p1.add_ink_annot([[(400, 300), (420, 305), (440, 300)]])
    ink.update()

    top = p1.add_text_annot((300, 20), "A general comment in the top margin.")
    top.update()

    refs = next(pg for pg in doc if pg.search_for("Mapes, B. E."))
    box = refs.add_freetext_annot(pymupdf.Rect(refs.search_for("Mapes, B. E.")[0]) + (0, 0, 200, 20),
                                  "Never cited?")
    box.update()
    doc.saveIncr()


def run(pdf, *args):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([str(TOOL), str(pdf), "-o", d, *args], check=True, capture_output=True)
        return (Path(d) / f"{pdf.stem}_comments.md").read_text()


def comment_lines(md):
    """'- **l.6** Highlight — *Referee 1, …*' -> ('l.6', 'Highlight', 'Referee 1')."""
    out = []
    for m in re.finditer(r"^- \*\*(\S+)\*\* (.+?)(?: \u2014 \*([^,*]*)[^\n]*)?$", md, re.M):
        out.append((m.group(1), m.group(2), m.group(3) or ""))
    return out


@unittest.skipUnless(shutil.which("pdflatex"), "needs pdflatex")
class TestExtractComments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.md = {}
        for name, tex in BUILDS.items():
            (d / f"{name}.tex").write_text(tex)
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                           cwd=d, check=True, capture_output=True)
        # Where the annotated phrases are, from the fixture's own line numbers,
        # read before annotating (pdftotext would read the text box's text too).
        layout = subprocess.run(["pdftotext", "-layout", str(d / "every.pdf"), "-"],
                                capture_output=True, text=True).stdout
        cls.at = {}
        for phrase in ("Zipser (1977)", "Houze (1989, 2018)", "Cold pools organise",
                       "(hereafter RCEMIP)", "Elsaesser et al. (2022)", "Mapes, B. E."):
            line = next(l for l in layout.split("\n") if phrase in l)
            cls.at[phrase] = int(line.split()[0])
        for name in BUILDS:
            annotate(d / f"{name}.pdf")
            cls.md[name] = run(d / f"{name}.pdf")
        cls.md["every-skip"] = run(d / "every.pdf", "--skip-bare")
        cls.md["every-drawings"] = run(d / "every.pdf", "--drawings")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def expected(self):
        at = self.at
        return [
            ("p.1", "Note", ""),                                   # top margin: no line
            (f"l.{at['Zipser (1977)']}", "Highlight", "Referee 1"),
            (f"l.{at['Houze (1989, 2018)']}", "Note", "Referee 1"),
            (f"l.{at['Elsaesser et al. (2022)']}", "Highlight", ""),
            (f"l.{at['Cold pools organise']}–{at['(hereafter RCEMIP)']}", "Strike-out", "Referee 1"),
            (f"l.{at['(hereafter RCEMIP)']}–{at['(hereafter RCEMIP)'] + 1}", "Highlight", ""),
            (f"l.{at['Mapes, B. E.']}", "Text box", ""),
        ]

    def test_every_line(self):
        self.assertEqual(comment_lines(self.md["every"]), self.expected())

    def test_every_5th_line_interpolated(self):
        self.assertEqual(comment_lines(self.md["mod5"]), self.expected())

    def test_text_quote_and_reply(self):
        md = self.md["every"]
        self.assertIn("  > Zipser (1977)\n  Check the year.\n  - Reply — *Author", md)
        self.assertIn("    Checked: fine.", md)
        self.assertIn("  Is 1989 in the list?\n  Second line.", md)
        self.assertIn("> Cold pools organise (hereafter RCEMIP)", md)
        self.assertIn("7 comments and 1 reply", md)
        self.assertIn("> is not a citation.\n  Hyphenated.", md)
        self.assertEqual(md.count("- Reply"), 1)            # nested, not listed twice

    def test_no_line_numbers(self):
        md = self.md["plain"]
        self.assertIn("Located by page (the PDF has no line numbers)", md)
        self.assertEqual({w for w, _, _ in comment_lines(md)}, {"p.1", "p.3"})

    def test_drawings_only_on_request(self):
        self.assertNotIn("Drawing", self.md["every"])
        self.assertIn("Drawing", self.md["every-drawings"])

    def test_skip_bare(self):
        md = self.md["every-skip"]
        self.assertNotIn("Elsaesser", md)                  # the bare highlight is gone
        self.assertIn("Zipser", md)                        # one with a comment stays


if __name__ == "__main__":
    unittest.main()
