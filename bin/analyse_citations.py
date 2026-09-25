#!/usr/bin/env python3
"""Analyse the author-year citations of a PDF against its reference list.

Runs entirely locally (pdftotext + regexes): nothing is sent anywhere, so it is
safe to use on a confidential manuscript or a student's dissertation. For
manuscript.pdf it writes

  manuscript_report.md
      What is wrong, and how often each reference is cited:
        - citations with no matching reference, with near-miss suggestions
          (a misspelt surname, a different year, the cited name being a
          co-author);
        - names spelt differently from the reference (a letter or two out,
          or a hyphen where the reference has a space);
        - citations whose author count or year letter disagrees with the
          reference ("Yuan et al. 2010" against a two-author entry; "Feng et
          al. 2021" when the list has 2021a and 2021b);
        - references never cited, duplicated, or not parsed;
        - abbreviations defined for citations ("Cortado (2013, hereafter
          C13)"), whose later uses count as citations;
        - a table of how many times each reference is cited.
  manuscript_references.bib
      The reference list as BibTeX, keyed <author><year><word>, with the raw
      entry above each one and fields citedcount and citedlines (ignored by
      BibTeX styles). Heuristic: check it before use.
  manuscript_citations.tsv
      Every in-text citation: line, as cited, the matching key.

and prints the report. Line-numbered review manuscripts are detected
automatically and everything is located by manuscript line number. It
understands author-year styles (AMS, AGU, APA, Harvard), not numbered ones. The
parsing is heuristic: treat every flag as "look at this", not as a verdict.

Usage:
    analyse-citations manuscript.pdf                 # writes ./manuscript_*.{md,bib,tsv}
    analyse-citations manuscript.pdf -o review/      # write them in review/ instead
    analyse-citations manuscript.txt                 # text you extracted yourself

    # Which cited papers do I already have? Adds an "In library" column and a
    # "To fetch" list (DOI, else key, else author + year + title similarity).
    analyse-citations manuscript.pdf --library ~/LitManData/literature
    # ... and open the DOIs of the 10 most-cited missing ones in the browser.
    analyse-citations manuscript.pdf --library ~/LitManData/literature --fetch 10

Set ANALYSE_CITATIONS_LIBRARY to make --library the default.

Needs Python 3.8+ and pdftotext (poppler: `brew install poppler`).
Tests: python3 ~/bin/tests/analyse_citations/test_analyse_citations.py (needs pdflatex).

Provenance
----------
Written on 2026-09-25 by Claude (Claude Code, model Claude Opus 5.5) working
with Mark Muetzelfeldt, in a session of his lit-workflow repository.

Why it exists: while refereeing a manuscript, MM found an in-text citation with
no entry in the reference list and wanted to check the rest systematically. The
journal's publisher (AMS) forbids reviewers from using AI tools to evaluate
manuscripts, so the manuscript was never given to Claude. Instead Claude wrote
this deterministic checker, which MM runs and whose report MM reads. Claude
did not see the manuscript, its citations or this tool's output on it. Keep it
that way: no network calls, no AI, nothing leaves the machine.

How it was tested: a line-numbered LaTeX fixture with planted errors, typeset
with every line and every 5th line numbered (tests/analyse_citations/), and a
regression pass over eight published papers from MM's library in AMS, AGU,
Wiley/APA and AMS Early Online Release styles. On those, most remaining flags
were genuine errors in the published papers (a citation to the wrong year, a
misspelt surname, a six-author paper cited as one author).

History: developed in lit-workflow as scripts/check_citations.py; near-miss
matching added after a hyphenated surname in a manuscript's text appeared
unhyphenated in its reference list and was reported as missing; moved to cfg
~/bin as check-citations; renamed analyse-citations the same day when it
gained the written report, the BibTeX list, citation counts and "hereafter"
abbreviations; --library and --fetch added so that the most-cited papers
missing from MM's library can be opened for download without the reference
list ever leaving the machine. Used for reviewing and marking dissertations.
"""
import argparse
import bisect
import difflib
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import quote

PARTICLE = r"(?:(?:[Vv]an|[Vv]on|[Dd]e|[Dd]el|[Dd]er|[Dd]en|[Dd]a|[Dd]i|[Dd]u|[Ll]a|[Ll]e|[Tt]en|[Tt]er|[Dd]os)\s+){0,2}"
SURNAME = PARTICLE + r"[A-Z][\w\u0300-\u036f'’\-]*\w"
# One name, "A and B", "A et al.", or an APA 7 list: "A, B, C, & D" / "A, B, et al.".
AUTHORS = (rf"(?P<first>{SURNAME})(?P<more>(?:\s*,\s*{SURNAME})*)"
           rf"(?:(?P<etal>,?\s+et\s+al\.?)|\s*,?\s*(?:and|&)\s+(?P<last>{SURNAME}))?")
YEAR = r"(?:1[89]\d\d|20\d\d)[a-z]?"
YEARS = rf"{YEAR}(?:\s*,\s*(?:{YEAR}|[a-z](?![\w.])))*"
CITE_RE = re.compile(
    rf"(?<![\w'’\-]){AUTHORS}\s*,?\s*[(\[]?\s*(?:e\.g\.,?\s*)?(?P<years>{YEARS})(?!\w)")

# Abbreviations defined for a citation: "Riehl and Malkus (1958, hereafter
# RM58)", "(hereafter referred to as C13)", "(C13 hereafter)". An abbreviation
# has a digit (C13, RM58) or is all capitals (HM).
ABBREV = r"[A-Z](?:[A-Za-z]*\d+[a-z]?|[A-Z]+)"
HEREAFTER = r"(?:hereafter|hereinafter|henceforth)"
ALIAS_RES = [
    re.compile(rf"\b{HEREAFTER}[,:]?\s+(?:referred\s+to\s+as\s+|called\s+|as\s+)?"
               rf"[\"“‘']?(?P<alias>{ABBREV})(?![\w\-])"),
    re.compile(rf"(?<![\w\-])[\"“‘']?(?P<alias>{ABBREV})[\"”’']?\s+{HEREAFTER}\b"),
]

