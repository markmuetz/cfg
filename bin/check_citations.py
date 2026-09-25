#!/usr/bin/env python3
"""Cross-check author-year citations against the reference list of a PDF.

Runs entirely locally (pdftotext + regexes): nothing is sent anywhere, so it is
safe to use on a confidential manuscript or a student's dissertation. It flags

  - citations with no matching reference, with near-miss suggestions (a
    misspelt surname, a different year, the cited name being a co-author);
  - names spelt differently from the reference (a letter or two out, or a
    hyphen where the reference has a space);
  - citations whose author count or year suffix disagrees with the reference
    ("Yuan et al. 2010" against a two-author entry; "Feng et al. 2021" when
    the list has 2021a and 2021b);
  - references that are never cited, duplicated, or could not be parsed.

Line-numbered review manuscripts are detected automatically and every flag
carries the manuscript line number. It understands author-year styles (AMS,
AGU, APA, Harvard), not numbered ones. The parsing is heuristic: treat every
flag as "look at this", not as a verdict, and check the NOT PARSED section.

Usage:
    check-citations manuscript.pdf
    check-citations manuscript.pdf --tsv outdir/   # also dump both lists as TSV
    check-citations manuscript.txt                 # text you extracted yourself

Needs Python 3.8+ and pdftotext (poppler: `brew install poppler`).
Tests: python3 ~/bin/tests/check_citations/test_check_citations.py (needs pdflatex).

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
with every line and every 5th line numbered (tests/check_citations/), and a
regression pass over eight published papers from MM's library in AMS, AGU,
Wiley/APA and AMS Early Online Release styles. On those, most remaining flags
were genuine errors in the published papers (a citation to the wrong year, a
misspelt surname, a six-author paper cited as one author).

History: developed in lit-workflow (scripts/check_citations.py); near-miss
matching added after a hyphenated surname in a manuscript's text appeared
unhyphenated in its reference list and was reported as missing; moved to cfg
~/bin the same day, to use for reviewing and for marking dissertations.
"""
import argparse
import bisect
import difflib
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PARTICLE = r"(?:(?:[Vv]an|[Vv]on|[Dd]e|[Dd]el|[Dd]er|[Dd]en|[Dd]a|[Dd]i|[Dd]u|[Ll]a|[Ll]e|[Tt]en|[Tt]er|[Dd]os)\s+){0,2}"
SURNAME = PARTICLE + r"[A-Z][\w\u0300-\u036f'’\-]*\w"
# One name, "A and B", "A et al.", or an APA 7 list: "A, B, C, & D" / "A, B, et al.".
AUTHORS = (rf"(?P<first>{SURNAME})(?P<more>(?:\s*,\s*{SURNAME})*)"
           rf"(?:(?P<etal>,?\s+et\s+al\.?)|\s*,?\s*(?:and|&)\s+(?P<last>{SURNAME}))?")
YEAR = r"(?:1[89]\d\d|20\d\d)[a-z]?"
YEARS = rf"{YEAR}(?:\s*,\s*(?:{YEAR}|[a-z](?![\w.])))*"
CITE_RE = re.compile(
    rf"(?<![\w'’\-]){AUTHORS}\s*,?\s*[(\[]?\s*(?:e\.g\.,?\s*)?(?P<years>{YEARS})(?!\w)")

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
DASHES = r"[—–_\-]{2,}"
REF_START_RE = re.compile(
    rf"^\s*(?:{PARTICLE}[A-Z][^\s,.:;()]*(?:[ \-][A-Z][^\s,.:;()]*)*"
    r",\s+(?:[A-Z]\.|(?:1[89]|20)\d\d[a-z]?[:.)])"
    rf"|{DASHES})")
REF_YEAR_RE = re.compile(r"(?:^|[\s(,])((?:1[89]|20)\d\d)([a-z]?)(?=[\s).:,;]|$)")
INITIALS_RE = re.compile(r"^(?:[A-Z]\.-?)+$|^[A-Z]{1,2}$|^[A-Z]\.?-[A-Z]\.?$")
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}
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
    cited: int = 0

    @property
    def n(self):
        return 3 if self.etal else len(self.surnames)

    def label(self, width=100):
        t = self.text if len(self.text) <= width else self.text[:width] + "…"
        return f"{where(self.page, self.lineno):>7}  {t}"


