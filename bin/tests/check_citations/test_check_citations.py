#!/usr/bin/env python3
"""Test check_citations.py against citations_manuscript.tex.

The fixture is typeset twice, numbering every line and every 5th line, and
both builds must give the same flags at the same manuscript line numbers.
Needs pdflatex. Run: python3 ~/bin/tests/check_citations/test_check_citations.py
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent))     # ~/bin
import check_citations as cc  # noqa: E402

TEX = (HERE / "citations_manuscript.tex").read_text()


def build(tex, workdir, name):
    (workdir / f"{name}.tex").write_text(tex)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                   cwd=workdir, check=True, capture_output=True)
    return workdir / f"{name}.pdf"


@unittest.skipUnless(shutil.which("pdflatex"), "needs pdflatex")
class TestFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.pdfs = {
            "every line": build(TEX, d, "every"),
            "every 5th line": build(TEX.replace(r"\linenumbers", r"\linenumbers\modulolinenumbers[5]"),
                                    d, "mod5"),
        }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, pdf):
        source, cites, refs, issues = cc.run(pdf)
        self.assertIn("line-numbered", source)
        flagged = {k: {(c.lineno, c.label()) for c, _ in v} for k, v in issues.items()}
        self.assertEqual(flagged["missing"], {
            (4, "Malkus and Riehl 1958"),    # authors in the wrong order
            (6, "Houze 1989"),               # no such reference
            (71, "Rutledge 1991"),           # cited in a figure caption only
        })
        self.assertEqual(flagged["suffix"], {(9, "Feng et al. 2021")})
        self.assertEqual(flagged["authors"], {(10, "Yuan et al. 2010")})
        self.assertEqual(flagged["spelling"], {
            (12, "García-Pérez and Smith 2019"),  # reference has "García Pérez"
            (12, "Hagos et al. 2013"),           # reference has "Hagoss"
        })
        # The reversed citation points at the right reference.
        reversed_ = next(msg for c, msg in issues["missing"] if c.first == "Malkus")
        self.assertIn("Riehl, H., and J. S. Malkus", reversed_)

        uncited = {r.first for r in refs if r.year and not r.cited}
        self.assertEqual(uncited, {"Elsaesser", "Mapes", "Riehl"})
        self.assertFalse([r for r in refs if not r.year], "unparsed references")
        # Repeat-author dashes resolve to the entry above.
        houze2018 = next(r for r in refs if r.year == "2018")
        self.assertEqual(houze2018.surnames, ["Houze"])
        sh2006 = next(r for r in refs if r.year == "2006")
        self.assertEqual(sh2006.surnames, ["Schumacher", "Houze"])
        # Acknowledgments contract number, dates and section numbers are not citations.
        labels = {c.label() for c in cites}
        self.assertFalse(any("DE" in l or "January" in l or "March" in l for l in labels), labels)

    def test_every_line(self):
        self.check(self.pdfs["every line"])

    def test_every_5th_line(self):
        self.check(self.pdfs["every 5th line"])


class TestUnicode(unittest.TestCase):
    """Accents as Word-made PDFs often extract: decomposed, or as a separate
    spacing mark with a stray space ("N´ un˜ez")."""

    def run_text(self, body, refs):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.txt"
            path.write_text("\n".join(body + ["References"] + refs) + "\n")
            return cc.run(path)

    def test_mangled_accents_still_match(self):
        _, cites, refs, issues = self.run_text(
            ["Waves (Mun\u0303oz-Garci\u0301a and Smith 2019) and",
             "Mun\u02dcoz-Garc\u00b4 ia and Smith (2019) and Volont\u00b4e et al. (2022)."],
            ["Mu\u00f1oz-Garc\u00eda, L., and J. Smith, 2019: Title. J. Climate, 32, 1-20.",
             "Volont\u00e9, A., A. J. Turner, and R. Schiemann, 2022: Title. QJRMS, 148, 1-2."])
        self.assertEqual(len(cites), 3)
        self.assertFalse(issues["missing"] or issues["spelling"], issues)
        self.assertTrue(all(r.cited for r in refs))

    def test_near_miss_is_reported_not_hidden(self):
        _, _, refs, issues = self.run_text(
            ["As in Liu et al. (2021)."],
            ["Lin, Y., A. Author, and B. Author, 2021: Title. J. Climate, 1, 1-2."])
        self.assertFalse(issues["missing"])
        (c, msg), = issues["spelling"]
        self.assertIn("typo, or a different paper", msg)


if __name__ == "__main__":
    unittest.main()