# Capitalised words that precede a year but are not authors.
STOP = {
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "jan", "feb", "mar", "apr",
    "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "fig", "figs", "figure", "figures", "table", "tables", "section", "sections",
    "sect", "eq", "eqs", "equation", "appendix", "chapter", "part", "phase",
    "version", "in", "from", "since", "until", "during", "between", "and",
    "the", "by", "of", "for", "before", "after", "through", "to", "summer",
    "winter", "spring", "autumn", "fall", "year", "years", "as", "on", "at",
    "cycle", "experiment", "period", "season", "seasons", "early", "late",
    "mid", "circa", "ca", "vol", "no", "pp", "day", "days", "this", "these",
    "however", "here", "we", "our", "all", "both", "each", "over", "within",
    "across", "around", "about", "near", "into", "under", "while", "then",
    # institutional words before a year: "Copyright 2004", "Meteorological Society, 2004"
    "copyright", "society", "union", "university", "press", "journal", "institute",
    "conference", "meeting", "workshop", "report", "precipitation", "accepted",
    "received", "revised", "published", "submitted",
}

REF_HEAD_RE = re.compile(
    r"^\s*(?:[\dIVX]+\.?\s*)?(REFERENCES|References|Bibliography|BIBLIOGRAPHY|"
    r"Literature Cited|LITERATURE CITED|REFERENCES CITED|References Cited)\s*$")
REF_END_RE = re.compile(
    r"^\s*(LIST OF (FIGURES|TABLES)|List of (Figures|Tables)|TABLES?\s*$|"
    r"(TABLE|Table)\s+\d+\.|(FIG|Fig)\.\s*\d+\.|(FIGURE|Figure)\s+\d+\.|"
    r"FIGURE CAPTIONS|Figure Captions|Figure captions)")
DASHES = r"[\u2014\u2013_\-]{2,}"
REF_START_RE = re.compile(
    rf"^\s*(?:{PARTICLE}[A-Z][^\s,.:;()]*(?:[ \-][A-Z][^\s,.:;()]*)*"
    r",\s+(?:[A-Z]\.|(?:1[89]|20)\d\d[a-z]?[:.)])"
    rf"|{DASHES})")
REF_YEAR_RE = re.compile(r"(?:^|[\s(,])((?:1[89]|20)\d\d)([a-z]?)(?=[\s).:,;]|$)")
INITIALS_RE = re.compile(r"^(?:[A-Z]\.-?)+$|^[A-Z]{1,2}$|^[A-Z]\.?-[A-Z]\.?$")
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}
TRUNCATED_RE = re.compile(r",?\s*(?:and\s+)?(?:et al\.?|Coauthors)")
LINENO_RE = re.compile(r"^\s*(\d{1,5})(?=\s{2,}\S|\s*$)")


