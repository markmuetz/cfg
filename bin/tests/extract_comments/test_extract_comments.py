#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Test extract-comments on an annotated, line-numbered LaTeX fixture.

Reuses analyse-citations' fixture manuscript, typeset with every line, every
5th line and no lines numbered; annotates it with PyMuPDF; checks that each
comment is found with its text, reply and manuscript line numbers, and that
only strike-outs, insertions and short marks (up to five words) quote text.
Needs pdflatex. Run: ~/bin/tests/extract_comments/test_extract_comments.py
"""
import importlib.machinery
import importlib.util
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

    note = p1.add_text_annot(p1.search_for("Houze (1989, 2018)")[0].tl, "M: Is 1989 in the list?\nSecond line.")
    note.set_info(title="Referee 1")
    note.update()

    # One strike-out across two lines: its quads sit on different lines.
    a, b = p1.search_for("Cold pools organise"), p1.search_for("(hereafter RCEMIP)")
    s = p1.add_strikeout_annot(quads=[pymupdf.Rect(a[0]).quad, pymupdf.Rect(b[0]).quad])
    s.set_info(content="t: Rephrase.", title="Referee 1")
    s.update()

    # An insertion mark: its text is what it inserts.
    r = p1.search_for("Land and ocean differ")[0]
    ins = p1.add_caret_annot(pymupdf.Point(r.x0, (r.y0 + r.y1) / 2))
    ins.set_info(content="t: The")
    ins.update()

    # Acrobat's "Replace text": a strike-out, and an insertion replying to it.
    old = p1.search_for("future changes")[0]
    rs = p1.add_strikeout_annot(old)
    rs.set_info(title="Referee 1")
    rs.update()
    ri = p1.add_caret_annot(pymupdf.Point(old.x1, (old.y0 + old.y1) / 2))
    ri.set_info(content="t: projected changes", title="Referee 1")
    ri.set_irt_xref(rs.xref)
    ri.update()

    bare = p1.add_highlight_annot(p1.search_for("Elsaesser et al. (2022)")[0])
    bare.update()

    # A highlight across a hyphenated line break: "cita-" / "tion.".
    c1, c2 = p1.search_for("is not a cita-")[0], p1.search_for("tion. As C13")[0]
    hy = p1.add_highlight_annot(quads=[c1.quad, pymupdf.Rect(c2.x0, c2.y0, c2.x0 + 18, c2.y1).quad])
    hy.set_info(content="Hyphenated.")
    hy.update()

    # A long highlight (eight words): located, not quoted.
    lh = p1.add_highlight_annot(p1.search_for("10 km grid spacing is used in all simulations")[0])
    lh.set_info(content="Which model?")
    lh.update()

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
    """'- **L6** Highlight — *Referee 1, …*' -> ('L6', 'Highlight', 'Referee 1')."""
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
        for phrase in ("Zipser (1977)", "Houze (1989, 2018)", "Land and ocean differ", "future changes", "Cold pools organise",
                       "(hereafter RCEMIP)", "Elsaesser et al. (2022)", "10 km grid spacing", "Mapes, B. E."):
            line = next(l for l in layout.split("\n") if phrase in l)
            cls.at[phrase] = int(line.split()[0])
        for name in BUILDS:
            annotate(d / f"{name}.pdf")
            cls.md[name] = run(d / f"{name}.pdf")
        cls.md["every-skip"] = run(d / "every.pdf", "--skip-bare")
        cls.md["every-drawings"] = run(d / "every.pdf", "--drawings")
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([str(TOOL), str(d / "every.pdf"), "-o", out, "--review"],
                           check=True, capture_output=True)
            cls.review = (Path(out) / "every_review.md").read_text()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def expected(self):
        at = self.at
        return [
            ("p1", "Note", ""),                                   # top margin: no line
            (f"L{at['Zipser (1977)']}", "Highlight", "Referee 1"),
            (f"L{at['Houze (1989, 2018)']}", "Note", "Referee 1"),
            (f"L{at['Land and ocean differ']}", "Insert", ""),
            (f"L{at['Elsaesser et al. (2022)']}", "Highlight", ""),
            (f"L{at['future changes']}", "Strike-out", "Referee 1"),
            (f"L{at['10 km grid spacing']}", "Highlight", ""),
            (f"L{at['Cold pools organise']}–{at['(hereafter RCEMIP)']}", "Strike-out", "Referee 1"),
            (f"L{at['(hereafter RCEMIP)']}–{at['(hereafter RCEMIP)'] + 1}", "Highlight", ""),
            (f"L{at['Mapes, B. E.']}", "Text box", ""),
        ]

    def test_every_line(self):
        self.assertEqual(comment_lines(self.md["every"]), self.expected())

    def test_every_5th_line_interpolated(self):
        self.assertEqual(comment_lines(self.md["mod5"]), self.expected())

    def test_text_quote_and_reply(self):
        md = self.md["every"]
        self.assertIn("  > Zipser (1977)\n  Check the year.\n  - Reply — *Author", md)
        self.assertIn("  > is not a citation\n  Hyphenated.", md)   # short: quoted
        self.assertIn("  > Elsaesser et al. (2022)\n", md)
        self.assertIn("    Checked: fine.", md)
        self.assertIn("  M: Is 1989 in the list?\n  Second line.", md)
        # Strike-outs: '"old" → new', the tag in front; a Replace-text pair is one item.
        self.assertIn('  t: "Cold pools organise (hereafter RCEMIP)" \u2192 Rephrase.', md)
        self.assertIn('  t: "future changes" \u2192 projected changes', md)
        self.assertNotIn("- Insert", md.split("future changes")[1].split("\n\n")[0])
        self.assertIn("  > t: The", md)                                 # insertion: quoted
        self.assertIn("10 comments and 1 reply", md)
        self.assertEqual(md.count("- Reply"), 1)            # nested, not listed twice
        # No other manuscript text: not what highlights mark, nor what notes sit beside.
        for text in ("grid spacing", "Mapes, B. E.", "near:", "Houze (1989"):
            self.assertNotIn(text, md)

    def test_no_line_numbers(self):
        md = self.md["plain"]
        self.assertIn("Located by page (the PDF has no line numbers)", md)
        self.assertEqual({w for w, _, _ in comment_lines(md)}, {"p1", "p3"})

    def test_drawings_only_on_request(self):
        self.assertNotIn("Drawing", self.md["every"])
        self.assertIn("Drawing", self.md["every-drawings"])

    def test_review(self):
        rv, at = self.review, self.at
        sections = re.split(r"^## ", rv, flags=re.M)
        get = lambda title: next(x for x in sections if x.startswith(title))
        major, minor, tech = get("Major comments"), get("Minor comments"), get("Technical corrections")
        self.assertIn(f"1. L{at['Houze (1989, 2018)']}: Is 1989 in the list?\n   Second line.", major)
        self.assertIn(f'2. L{at["future changes"]}: "future changes" \u2192 projected changes', tech)
        self.assertIn(f"3. L{at['Cold pools organise']}–{at['(hereafter RCEMIP)']}: "
                      '"Cold pools organise (hereafter RCEMIP)" \u2192 Rephrase.', tech)
        # Untagged comments are minor, in document order; replies follow their item.
        self.assertIn(f'1. L{at["Land and ocean differ"]}: insert "The"', tech)
        self.assertEqual(re.findall(r"^\d+\. (\S+): (.*)$", minor, re.M), [
            ("p1", "A general comment in the top margin."),
            (f"L{at['Zipser (1977)']}", '"Zipser (1977)" Check the year.'),
            (f"L{at['10 km grid spacing']}", "Which model?"),
            (f"L{at['(hereafter RCEMIP)']}–{at['(hereafter RCEMIP)'] + 1}",
             '"is not a citation" Hyphenated.'),
            (f"L{at['Mapes, B. E.']}", "Never cited?"),
        ])
        self.assertIn("   - Reply (Author): Checked: fine.", minor)
        self.assertIn(f'- L{at["Elsaesser et al. (2022)"]}: highlight "Elsaesser et al. (2022)"',
                      get("Marks without"))
        # Long marks and nearby text are not quoted.
        for text in ("grid spacing", "near:", "described by"):
            self.assertNotIn(text, rv)

    def test_skip_bare(self):
        md = self.md["every-skip"]
        self.assertEqual(len(comment_lines(md)), len(self.expected()) - 1)   # the bare highlight is gone
        self.assertIn("Check the year.", md)               # one with a comment stays


class TestShiftedColumn(unittest.TestCase):
    """Line numbers whose margin column moves between pages are all found."""

    def test_column_per_page(self):
        spec = importlib.util.spec_from_loader("ec", importlib.machinery.SourceFileLoader("ec", str(TOOL)))
        ec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ec)
        doc = pymupdf.open()
        n = 1
        for right_edge in (60, 75, 60):          # page 2's numbers sit 15 pt further right
            page = doc.new_page()
            for i in range(20):
                y = 100 + 20 * i
                label = str(n)
                width = pymupdf.get_text_length(label, fontsize=9)
                page.insert_text((right_edge - width, y), label, fontsize=9)
                page.insert_text((100, y), "Body text on this line.", fontsize=9)
                n += 1
        debug = []
        pages = ec.margin_numbers(doc, debug)
        self.assertEqual(sorted(pages), [1, 2, 3], debug)
        self.assertEqual([len(v) for v in pages.values()], [20, 20, 20])
        self.assertEqual(ec.line_at(pages[2], 100 + 20 * 5), 26)


if __name__ == "__main__":
    unittest.main()
