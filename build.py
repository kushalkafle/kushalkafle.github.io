#!/usr/bin/env python3
"""Build kushalkafle.com into _site/.

    python3 build.py                     # build the website into _site/
    python3 build.py --cv-dir DIR        # also write CV fragments: DIR/pubs.tex, DIR/transfers.tex

Publications come from pubs.bib; news, tech transfers, talks and site settings from
src/*.yml; layout from src/_base.html.j2, the home page from src/index.html.j2, and
project pages from src/projects/*.html.j2. See the header of pubs.bib for supported custom fields.
"""
import argparse
import datetime as dt
import re
import shutil
import sys
import subprocess
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "_site"
ME = "Kushal Kafle"

TOPICS = [
    ("mllm", "Multimodal LLMs & Evaluation"),
    ("vlrep", "Vision-Language Representation Learning"),
    ("gen", "Generative Models & Image Editing"),
    ("bias", "Fairness & Robustness"),
    ("vqa", "Visual Question Answering"),
]
COPY = ["CNAME", "favicon.ico", "images", "data"]
COPY_IGNORE = shutil.ignore_patterns("game", ".DS_Store")


# ----------------------------------------------------------------- BibTeX

def _read_braced(s, i):
    """s[i] is '{' -> (content, index after matching '}')."""
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{" and s[j - 1] != "\\":
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError(f"Unbalanced braces near: {s[i:i + 60]!r}")


def parse_bib(text):
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{", text):
        body, _ = _read_braced(text, m.end() - 1)
        key, _, rest = body.partition(",")
        fields, i = {}, 0
        while True:
            fm = re.compile(r"\s*(\w+)\s*=\s*").match(rest, i)
            if not fm:
                break
            name, i = fm.group(1).lower(), fm.end()
            if rest[i] == "{":
                value, i = _read_braced(rest, i)
            elif rest[i] == '"':
                j = rest.index('"', i + 1)
                value, i = rest[i + 1:j], j + 1
            else:
                vm = re.compile(r"[^,\s}]+").match(rest, i)
                value, i = vm.group(0), vm.end()
            fields[name] = " ".join(value.split())
            i = rest.find(",", i) + 1 or len(rest)
        raw = text[m.start(): m.end() - 1 + len(body) + 2]
        entries.append({"type": m.group(1).lower(), "key": key.strip(), "raw": raw.strip(), **fields})
    return entries


ACCENTS = {"'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302", "~": "\u0303", "v": "\u030c",
           "c": "\u0327", "=": "\u0304", ".": "\u0307", "u": "\u0306", "H": "\u030b"}


def delatex(s):
    import unicodedata
    s = re.sub(r"\\textquotesingle\s*", "'", s)
    s = re.sub(r"\\textquotedbl\s*", '"', s)
    s = re.sub(r"\\([`'\"^~=.]|[vcuH](?=[\s{]))\s*\{?\\?([A-Za-z])\}?",
               lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_").replace("~", "\u00a0")
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    return re.sub(r"[{}]", "", s)


def _words(name):
    """Split on spaces outside braces, so "Salma {Abdel Magid}" keeps the braced surname together."""
    words, depth, cur = [], 0, ""
    for ch in name:
        depth += ch == "{"
        depth -= ch == "}"
        if ch.isspace() and depth == 0:
            if cur:
                words.append(cur)
            cur = ""
        else:
            cur += ch
    return words + ([cur] if cur else [])


def split_authors(author_field):
    names = []
    for a in re.split(r"\s+and\s+", " ".join(author_field.split())):
        if "," in a:
            last, _, first = (p.strip() for p in a.partition(","))
        else:  # "First von Last" form (e.g. arXiv exports)
            w = _words(a)
            i = len(w) - 1
            while i > 1 and w[i - 1][:1].islower():
                i -= 1
            first, last = " ".join(w[:i]), " ".join(w[i:])
        names.append((delatex(first), delatex(last)))
    return names


# ------------------------------------------------------------ Publications

# Short venue labels derived from the official booktitle/journal. Acronyms in the BibTeX itself
# (e.g. "... (CVPR)", "Computer Vision -- ECCV 2024", "BMVC") are used directly; this table covers
# venues whose official name has no acronym. Add a row when a new venue appears.
VENUE_LUT = [
    (r"Neural Information Processing Systems", "NeurIPS"),
    (r"AAAI Conference on Artificial Intelligence", "AAAI"),
    (r"Annual Meeting of the Association for Computational Linguistics", "ACL"),
    (r"Empirical Methods in Natural Language Processing", "EMNLP"),
    (r"North American Chapter of the Association for Computational Linguistics", "NAACL"),
    (r"International Conference on Natural Language Generation", "INLG"),
    (r"International Conference on Machine Learning", "ICML"),
    (r"International Conference on Learning Representations", "ICLR"),
    (r"Computer Vision and Image Understanding", "CVIU"),
    (r"Frontiers in Artificial Intelligence", "Frontiers in AI"),
    (r"Transactions on Machine Learning Research", "TMLR"),
]
SCHOOL_LUT = {"Rochester Institute of Technology": "RIT"}


def derive_venue(e):
    """-> (short venue, event year, is_workshop) from the official BibTeX fields."""
    year = int(e["year"])
    if e["type"] == "phdthesis":
        school = delatex(e.get("school", ""))
        return f"Ph.D. Thesis, {SCHOOL_LUT.get(school, school)}", year, False
    if e.get("eprint") and not (e.get("booktitle") or e.get("journal")):
        return "arXiv", year, False
    full = delatex(e.get("booktitle") or e.get("journal") or "")
    m = re.search(r"\(([A-Z][A-Za-z]+)\)\s*Workshops?\b", full)
    if m:
        return m.group(1) + "W", year, True
    m = re.search(r"--?\s*([A-Z][A-Za-z]+)\s+(\d{4})\b", full) or re.search(r"\u2013\s*([A-Z][A-Za-z]+)\s+(\d{4})\b", full)
    if m:  # Springer: "Computer Vision -- ECCV 2024" (its `year` is often the print year)
        return m.group(1), int(m.group(2)), False
    m = re.search(r"\(([A-Z][A-Za-z]+)\)\s*$", full)
    if m:
        return m.group(1), year, False
    if re.fullmatch(r"[A-Z][A-Za-z]{1,9}", full):
        return full, year, "workshop" in full.lower()
    for pattern, label in VENUE_LUT:
        if re.search(pattern, full):
            return label, year, False
    print(f"warning: no short venue for {e['key']!r} ({full!r}); add a row to VENUE_LUT", file=sys.stderr)
    return full, year, False


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [x.strip() for x in str(v).split(",") if x.strip()]


def load_pubs():
    meta = load_yaml("papers.yml") or {}
    entries = parse_bib((ROOT / "pubs.bib").read_text(encoding="utf-8"))
    unknown = set(meta) - {e["key"] for e in entries}
    if unknown:
        raise SystemExit(f"src/papers.yml has keys not in pubs.bib: {sorted(unknown)}")
    pubs = []
    for e in entries:
        m = meta.get(e["key"]) or {}
        venue, year, workshop = derive_venue(e)
        if e["type"] == "inproceedings":
            kind = "workshop" if workshop else "conference"
        elif e["type"] == "article":
            kind = "journal"
        elif e["type"] == "phdthesis":
            kind = "thesis"
        else:
            kind = "preprint"
        equal = {int(x) for x in as_list(m.get("equal"))}
        authors = [{"name": f"{f} {l}".strip(), "first": f, "last": l,
                    "me": f"{f} {l}" == ME, "equal": i + 1 in equal}
                   for i, (f, l) in enumerate(split_authors(e["author"]))]
        arxiv = str(m.get("arxiv") or (e.get("eprint") if "arxiv" in e.get("archiveprefix", "").lower() else "") or "")
        doi = e.get("doi") or m.get("doi")
        links = []
        if arxiv:
            links.append(("arXiv", f"https://arxiv.org/abs/{arxiv}"))
        if m.get("pdf"):
            links.append(("PDF", m["pdf"]))
        elif doi and not arxiv:
            links.append(("Paper", f"https://doi.org/{doi}"))
        for field, label in (("code", "Code"), ("project", "Project")):
            if m.get(field):
                links.append((label, m[field]))
        pubs.append({
            "key": e["key"], "kind": kind, "year": year,
            "title": delatex(e["title"]),
            "authors": authors, "has_equal": bool(equal),
            "venue": venue,
            "venue_label": venue if kind == "thesis" and str(year) in venue else
                           (f"{venue}, {year}" if kind == "thesis" else f"{venue} {year}"),
            "venue_full": delatex(e.get("booktitle") or e.get("journal") or e.get("school") or ""),
            "award": m.get("award", ""),
            "topics": as_list(m.get("topic")),
            "selected": bool(m.get("selected")),
            "thumb": m.get("thumb", ""),
            "links": links,
            "bibtex": e["raw"],
        })
    pubs.sort(key=lambda p: -p["year"])  # stable: keeps file order within a year
    return pubs


# --------------------------------------------------------------------- CV

def cv_name(a):
    initials = " ".join("-".join(f"{h[0]}." for h in p.split("-") if h) for p in a["first"].split())
    s = f"{a['last']}, {initials}".strip().rstrip(",")
    if a["equal"]:
        s += "*"
    return rf"\textbf{{{s}}}" if a["me"] else s


def tex_escape(s):
    return s.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")


def cv_item(p):
    names = [cv_name(a) for a in p["authors"]]
    if len(names) <= 2:
        authors = r" \& ".join(names)
    else:
        authors = ", ".join(names[:-1]) + r", \& " + names[-1]
    venue = "arXiv preprint" if p["kind"] == "preprint" else p["venue_label"]
    title = tex_escape(p["title"]) + ("" if p["title"][-1] in "?!." else ".")
    line = rf"    \item {authors} ({p['year']}). {title} \emph{{{tex_escape(venue)}}}."
    url = dict(p["links"]).get("arXiv") or dict(p["links"]).get("Paper") or dict(p["links"]).get("PDF")
    if p["kind"] == "preprint" and url:
        line = line[:-1] + rf" \href{{{url}}}{{arXiv:{url.rsplit('/', 1)[-1]}}}."
    if p["award"]:
        line += rf" \textcolor{{red}}{{{tex_escape(p['award'])}}}"
    if p["has_equal"]:
        line += r" \textcolor{red}{*equal contribution}"
    return line


def write_cv_pubs(pubs, path):
    groups = [("Peer Reviewed International Conferences", "conference", "C"),
              ("Peer Reviewed Journals", "journal", "J"),
              ("Workshop Papers", "workshop", "W"),
              ("Preprints", "preprint", "P")]
    out = ["% AUTO-GENERATED by build.py from pubs.bib -- do not edit by hand.", ""]
    for title, kind, label in groups:
        items = [p for p in pubs if p["kind"] == kind]
        if not items:
            continue
        out += [rf"\subsection*{{{title}}}", rf"\begin{{enumerate}}[label=({label}\arabic*)]", r"\small"]
        out += [cv_item(p) for p in items]
        out += [r"\end{enumerate}", ""]
    Path(path).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {path}")


def html_to_tex(s):
    links = []

    def keep(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00{len(links) - 1}\x00"

    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', keep, s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    s = tex_escape(s).replace("–", "--")
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: r"\href{%s}{%s}" % (links[int(m.group(1))][0], tex_escape(links[int(m.group(1))][1])), s)


def write_cv_transfers(transfers, path):
    out = ["% AUTO-GENERATED by build.py from src/transfers.yml -- do not edit by hand.",
           r"\begin{itemize}[leftmargin=*]", r"\small"]
    others = []
    for t in transfers:
        for b in t.get("bullets") or []:
            if isinstance(b, dict) and b.get("short"):
                others.append(b["short"])
        if t.get("cv") != "highlight":
            if t.get("short"):
                others.append(t["short"])
            continue
        name = tex_escape(t["name"])
        if t.get("links"):
            name = rf"\href{{{t['links'][0][1]}}}{{{name}}}"
        out.append(rf"\item \textbf{{{name}}} \hfill \textit{{{html_to_tex(str(t['span']))}}}\\")
        out.append(rf"\begin{{scriptsize}}{html_to_tex(' '.join(t['text'].split()))}\end{{scriptsize}}")
        out.append("")
    if others:
        out.append(r"\item \textbf{Other transfers:} \begin{scriptsize}"
                   + "; ".join(html_to_tex(o) for o in others) + r".\end{scriptsize}")
    out.append(r"\end{itemize}")
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {path}")


# ------------------------------------------------------------------- Site

def pubs_updated():
    """Date pubs.bib last changed: its git commit date, or file mtime if it has uncommitted edits."""
    bib = ROOT / "pubs.bib"
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        except OSError:
            return ""
    if not git("status", "--porcelain", "--", bib.name):
        stamp = git("log", "-1", "--format=%cs", "--", bib.name)
        if stamp:
            return dt.date.fromisoformat(stamp)
    return dt.date.fromtimestamp(bib.stat().st_mtime)


def load_yaml(name):
    return yaml.safe_load((SRC / name).read_text(encoding="utf-8"))


def build_site(pubs):
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in COPY:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, OUT / name, ignore=COPY_IGNORE)
        elif src.exists():
            shutil.copy2(src, OUT / name)
    for asset in ("style.css", "site.js"):
        shutil.copy2(SRC / asset, OUT / asset)

    site = load_yaml("site.yml") or {}
    transfers = load_yaml("transfers.yml") or []
    by_key = {p["key"]: p for p in pubs}
    news = load_yaml("news.yml") or []
    for n in news:
        missing = [k for k in n.get("papers", []) if k not in by_key]
        if missing:
            raise SystemExit(f"news.yml ({n['date']}): unknown paper keys {missing}")
        n["refs"] = [by_key[k] for k in n.get("papers", [])]
    interns = load_yaml("interns.yml") or []
    intern_years = [(y, [i for i in interns if i["year"] == y])
                    for y in sorted({i["year"] for i in interns}, reverse=True)]
    tabs = [{"id": "selected", "label": "Selected", "pubs": [p for p in pubs if p["selected"]]}]
    for tid, label in TOPICS:
        tabs.append({"id": tid, "label": label, "pubs": [p for p in pubs if tid in p["topics"]]})
    tabs.append({"id": "all", "label": "All", "pubs": pubs})

    env = Environment(loader=FileSystemLoader(SRC), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    common = dict(site=site, built=dt.date.today().strftime("%B %Y"))
    for tpl in sorted((SRC / "projects").glob("*.html.j2")):
        out = OUT / "projects" / tpl.name[: -len(".j2")]
        out.parent.mkdir(exist_ok=True)
        out.write_text(env.get_template(f"projects/{tpl.name}").render(root="../", **common), encoding="utf-8")
    page = env.get_template("index.html.j2").render(
        root="", tabs=tabs, news=news, transfers=transfers, pubs=pubs, talks=load_yaml("talks.yml") or [], intern_years=intern_years, **common,
        pubs_updated=f"{pubs_updated():%B} {pubs_updated().day}, {pubs_updated():%Y}",
        counts={k: sum(p["kind"] == k for p in pubs) for k in ("conference", "journal", "workshop", "preprint")},
    )
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"built {OUT.relative_to(ROOT)}/index.html: {len(pubs)} publications, {len(news)} news items")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cv-dir", help="also write CV fragments (pubs.tex, transfers.tex) into this directory")
    args = ap.parse_args()
    pubs = load_pubs()
    build_site(pubs)
    if args.cv_dir:
        Path(args.cv_dir).mkdir(parents=True, exist_ok=True)
        write_cv_pubs(pubs, Path(args.cv_dir) / "pubs.tex")
        write_cv_transfers(load_yaml("transfers.yml") or [], Path(args.cv_dir) / "transfers.tex")


if __name__ == "__main__":
    main()