@dataclass
class Cite:
    names: list      # surnames as written, e.g. ["Schumacher", "Houze"]
    etal: bool
    year: str
    suffix: str
    page: int
    lineno: int
    context: str

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
        return f"{a} {self.year}{self.suffix}"


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
            elif raw.strip() and last:
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
        authors = re.sub(r",?\s*(?:and\s+)?(?:et al\.?|Coauthors)", "", authors)
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


def find_cites(lines):
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
    text = "".join(parts)
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
                              line.page, line.lineno, ctx))
    return cites


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
    issues = defaultdict(list)       # category -> [(cite, message)]
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
        first_time = dedup not in seen
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
        best.cited += 1
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


# --- output ----------------------------------------------------------------

def indent(s, pad=" " * 11):
    return "\n".join(pad + l.strip() if i else l for i, l in enumerate(s.split("\n")))


def report(source, cites, refs, issues):
    out = [f"Read as: {source}",
           f"{len(cites)} citations in the text, {len(refs)} reference entries.", ""]
    p = out.append

    def section(title, rows, fmt, note=""):
        p(f"== {title} ({len(rows)})" + (f"  {note}" if note else ""))
        for row in rows:
            p(fmt(row))
        p("")

    def cite_fmt(row):
        c, msg = row
        return (f"  {where(c.page, c.lineno):>7}  {c.label()}\n"
                f"           “…{c.context}…”\n"
                f"           {indent(msg)}")

    section("CITED BUT NOT IN REFERENCES", issues["missing"], cite_fmt)
    section("NAME SPELT DIFFERENTLY FROM THE REFERENCE", issues["spelling"], cite_fmt)
    section("YEAR LETTER MISMATCH", issues["suffix"], cite_fmt)
    section("AUTHOR MISMATCH", issues["authors"], cite_fmt,
            "(count, or second author; AMS uses et al. for 3+)")
    section("IN REFERENCES BUT NEVER CITED",
            [r for r in refs if r.year and not r.cited], lambda r: f"  {r.label()}")
    keyed = defaultdict(list)
    for r in refs:
        if r.year:
            keyed[(norm(r.first), r.year, r.suffix, r.etal, tuple(map(norm, r.surnames)))].append(r)
    section("POSSIBLE DUPLICATE REFERENCES", [rs for rs in keyed.values() if len(rs) > 1],
            lambda rs: "\n".join(f"  {r.label()}" for r in rs))
    section("REFERENCE ENTRIES NOT PARSED", [r for r in refs if not r.year],
            lambda r: f"  {r.label()}",
            "(no year found; may be a wrapped line or a heading: check by hand)")
    return "\n".join(out)


def dump_tsv(outdir, cites, refs):
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "citations.tsv", "w") as f:
        f.write("page\tline\tcited_as\tyear\tcontext\n")
        for c in cites:
            f.write(f"{c.page}\t{c.lineno}\t{c.label()}\t{c.year}{c.suffix}\t{c.context}\n")
    with open(outdir / "references.tsv", "w") as f:
        f.write("page\tline\tfirst\tn_authors\tyear\ttimes_cited\tentry\n")
        for r in refs:
            n = f"{len(r.surnames)}{'+' if r.etal else ''}"
            f.write(f"{r.page}\t{r.lineno}\t{r.first}\t{n}\t{r.year}{r.suffix}\t{r.cited}\t{r.text}\n")


def run(path, line_numbers="auto"):
    lines, source = load(path, line_numbers)
    body, ref_lines, trailing = split_sections(lines)
    refs = parse_refs(ref_lines)
    # Tables and figure captions after the reference list cite papers too.
    cites = find_cites(body) + find_cites(trailing)
    return source, cites, refs, check(cites, refs)


def main():
    # --help shows the usage part; the provenance is for readers of the source.
    ap = argparse.ArgumentParser(description=__doc__.split("\nProvenance\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path, help="PDF, or a .txt already extracted")
    ap.add_argument("--line-numbers", choices=["auto", "yes", "no"], default="auto",
                    help="line-numbered manuscript? (default: detect)")
    ap.add_argument("--tsv", type=Path, metavar="DIR",
                    help="also write citations.tsv and references.tsv")
    args = ap.parse_args()
    source, cites, refs, issues = run(args.file, args.line_numbers)
    print(report(source, cites, refs, issues))
    if args.tsv:
        dump_tsv(args.tsv, cites, refs)
        print(f"Wrote {args.tsv}/citations.tsv and {args.tsv}/references.tsv")


if __name__ == "__main__":
    main()