def norm(name):
    """Fold accents and case, keep letters only: 'Volonté' -> 'volonte'."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())


@dataclass
class Line:
    page: int
    lineno: int      # manuscript line number, 0 if the PDF has none
    text: str


def where(page, lineno):
    return f"l.{lineno}" if lineno else f"p.{page}"


def places(cites):
    """'l.5, l.20, l.31': where the citations are, in order, without repeats."""
    return list(dict.fromkeys(where(c.page, c.lineno)
                              for c in sorted(cites, key=lambda c: (c.page, c.lineno))))


@dataclass
class Ref:
    index: int
    text: str
    page: int = 0
    lineno: int = 0
    authors: str = ""
    first: str = ""
    surnames: list = field(default_factory=list)
    etal: bool = False
    year: str = ""
    suffix: str = ""
    cited: list = field(default_factory=list)     # the Cites matched to it
    key: str = ""
    title: str = ""
    doi: str = ""
    library: str = ""    # key of the matching entry in --library, if any

    @property
    def n(self):
        return 3 if self.etal else len(self.surnames)

    def label(self, width=100):
        t = self.text if len(self.text) <= width else self.text[:width] + "…"
        return f"{where(self.page, self.lineno):>7}  {t}"

    def short(self):
        """'Riehl and Malkus 1958', 'Feng et al. 2021a'."""
        if self.etal:
            a = f"{self.first} et al."
        elif len(self.surnames) == 2:
            a = f"{self.first} and {self.surnames[1]}"
        else:
            a = self.first
        return f"{a} {self.year}{self.suffix}"


@dataclass
class Cite:
    names: list      # surnames as written, e.g. ["Schumacher", "Houze"]
    etal: bool
    year: str
    suffix: str
    page: int
    lineno: int
    context: str
    pos: int = 0     # offsets in the joined text
    end: int = 0
    alias: str = ""  # set when this is a use of an abbreviation such as "C13"
    ref: object = None

    @property
    def first(self):
        return self.names[0]

    def label(self):
        if self.etal:
            a = ", ".join(self.names) + " et al."
        elif len(self.names) > 1:
            a = ", ".join(self.names[:-1]) + " and " + self.names[-1]
        else:
            a = self.names[0]
        s = f"{a} {self.year}{self.suffix}"
        return f"{self.alias} (= {s})" if self.alias else s


@dataclass
class Alias:
    alias: str
    cite: Cite       # the citation it abbreviates
    page: int
    lineno: int
    uses: list = field(default_factory=list)


@dataclass
class Analysis:
    path: Path
    source: str
    cites: list
    refs: list
    issues: dict
    aliases: list
    unlinked: list   # abbreviations with no citation just before them: [(alias, Line)]
    library: str = ""    # the --library directory, if one was checked

    def to_fetch(self):
        """Cited references missing from the library, most cited first."""
        if not self.library:
            return []
        return sorted((r for r in self.refs if r.year and r.cited and not r.library),
                      key=lambda r: (-len(r.cited), norm(r.first), r.year))


# --- text extraction -------------------------------------------------------

def pdftotext(path, layout):
    cmd = ["pdftotext", "-enc", "UTF-8"] + (["-layout"] if layout else []) + [str(path), "-"]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


# pdftotext renders accents in some PDFs (often Word-made) as a separate
# spacing mark, sometimes with a stray space: "N´ un˜ez", "Volont´e".
SPACING_ACCENTS = {"\u00b4": "\u0301", "`": "\u0300", "\u02dc": "\u0303", "\u00a8": "\u0308",
                   "\u02c6": "\u0302", "\u02c7": "\u030c", "\u00b8": "\u0327", "\u02da": "\u030a"}
SPACING_RE = re.compile(r"([A-Za-z]?)\s?([\u00b4`\u02dc\u00a8\u02c6\u02c7\u00b8\u02da])\s?([A-Za-z])")


def fix_unicode(s):
    """Recompose accents so that 'Muñoz' is one word however the PDF stored it."""
    def join(m):
        # The mark belongs to the following letter in TeX output ("Volont´e"),
        # which is what pdftotext gives for most PDFs.
        return m.group(1) + m.group(3) + SPACING_ACCENTS[m.group(2)]
    s = SPACING_RE.sub(join, s)
    return unicodedata.normalize("NFC", s)


def to_lines(text, margin=None):
    """Split into Lines, stripping line numbers that sit in the margin column.

    `margin` is the column where the line numbers end (they are right-aligned),
    so a section number such as the "1" in "1   Introduction" is left alone.
    """
    out, page, last = [], 1, 0
    for raw in text.split("\n"):
        page += raw.count("\f")
        raw = raw.replace("\f", "")
        lineno = 0
        if margin is not None:
            m = LINENO_RE.match(raw)
            if m and m.end(1) == margin:
                lineno = last = int(m.group(1))
                raw = raw[m.end():]
            elif raw.strip() and last and not re.fullmatch(r"\s*\d{1,5}\s*", raw):
                # Only every nth line numbered (lineno's \modulolinenumbers): count on.
                last += 1
                lineno = last
        s = fix_unicode(re.sub(r"\s+", " ", raw).strip())
        # A line that is only a number is a page number (or a stray line number).
        if s and not re.fullmatch(r"\d{1,5}", s):
            out.append(Line(page, lineno, s))
    # Lines above the first printed number (lines 1-4 when only every 5th is
    # numbered): count back from the first numbered line.
    first = next((i for i, l in enumerate(out) if l.lineno), None)
    if first:
        for i in range(first - 1, -1, -1):
            out[i].lineno = max(out[i + 1].lineno - 1, 0)
    return out


def line_number_margin(layout_text):
    """Return the column where manuscript line numbers end, or None.

    Review PDFs number every line (or every 5th) down the left margin: many
    rising numbers, all right-aligned to the same column.
    """
    rows = [l.replace("\f", "") for l in layout_text.split("\n")]
    text_rows = sum(1 for r in rows if r.strip())
    hits = [(m.end(1), int(m.group(1))) for r in rows
            if (m := LINENO_RE.match(r)) and r[m.end():].strip()]
    if not hits:
        return None
    margin = Counter(col for col, _ in hits).most_common(1)[0][0]
    nums = [n for col, n in hits if col == margin]
    if len(nums) < 10 or len(nums) < 0.05 * text_rows:
        return None
    # Steps of 1, or of up to 10 when only every nth line is numbered.
    rising = sum(0 < b - a <= 10 for a, b in zip(nums, nums[1:]))
    return margin if rising >= 0.8 * (len(nums) - 1) else None


def load(path, mode):
    """Return (lines, description of how the text was read)."""
    if path.suffix.lower() == ".txt":
        text = path.read_text(errors="replace")
        margin = line_number_margin(text) if mode != "no" else None
        return to_lines(text, margin), "text file" + (", line numbers stripped" if margin else "")
    layout = pdftotext(path, layout=True)
    margin = line_number_margin(layout) if mode != "no" else None
    if margin is not None:
        # -layout keeps each line number beside its own text; the default mode
        # emits the numbers as separate lines and can reorder headings.
        return to_lines(layout, margin), "line-numbered manuscript (pdftotext -layout)"
    if mode == "yes":
        sys.exit("--line-numbers yes, but no column of rising line numbers was found.")
    return to_lines(pdftotext(path, layout=False)), "no line numbers (pdftotext)"


def split_sections(lines):
    """Return (body, references, trailing lines after the references)."""
    heads = [i for i, l in enumerate(lines) if REF_HEAD_RE.match(l.text)]
    if not heads:
        sys.exit("No 'References' heading found. Extract the text yourself and pass "
                 "the .txt, with a line reading 'References' before the list.")
    start = heads[-1]
    end = next((j for j in range(start + 1, len(lines)) if REF_END_RE.match(lines[j].text)),
               len(lines))
    return lines[:start], lines[start + 1:end], lines[end:]


# --- references ------------------------------------------------------------

def surname_of(chunk):
    toks = [t for t in chunk.split() if t.lower() not in SUFFIXES and not INITIALS_RE.match(t)]
    return " ".join(toks)


def parse_ref(ref, prev):
    text = ref.text
    m = REF_YEAR_RE.search(text[:400])
    if not m:
        return ref
    ref.year, ref.suffix = m.group(1), m.group(2)
    authors = text[:m.start(1)].strip(" ,(")
    # AMS/AGU repeat-author dashes. "——, 2005:" repeats the whole author list
    # of the entry above; "——, and ——, 2006:" repeats its authors one by one.
    if re.match(DASHES, authors) and prev and prev.year:
        runs = re.findall(DASHES, authors)
        rest = re.sub(rf"{DASHES}|\band\b|,", "", authors).strip()
        if len(runs) == 1 and not rest:
            authors = prev.authors
        else:
            names = iter(prev.surnames)
            authors = re.sub(DASHES, lambda d: next(names, d.group(0)), authors)
        ref.text = authors + ", " + text[m.start(1):]
    ref.authors = authors
    # "et al." and AMS's "and Coauthors" both stand for a truncated list.
    if re.search(r"\bet al\b|\bCoauthors\b", authors):
        ref.etal = True
        authors = TRUNCATED_RE.sub("", authors)
    chunks = [c.strip() for c in re.split(r",|\band\b|&", authors) if c.strip()]
    if not chunks:
        return ref
    ref.first = chunks[0]
    ref.surnames = [chunks[0]] + [s for s in map(surname_of, chunks[1:]) if s]
    if len(ref.surnames) > 2:
        ref.etal = True
    return ref


def parse_refs(lines):
    entries = []        # [first Line, text]
    for line in lines:
        # A long author list can wrap onto a line that itself looks like the
        # start of an entry ("Strauch, F. H. Merrem, ..."): stay in the current
        # entry while it has no year yet and ends mid-list.
        mid_list = entries and not REF_YEAR_RE.search(entries[-1][1]) and re.search(
            r"(,|\b[A-Z]\.|&|\band)$", entries[-1][1])
        if (REF_START_RE.match(line.text) and not mid_list) or not entries:
            entries.append([line, line.text])
        else:
            t = entries[-1][1]
            entries[-1][1] = (t[:-1] if t.endswith("-") and line.text[:1].islower()
                              else t + " ") + line.text
    refs, prev = [], None
    for i, (line, text) in enumerate(entries):
        ref = parse_ref(Ref(i, text, line.page, line.lineno), prev)
        if ref.year:
            prev = ref
        refs.append(ref)
    return refs


# --- citations -------------------------------------------------------------

def clean_name(name):
    return re.sub(r"['’]s$", "", name.strip())     # "Zipser’s [1977]"


def join_lines(lines):
    """One string for the whole text, plus the offset where each line starts."""
    parts, starts, pos = [], [], 0
    for l in lines:
        if parts and parts[-1].endswith("-") and l.text[:1].islower():
            parts[-1] = parts[-1][:-1]      # undo end-of-line hyphenation
            pos -= 1
        elif parts:
            parts.append(" ")
            pos += 1
        starts.append(pos)
        parts.append(l.text)
        pos += len(l.text)
    return "".join(parts), starts


def find_cites(lines):
    """Return (cites, joined text, line start offsets)."""
    text, starts = join_lines(lines)
    cites = []
    for m in CITE_RE.finditer(text):
        names = [m.group("first")] + re.findall(SURNAME, m.group("more") or "")
        if m.group("last"):
            names.append(m.group("last"))
        names = [clean_name(n) for n in names]

        def junk(n):
            return norm(n.split()[-1]) in STOP or norm(n) in STOP or re.search(r"\d", n)

        # "However, Braun and Houze [1997]": drop leading non-names ...
        while names and junk(names[0]):
            names = names[1:]
        if not names:
            continue
        # ... and a stop word later in the list ends it ("Houze and January 2004").
        for i, n in enumerate(names[1:], 1):
            if junk(n):
                names = names[:i]
                break
        line = lines[bisect.bisect_right(starts, m.start()) - 1]
        ctx = text[max(0, m.start() - 60):m.end() + 25]
        last_year = ""
        for y in re.findall(rf"{YEAR}|(?<=,)\s*[a-z](?![\w.])", m.group("years")):
            y = y.strip()
            if len(y) == 1:                   # the "b" in "2021a, b"
                if not last_year:
                    continue
                year, suffix = last_year, y
            else:
                year, suffix = y[:4], y[4:]
                last_year = year
            cites.append(Cite(names, bool(m.group("etal")), year, suffix,
                              line.page, line.lineno, ctx, m.start(), m.end()))
    return cites, text, starts


def find_aliases(cites, lines, text, starts):
    """Abbreviations defined for citations, and every later use of each.

    An abbreviation belongs to the citation just before it, in the same
    sentence and at most 40 characters away: "Riehl and Malkus (1958,
    hereafter RM58)", "(Cortado 2013; hereafter referred to as C13)". Its
    later uses become Cites of the same work, counted like any citation.
    """
    defs = {}
    for rx in ALIAS_RES:
        for m in rx.finditer(text):
            if m.group("alias") not in defs or m.start() < defs[m.group("alias")].start():
                defs[m.group("alias")] = m
    aliases, unlinked = [], []
    for name, m in sorted(defs.items(), key=lambda kv: kv[1].start()):
        line = lines[bisect.bisect_right(starts, m.start()) - 1]
        at = m.start("alias")
        before = [c for c in cites if c.end <= at and at - c.end <= 40
                  and not re.search(r"[.!?]\s", text[c.end:at])]
        if not before:
            # "(hereafter RCEMIP)" names a project, not a paper; only a
            # citation-like abbreviation (with a digit: "C13") is worth reporting.
            if re.search(r"\d", name):
                unlinked.append((name, line))
            continue
        target = max(before, key=lambda c: c.end)
        a = Alias(name, target, line.page, line.lineno)
        for u in re.finditer(rf"(?<![\w\-]){re.escape(name)}(?![\w\-])", text):
            if u.start() < m.end():
                continue            # the definition itself, or text before it
            ul = lines[bisect.bisect_right(starts, u.start()) - 1]
            a.uses.append(Cite(target.names, target.etal, target.year, target.suffix,
                               ul.page, ul.lineno, text[max(0, u.start() - 60):u.end() + 25],
                               u.start(), u.end(), alias=name))
        aliases.append(a)
    return aliases, unlinked


# --- matching --------------------------------------------------------------

def levenshtein(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def near_name(a, b):
    """Edit distance if a and b are probably the same surname misspelt, else None.

    One edit for names of up to 5 letters (Hagos/Hagoss), two for longer ones.
    Accents, hyphens, spaces and case are already folded away by norm().
    """
    a, b = norm(a), norm(b)
    d = levenshtein(a, b)
    return d if 0 < d <= (1 if min(len(a), len(b)) <= 5 else 2) else None


def spelled(name):
    """Fold case and accents but keep hyphens and spaces, so 'García-Pérez' and
    'García Pérez' differ here but not under norm(). Accents are folded because
    PDF extraction mangles them too often to trust a difference."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).casefold().replace("’", "'")


