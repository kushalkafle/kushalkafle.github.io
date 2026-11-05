# Agent guide for kushalkafle.com

Personal academic website of Kushal Kafle. A small Python static generator renders
`_site/`, which GitHub Actions deploys to GitHub Pages (custom domain via `CNAME`).

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python build.py                          # render into _site/
.venv/bin/python -m http.server 8000 -d _site      # preview at http://localhost:8000
.venv/bin/python build.py --cv-dir <cv-repo>       # also write <cv-repo>/pubs.tex and transfers.tex
```

There are no tests. Verify changes by building, opening the preview (desktop and a ~390px
phone width), and checking that links and images resolve.

## Where things live

| Edit this | For |
|---|---|
| `pubs.bib` | All publications (site + CV). Custom fields documented at the top of the file. |
| `src/news.yml` | News, newest first. |
| `src/transfers.yml` | Tech Transfers cards; also drives the CV transfers section. |
| `src/talks.yml` | Talks section. |
| `src/site.yml` | Public title and the highlighted banner. |
| `src/index.html.j2` | Home page text and section order. |
| `src/_base.html.j2`, `src/_macros.html.j2` | Shared layout and helpers. |
| `src/projects/*.html.j2` | Project pages (keep URLs `projects/*.html` stable). |
| `src/style.css`, `src/site.js` | Styling, research tabs, nav highlight, paper deep links. |
| `images/`, `data/` | Static assets copied as-is. `data/KushalKafle_CV.pdf` is the linked CV. |

Never edit `_site/` (generated, gitignored) and don't reintroduce a root `index.html`.

## Content conventions

- **BibTeX is copied, never generated.** Always paste the official BibTeX from the source (publisher or
  proceedings page, DBLP, arXiv, Google Scholar). Do not write or reconstruct entries yourself; only add
  the custom fields (`venue`, `topic`, `selected`, `thumb`, `arxiv`/`pdf`/`code`/`project`, ...).
- **Publications:** `topic` uses the tab ids in `build.py` `TOPICS` (`mllm`, `vlrep`, `gen`, `bias`,
  `vqa`). `selected = {true}` + `thumb` puts a paper in the Selected tab. Paper list entries have no
  stars or badges.
- **News:** no single-paper announcements (those belong in Research). Put links on the specific
  words (conference name -> conference site, role -> program committee page), not the whole
  sentence. Use `papers: [bibkeys]` for `[1] [2]` links that jump to and highlight the paper.
- **Transfers:** use time spans ("2023 – present"), not exact dates. `cv: highlight` gives a full
  CV entry; otherwise the card's `short` name goes on the CV's single "Other transfers" line.
  List fields are named `bullets` (Jinja treats `items`/`keys`/`values` as dict methods).
  Quote or `str()` YAML years; a bare `2025` loads as an int.
- **Wording:** plain, factual, no name-dropping of other models or datasets (e.g. avoid
  "X-style"), and no Adobe-internal code names or numbers (internal IDs, invention disclosure
  numbers, unreleased features). The public title on the site may be simpler than the exact
  internal level shown on the CV.
- **Facts:** verify roles and dates against official sources (e.g. conference ProgramCommittee
  pages) before adding them; don't overclaim (e.g. "worked with" vs "advised by").
- **Images:** use the author's own material or official Adobe/conference sources; crop out
  banners/UI chrome; keep thumbnails <= ~900px wide and compressed (animated WebP for short loops).

## CV (separate repo)

The CV is an Overleaf project cloned next to this repo (`../5bd0b56e375b3c171de23337`, remote on
git.overleaf.com). `main.tex` `\input`s the generated `pubs.tex` and `transfers.tex`; regenerate
them with `--cv-dir` instead of editing them. Build locally with
`tectonic -X compile main.tex --outdir /tmp/cvbuild` (US Letter, XeLaTeX/fontspec), then copy the
PDF to `data/KushalKafle_CV.pdf` and rebuild the site. `patents.tex` is a draft that is
intentionally not `\input`.

## Workflow preferences

- Website: preview locally and get the owner's OK before pushing; pushes to `master` deploy live.
- CV: small incremental commits pushed to Overleaf are fine.
- Commit identity for both repos: Kushal Kafle <kushalkafle@gmail.com> (set per repo).

## Backlog / ideas

Blog (Markdown posts in `src/posts/`, rendered via the base layout, optional RSS); detail pages
for highlighted tech transfers; optional interns/mentoring list; patents section (draft exists in
the CV repo).
