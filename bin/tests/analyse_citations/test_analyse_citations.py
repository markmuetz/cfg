#!/usr/bin/env python3
"""Test analyse_citations.py against citations_manuscript.tex.

The fixture is typeset twice, numbering every line and every 5th line, and
both builds must give the same flags at the same manuscript line numbers.
Needs pdflatex. Run: python3 ~/bin/tests/analyse_citations/test_analyse_citations.py
"""
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent))     # ~/bin
import analyse_citations as ac  # noqa: E402

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
        a = ac.run(pdf)
        cites, refs, issues = a.cites, a.refs, a.issues
        self.assertIn("line-numbered", a.source)
        flagged = {k: {(c.lineno, c.label()) for c, _ in v} for k, v in issues.items()}
        self.assertEqual(flagged["missing"], {
            (4, "Malkus and Riehl 1958"),    # authors in the wrong order
            (6, "Houze 1989"),               # no such reference
            (77, "Rutledge 1991"),           # cited in a figure caption only
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

        # "Cortado (2013, hereafter C13)": two later uses of C13, so three citations.
        (c13,) = a.aliases
        self.assertEqual((c13.alias, len(c13.uses)), ("C13", 2))
        cortado = next(r for r in refs if r.first == "Cortado")
        self.assertEqual(len(cortado.cited), 3)
        self.assertEqual(cortado.key, "cortado2013cold")
        self.assertEqual(a.unlinked, [])     # "(hereafter RCEMIP)" is not a citation
        return a

    def test_outputs(self):
        a = self.check(self.pdfs["every line"])
        with tempfile.TemporaryDirectory() as d:
            ac.write(a, Path(d))
            names = sorted(p.name for p in Path(d).iterdir())
            self.assertEqual(names, ["every_citations.tsv", "every_references.bib", "every_report.md"])
            bib = (Path(d) / "every_references.bib").read_text()
            report = (Path(d) / "every_report.md").read_text()
            tsv = (Path(d) / "every_citations.tsv").read_text()
        self.assertEqual(bib.count("\n@"), len([r for r in a.refs if r.year]))
        riehl = bib[bib.index("@article{riehl1958heat,"):]
        riehl = riehl[:riehl.index("\n}")]
        for field in ("author = {Riehl, H. and Malkus, J. S.}",
                      "title = {On the heat balance in the equatorial trough zone}",
                      "journal = {Geophysica}", "volume = {6}", "pages = {503--538}",
                      "citedcount = {0}"):
            self.assertIn(field, riehl)
        self.assertIn("author = {Feng, Z. and others}", bib)          # "and Coauthors"
        self.assertIn("author = {Houze, Jr., R. A.}", bib)
        self.assertIn("| C13 | Cortado 2013 |", report)
        self.assertIn("| 3 | Cortado 2013 | cortado2013cold |", report)
        self.assertIn("C13 (= Cortado 2013)\tcortado2013cold", tsv)

    def test_library_and_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d)
            def item(key, bib=None):
                (lib / key).mkdir()
                if bib:
                    (lib / key / "ref.bib").write_text(bib)
            nesbitt = ("@article{{{key},\n    title = {{{title}}},\n    author = {{Nesbitt, Stephen W}},\n"
                       "    year = {{2000}},\n    doi = {{10.1175/1520-0442(2000)013<4087:ACOPFI>2.0.CO;2}}\n}}\n")
            title = "A census of precipitation features in the tropics using TRMM"
            item("nesbitt2000census", nesbitt.format(key="nesbitt2000census", title=title))
            item("nesbitt2000censussupplement",       # shares the DOI; must not win
                 nesbitt.format(key="nesbitt2000censussupplement", title="Supplement for: " + title))
            item("houze2004mesoscale")                 # no ref.bib: matched by key
            item("liu2021global", "@article{liu2021global,\n    title = {{Global mesoscale convective "
                 "system latent heating characteristics from GPM retrievals and an MCS tracking "
                 "dataset}},\n    author = {Liu, Nana and Leung, L Ruby and Feng, Zhe},\n"
                 "    year = {2021}\n}\n")               # no DOI: matched by title
            a = ac.run(self.pdfs["every line"], library=lib)
            held = {r.key: r.library for r in a.refs if r.library}
            self.assertEqual(held, {"nesbitt2000census": "nesbitt2000census",
                                    "houze2004mesoscale": "houze2004mesoscale",
                                    "liu2021global": "liu2021global"})
            fetch = [r.key for r in a.to_fetch()]
            self.assertEqual(fetch[0], "cortado2013cold")          # cited 3 times
            self.assertNotIn("houze2004mesoscale", fetch)
            self.assertIn("| Cited references to fetch |", ac.report(a))

            opened = []
            with mock.patch("webbrowser.open", opened.append), \
                    mock.patch("sys.stdout", io.StringIO()) as out:
                ac.open_dois(a, 20)
            # Only Zipser 1977 has a DOI among those to fetch; its old AMS form is rebuilt.
            self.assertEqual(opened, ["https://doi.org/10.1175/1520-0493(1977)105%3C1568:MACSDA%3E2.0.CO;2"])
            self.assertIn("No DOI, search by title: Cortado 2013", out.getvalue())

    def test_every_line(self):
        self.check(self.pdfs["every line"])

    def test_every_5th_line(self):
        self.check(self.pdfs["every 5th line"])


class TestSici(unittest.TestCase):
    def test_mangled_old_ams_dois_are_rebuilt(self):
        self.assertEqual(ac.fix_sici("10.1175/15200450(2004)043,1095:SROLHP.2.0.CO;2"),
                         "10.1175/1520-0450(2004)043<1095:SROLHP>2.0.CO;2")
        self.assertEqual(ac.fix_sici("10.1175/JCLI-D-20-0997.1"), "10.1175/JCLI-D-20-0997.1")


class TestUnicode(unittest.TestCase):
    """Accents as Word-made PDFs often extract: decomposed, or as a separate
    spacing mark with a stray space ("N´ un˜ez")."""

    def run_text(self, body, refs):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.txt"
            path.write_text("\n".join(body + ["References"] + refs) + "\n")
            a = ac.run(path)
            return a.source, a.cites, a.refs, a.issues

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