def same_name(a, b):
    return norm(a) == norm(b)


def candidates(c, refs):
    """References with the cited first author and year.

    Falls back to a compound or corporate first author whose last word is the
    cited name: "Silva Dias et al." -> "Silva Dias, M. F."; "GPM Science Team,
    2017a" is found as "Team" and matched to "GPM Science Team".
    """
    exact = [r for r in refs if r.year == c.year and same_name(r.first, c.first)]
    if exact:
        return exact
    return [r for r in refs if r.year == c.year and len(r.first.split()) > 1
            and norm(r.first.split()[-1]) == norm(c.first)]


def author_problem(c, r):
    """Why the cited author list does not fit reference r, or ''."""
    n = f"{len(r.surnames)}{'+' if r.etal else ''}"
    for i, name in enumerate(c.names[1:], 1):
        if i >= len(r.surnames) or not (same_name(name, r.surnames[i])
                                         or near_name(name, r.surnames[i])):
            return f"cited author {i + 1} is {name}; reference differs"
    if c.etal:
        if r.n < 3:
            return f"cited with et al., reference has {n} author(s)"
    elif len(c.names) != len(r.surnames) or r.etal and len(c.names) < len(r.surnames):
        k = len(c.names)
        return f"cited as {k} author{'s' if k > 1 else ''}, reference has {n}"
    return ""


def check(cites, refs):
    """Match each citation to a reference (setting Cite.ref and Ref.cited) and
    return the problems found, by category: {category: [(cite, message)]}."""
    issues = defaultdict(list)
    seen = set()
    for c in cites:
        # The list pattern can pick up a leading word after a comma ("CRE,
        # Harrison et al."; "Recently, Benedict et al."): drop leading names
        # until the first one matches a reference. Never drop below the two
        # names either side of an "and": "Malkus and Riehl" is not "Riehl".
        keep = 1 if c.etal or len(c.names) == 1 else 2
        for i in range(1, len(c.names) - keep + 1):
            if candidates(c, refs):
                break
            trimmed = Cite(c.names[i:], c.etal, c.year, c.suffix, c.page, c.lineno, c.context)
            if candidates(trimmed, refs):
                c.names = trimmed.names
                break
        dedup = (tuple(map(norm, c.names)), c.etal, c.year, c.suffix)
        # Uses of an abbreviation repeat their citation's problems: count, don't flag.
        first_time = dedup not in seen and not c.alias
        seen.add(dedup)
        cands = candidates(c, refs)
        if not cands:
            # A near miss on the first author's name, same year: report it as a
            # spelling problem rather than a missing reference, but never match
            # it silently (Liu and Lin are both real surnames).
            near = sorted((d, r.index, r) for r in refs if r.year == c.year
                          for d in [near_name(c.first, r.first)] if d)
            if not near:
                if first_time:
                    issues["missing"].append((c, suggest(c, refs)))
                continue
            cands = [r for d, _, r in near if d == near[0][0]]
        exact = [r for r in cands if r.suffix == c.suffix]
        if not exact:
            exact = cands
            if first_time:
                have = ", ".join(r.year + (r.suffix or " (no letter)") for r in cands)
                issues["suffix"].append((c, f"reference list has {have}"))
        best = min(exact, key=lambda r: (bool(author_problem(c, r)), r.index))
        best.cited.append(c)
        c.ref = best
        problem = author_problem(c, best)
        if problem and first_time:
            issues["authors"].append((c, f"{problem}:\n{best.label()}"))
        if first_time:
            for name, ref_name in zip(c.names, best.surnames):
                if spelled(name) == spelled(ref_name):
                    continue
                # "SkofronickJackson": pdftotext drops the hyphen when a name
                # breaks across a line. Only a hyphen-vs-space difference
                # ("García-Pérez" / "García Pérez") is the author's.
                parts = [re.split(r"[-\s]+", spelled(x)) for x in (name, ref_name)]
                if "".join(parts[0]) == "".join(parts[1]) and min(map(len, parts)) == 1:
                    continue
                d = near_name(name, ref_name)
                if not d and norm(name) != norm(ref_name):
                    continue    # compound name matched on its last word, or a mismatch flagged above
                how = (f"{d} letter{'s' if d > 1 else ''} different: typo, "
                       f"or a different paper missing from the list?" if d else
                       "hyphens or spaces differ")
                issues["spelling"].append(
                    (c, f"“{name}” vs reference “{ref_name}” ({how}):\n{best.label()}"))
    return issues


def suggest(c, refs):
    out, first = [], norm(c.first)
    names = [norm(n) for n in c.names]
    for r in refs:
        if not r.year:
            continue
        f = norm(r.first)
        others = [norm(s) for s in r.surnames[1:]]
        if f == first:
            out.append(f"same first author, {r.year}{r.suffix}:\n{r.label()}")
        elif r.year == c.year and difflib.SequenceMatcher(None, f, first).ratio() >= 0.75:
            out.append(f"similar surname, same year:\n{r.label()}")
        elif r.year == c.year and any(difflib.SequenceMatcher(None, o, nm).ratio() >= 0.75
                                      for o in others for nm in names):
            out.append(f"same year, cited name(s) among its authors (order? spelling?):\n{r.label()}")
    return "\n".join(out[:3]) if out else "no near match in the reference list"


def duplicates(refs):
    keyed = defaultdict(list)
    for r in refs:
        if r.year:
            keyed[(norm(r.first), r.year, r.suffix, r.etal, tuple(map(norm, r.surnames)))].append(r)
    return [rs for rs in keyed.values() if len(rs) > 1]


# --- BibTeX ----------------------------------------------------------------

# Leading words skipped when choosing a key's word: "What is the role of..." -> role.
KEY_SKIP = {
    "a", "an", "the", "on", "of", "in", "for", "to", "and", "or", "at", "by", "from",
    "with", "into", "about", "as", "is", "are", "was", "were", "be", "do", "does",
    "can", "could", "will", "would", "should", "what", "why", "how", "when", "where",
    "which", "who", "whose", "whether",
}
# Old AMS DOIs contain a colon that PDF text often follows with a space:
# "10.1175/1520-0493(1979)107,0963: TOAFMM.2.0.CO;2".
DOI_RE = re.compile(r"(?:https?://\s?(?:dx\.)?doi\.org/\s?|doi:\s*)?(10\.\d{4,9}/\S+(?:(?<=:)\s\S+)?)", re.I)
# "…title. J. Climate, 34(21), 8599–8613" (AMS, APA) or "…title, Mon. Weather Rev.,
# 105, 1568–1589" (AGU). A journal name is capitalised words and connectives,
# which keeps a title's "Part I: Evolution and dynamics" out of it.
JWORD = r"(?:[A-Z][\w.'’&:\-]*|of|and|the|in|for|on|&|de|des|du|la|der|für|und)"
VENUE_RE = re.compile(
    rf"[.,?!]\s+(?P<journal>{JWORD}(?:\s+{JWORD})*),\s*(?P<volume>\d{{1,4}})"
    r"(?:\s*\((?P<number>[^)]{1,12})\))?"
    r"(?:,\s*(?P<pages>[A-Za-z]{0,3}\d+[A-Za-z0-9]*(?:\s*[\u2013\u2014-]+\s*[A-Za-z]{0,3}\d+)?))?")


SICI_RE = re.compile(r"^10\.1175/(\d{4})-?(\d{3}[\dX])\((\d{4})\)(\d{3})[,<]?(\d{4}):"
                     r"([A-Z0-9]+)[.>]?(2\.0\.CO;2)$", re.I)


def fix_sici(doi):
    """Rebuild an old AMS DOI as PDF text mangles it: '<' and '>' come out as
    ',' and '.', and the ISSN hyphen may go: "10.1175/15200450(2004)043,1095:
    SROLHP.2.0.CO;2" -> "10.1175/1520-0450(2004)043<1095:SROLHP>2.0.CO;2"."""
    m = SICI_RE.match(doi.replace(" ", ""))
    if not m:
        return doi
    a, b, year, vol, page, code, tail = m.groups()
    return f"10.1175/{a}-{b}({year}){vol}<{page}:{code.upper()}>{tail.upper()}"


def doi_url(doi):
    return "https://doi.org/" + quote(doi, safe="/():;.-_")


def bib_escape(s):
    return re.sub(r"([&%$#_])", r"\\\1", s).replace("{", "").replace("}", "")


def bib_persons(authors):
    """'Riehl, H., and J. S. Malkus' -> 'Riehl, H. and Malkus, J. S.'.

    Handles AMS order (first author inverted, the rest not) and APA order
    (all inverted) by attaching each run of initials to its surname.
    """
    truncated = bool(re.search(r"\bet al\b|\bCoauthors\b", authors))
    persons = []        # [surname, initials, suffix]
    for chunk in (c.strip() for c in re.split(r",|\band\b|&", TRUNCATED_RE.sub("", authors))):
        if not chunk:
            continue
        toks = chunk.split()
        inits = [t for t in toks if INITIALS_RE.match(t)]
        sufs = [t for t in toks if t.lower() in SUFFIXES]
        sur = " ".join(t for t in toks if t not in inits and t not in sufs)
        if sur:
            persons.append([sur, " ".join(inits), " ".join(sufs)])
        elif persons and inits and not persons[-1][1]:
            persons[-1][1] = " ".join(inits)       # APA, and AMS's first author: "Houze, R. A."
        elif persons and sufs:
            persons[-1][2] = " ".join(sufs)        # "Houze, R. A., Jr."
    out = []
    for sur, inits, suf in persons:
        if not inits and sur.isupper():
            out.append("{" + sur + "}")            # corporate author: {IPCC}
        else:
            out.append(", ".join(x for x in (sur, suf, inits) if x))
    if truncated:
        out.append("others")
    return " and ".join(out)


def bib_fields(ref):
    """Split a reference entry into BibTeX fields. Heuristic."""
    f = {}
    m = REF_YEAR_RE.search(ref.text[:400])
    rest = ref.text[m.end():] if m else ref.text
    rest = re.sub(r"^[a-z]?[).:,\s]+", "", rest)
    d = DOI_RE.search(rest)
    if d:
        doi = d.group(1)
        # An old AMS DOI cut short by a space, "10.1175/1520-0469(1984) 041,0113:
        # SIOTMC.2.0.CO;2": take the next one or two words if they end it.
        if "(" in doi and "CO;2" not in doi:
            more = re.match(r"\s?(\S*CO;2|\S+\s\S*CO;2)", rest[d.end():])
            if more:
                doi += more.group(1).replace(" ", "")
        f["doi"] = fix_sici(doi.rstrip(".,;)") if "CO;2" not in doi else doi.rstrip(".,"))
        rest = rest[:d.start()]
    rest = re.sub(r"\s*,?\s*https?://\S+", "", rest).strip(" .,")
    venues = list(VENUE_RE.finditer(rest))
    if venues:
        # The last "Journal, volume" group is the venue; the title is before it.
        v = venues[-1]
        end = rest[v.start()]
        f["title"] = rest[:v.start()].strip() + (end if end in "?!" else "")
        f["journal"] = v.group("journal").strip()
        f["volume"] = v.group("volume")
        if v.group("number"):
            f["number"] = v.group("number")
        if v.group("pages"):
            f["pages"] = re.sub(r"\s*[\u2013\u2014-]+\s*", "--", v.group("pages"))
        return f
    # Books, reports, conference papers: the title runs to the first sentence
    # end followed by a capital; the rest goes in a note.
    t = re.match(r"(?P<title>.+?[.?!])\s+(?=[A-Z])", rest)
    f["title"] = t.group("title").rstrip(".") if t else rest
    if t and rest[t.end():].strip(" ."):
        f["note"] = rest[t.end():].strip(" .")
    return f


def bib_key(ref, title, used):
    """<author><year><word>: first author's surname, year, first content word
    of the title; a letter is appended if the key is taken."""
    word = next((norm(w) for w in re.findall(r"[^\W\d_][\w'’-]*", title)
                 if norm(w) and norm(w) not in KEY_SKIP), "")
    base = norm(ref.first) + ref.year + word
    key, n = base, 0
    while key in used:
        n += 1
        key = base + chr(ord("a") + n)
    used.add(key)
    return key


def to_bibtex(refs):
    """Return the parsed references as BibTeX, setting each Ref.key."""
    used, out = set(), []
    for r in refs:
        if not r.year:
            continue
        f = bib_fields(r)
        r.key = bib_key(r, f["title"], used)
        r.title, r.doi = f["title"], f.get("doi", "")
        fields = [("author", bib_persons(r.authors)), ("title", bib_escape(f["title"])),
                  ("journal", f.get("journal")), ("year", r.year), ("volume", f.get("volume")),
                  ("number", f.get("number")), ("pages", f.get("pages")),
                  ("note", f.get("note") and bib_escape(f["note"])), ("doi", f.get("doi")),
                  ("citedcount", str(len(r.cited))), ("citedlines", ", ".join(places(r.cited))),
                  ("inlibrary", r.library)]
        out.append(f"% {where(r.page, r.lineno)}: {r.text}")
        out.append(f"@{'article' if 'journal' in f else 'misc'}{{{r.key},")
        out.append(",\n".join(f"    {k} = {{{v}}}" for k, v in fields if v))
        out.append("}\n")
    return "\n".join(out)


# --- library ---------------------------------------------------------------

@dataclass
class LibEntry:
    key: str
    doi: str
    first: str       # first author's surname, norm()ed
    year: str
    title: str       # letters and spaces only, lower case


BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)\n\s*\}", re.S)


def bib_value(body, name):
    m = re.search(rf"^\s*{name}\s*=\s*(.+?),?\s*$", body, re.M | re.I)
    return re.sub(r"[{}\"]", "", m.group(1)).strip() if m else ""


def plain_title(t):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFKD", t).lower()).split())


def load_library(directory):
    """Every entry of every .bib file under directory, plus, for litman
    (~/LitManData/literature: one directory per item, named by its key), the
    items that have no ref.bib, which can then only be matched by key."""
    root = Path(directory).expanduser()
    entries = [LibEntry(d.name, "", "", "", "") for d in sorted(root.iterdir())
               if d.is_dir() and not any(d.glob("*.bib"))]
    for path in sorted(root.rglob("*.bib")):
        for m in BIB_ENTRY_RE.finditer(path.read_text(errors="replace")):
            body = m.group(2)
            author = bib_value(body, "author").split(" and ")[0]
            surname = author.split(",")[0] if "," in author else (author.split() or [""])[-1]
            entries.append(LibEntry(m.group(1), bib_value(body, "doi").lower(), norm(surname),
                                    bib_value(body, "year")[:4], plain_title(bib_value(body, "title"))))
    return entries


def match_library(refs, entries):
    """Set Ref.library to the key of the library entry for the same work:
    same DOI; else the same key (for items with no bib); else same first
    author and year with a similar title (ratio 0.8)."""
    by_doi, by_key = defaultdict(list), {e.key: e for e in entries}
    by_author_year = defaultdict(list)
    for e in entries:
        if e.doi:
            by_doi[fix_sici(e.doi).lower()].append(e)
        by_author_year[(e.first, e.year)].append(e)

    def most_like(title, cands):
        """(similarity, key, entry) of the candidate whose title is closest."""
        return max(((difflib.SequenceMatcher(None, title, c.title).ratio(), c.key, c)
                    for c in cands), default=None, key=lambda t: (t[0], -len(t[1])))

    for r in refs:
        if not r.year:
            continue
        title = plain_title(r.title)
        # A supplement or preprint can share its paper's DOI: take the entry
        # whose title is closest ("Supplement for: …" loses).
        same_doi = by_doi.get(r.doi.lower(), []) if r.doi else []
        e = most_like(title, same_doi)[2] if same_doi else by_key.get(r.key)
        if not e:
            best = most_like(title, [c for c in by_author_year[(norm(r.first), r.year)] if c.title])
            e = best[2] if best and best[0] >= 0.8 else None
        if e:
            r.library = e.key


# --- report ----------------------------------------------------------------

def md(s):
    return re.sub(r"([*_`<>\[\]|])", r"\\\1", s)


def report(a):
    out = []
    p = out.append
    parsed = [r for r in a.refs if r.year]
    cited_refs = [r for r in parsed if r.cited]
    uncited = [r for r in parsed if not r.cited]
    unparsed = [r for r in a.refs if not r.year]
    dups = duplicates(a.refs)
    p(f"# Citation analysis: {md(a.path.name)}\n")
    p(f"Read as: {a.source}. Generated {date.today().isoformat()} by analyse-citations. "
      "Every flag is a lead to check, not a verdict.\n")
    p("| | count |\n|---|---:|")
    for k, v in [
        ("In-text citations", len(a.cites)),
        ("… uses of an abbreviation (e.g. “C13”)", sum(len(x.uses) for x in a.aliases)),
        ("… matched to a reference", sum(1 for c in a.cites if c.ref)),
        ("Reference entries", len(a.refs)),
        ("… cited at least once", len(cited_refs)),
        ("Cited but not in references", len(a.issues["missing"])),
        ("Name spelt differently", len(a.issues["spelling"])),
        ("Year letter mismatch", len(a.issues["suffix"])),
        ("Author mismatch", len(a.issues["authors"])),
        ("In references but never cited", len(uncited)),
        ("Possible duplicate references", len(dups)),
        ("Reference entries not parsed", len(unparsed)),
    ] + ([("Cited references already in the library", sum(1 for r in cited_refs if r.library)),
          ("Cited references to fetch", len(a.to_fetch()))] if a.library else []):
        p(f"| {k} | {v} |")
    p("")

    def section(title, n, note=""):
        p(f"## {title} ({n})\n")
        if note:
            p(f"{note}\n")

    def cite_items(rows):
        for c, msg in rows:
            p(f"- **{where(c.page, c.lineno)}** {md(c.label())}  ")
            p(f"  “…{md(c.context)}…”")
            for m in msg.split("\n"):
                p(f"  - {md(m.strip())}")
        p("")

    def ref_items(rs):
        for r in rs:
            p(f"- **{where(r.page, r.lineno)}** {md(r.text)}")
        p("")

    section("Cited but not in references", len(a.issues["missing"]))
    cite_items(a.issues["missing"])
    section("Name spelt differently from the reference", len(a.issues["spelling"]))
    cite_items(a.issues["spelling"])
    section("Year letter mismatch", len(a.issues["suffix"]))
    cite_items(a.issues["suffix"])
    section("Author mismatch", len(a.issues["authors"]),
            "Author count or a co-author differs. AMS style uses et al. for 3+ authors.")
    cite_items(a.issues["authors"])
    section("In references but never cited", len(uncited))
    ref_items(uncited)
    section("Possible duplicate references", len(dups))
    for rs in dups:
        p("- " + "  \n  ".join(f"**{where(r.page, r.lineno)}** {md(r.text)}" for r in rs))
    p("")
    section("Reference entries not parsed", len(unparsed),
            "No year found: a wrapped line, a heading or a malformed entry. Check by hand.")
    ref_items(unparsed)

    section("Abbreviated citations", len(a.aliases) + len(a.unlinked),
            "Abbreviations defined with “hereafter”. Each later use counts as a citation.")
    if a.aliases:
        p("| Abbreviation | Stands for | Defined | Uses | Reference |\n|---|---|---|---:|---|")
        for x in a.aliases:
            ref = x.cite.ref.key if x.cite.ref else "not in references"
            p(f"| {md(x.alias)} | {md(x.cite.label())} | {where(x.page, x.lineno)} "
              f"| {len(x.uses)} | {md(ref)} |")
        p("")
    for name, line in a.unlinked:
        p(f"- **{where(line.page, line.lineno)}** “{md(name)}” is defined with “hereafter”, "
          "but no citation comes just before it, so its uses are not counted.")
    if a.unlinked:
        p("")

    section("Citation counts", len(cited_refs),
            "Times each reference is cited in the text, including uses of abbreviations. "
            "Uncited references are listed above.")
    lib = " In library |" if a.library else ""
    p(f"| Cited | Reference | Key |{lib} Where |\n|---:|---|---|{'---|' if lib else ''}---|")
    for r in sorted(cited_refs, key=lambda r: (-len(r.cited), norm(r.first), r.year)):
        at = places(r.cited)
        more = f" … (+{len(at) - 12})" if len(at) > 12 else ""
        held = f" {r.library or '—'} |" if a.library else ""
        p(f"| {len(r.cited)} | {md(r.short())} | {r.key} |{held} {', '.join(at[:12])}{more} |")
    p("")

    if a.library:
        fetch = a.to_fetch()
        section("To fetch", len(fetch),
                f"Cited references not found in {md(a.library)}, most cited first. "
                "`--fetch N` opens the first N DOIs in the browser.")
        p("| Cited | Reference | Title | DOI |\n|---:|---|---|---|")
        for r in fetch:
            title = r.title if len(r.title) <= 80 else r.title[:80] + "…"
            doi = f"[{md(r.doi)}]({doi_url(r.doi)})" if r.doi else "none: search by title"
            p(f"| {len(r.cited)} | {md(r.short())} | {md(title)} | {doi} |")
        p("")
    return "\n".join(out)


def citations_tsv(a):
    rows = ["page\tline\tcited_as\tkey\tin_library\tcontext"]
    for c in sorted(a.cites, key=lambda c: (c.page, c.lineno, c.pos)):
        key, held = (c.ref.key, c.ref.library) if c.ref else ("", "")
        rows.append(f"{c.page}\t{c.lineno}\t{c.label()}\t{key}\t{held}\t{c.context}")
    return "\n".join(rows) + "\n"


# --- driver ----------------------------------------------------------------

def run(path, line_numbers="auto", library=None):
    path = Path(path)
    lines, source = load(path, line_numbers)
    body, ref_lines, trailing = split_sections(lines)
    refs = parse_refs(ref_lines)
    cites, text, starts = find_cites(body)
    aliases, unlinked = find_aliases(cites, body, text, starts)
    # Tables and figure captions after the reference list cite papers too.
    cites += find_cites(trailing)[0]
    for x in aliases:
        cites += x.uses
    issues = check(cites, refs)
    to_bibtex(refs)        # sets the keys, titles and DOIs used below
    if library:
        match_library(refs, load_library(library))
    return Analysis(path, source, cites, refs, issues, aliases, unlinked,
                    str(library) if library else "")


def open_dois(a, n):
    """Open the DOIs of the n most-cited references to fetch in the browser;
    list those among them that have no DOI."""
    import webbrowser
    for r in a.to_fetch()[:n]:
        if r.doi:
            print(f"Opening {r.short()}: {doi_url(r.doi)}")
            webbrowser.open(doi_url(r.doi))
        else:
            print(f"No DOI, search by title: {r.short()}: {r.title}")


def write(a, outdir):
    """Write <stem>_report.md, <stem>_references.bib and <stem>_citations.tsv."""
    outdir.mkdir(parents=True, exist_ok=True)
    stem = a.path.stem
    rep = report(a)
    (outdir / f"{stem}_report.md").write_text(rep)
    (outdir / f"{stem}_references.bib").write_text(
        f"% Reference list of {a.path.name}, parsed by analyse-citations on "
        f"{date.today().isoformat()}.\n% Heuristic: each entry has its raw text above "
        f"it; check before use.\n\n" + to_bibtex(a.refs))
    (outdir / f"{stem}_citations.tsv").write_text(citations_tsv(a))
    return rep


def main():
    # --help shows the usage part; the provenance is for readers of the source.
    ap = argparse.ArgumentParser(description=__doc__.split("\nProvenance\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path, help="PDF, or a .txt already extracted")
    ap.add_argument("-o", "--out", type=Path, metavar="DIR", default=Path("."),
                    help="output directory (default: the current one)")
    ap.add_argument("--line-numbers", choices=["auto", "yes", "no"], default="auto",
                    help="line-numbered manuscript? (default: detect)")
    ap.add_argument("-q", "--quiet", action="store_true", help="do not print the report")
    ap.add_argument("--library", metavar="DIR", default=os.environ.get("ANALYSE_CITATIONS_LIBRARY"),
                    help="directory of .bib files (e.g. ~/LitManData/literature) to check "
                         "which cited references you already hold (default: "
                         "$ANALYSE_CITATIONS_LIBRARY)")
    ap.add_argument("--fetch", type=int, metavar="N",
                    help="open the DOIs of the N most-cited references not in the "
                         "library in the browser, to download them")
    args = ap.parse_args()
    if args.fetch and not args.library:
        ap.error("--fetch needs --library, to know what you already have")
    a = run(args.file, args.line_numbers, args.library)
    rep = write(a, args.out)
    if not args.quiet:
        print(rep)
    stem = args.out / args.file.stem
    print(f"Wrote {stem}_report.md, {stem}_references.bib and {stem}_citations.tsv")
    if args.fetch:
        open_dois(a, args.fetch)


if __name__ == "__main__":
    main()
