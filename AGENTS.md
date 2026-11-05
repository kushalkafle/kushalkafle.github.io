# Agent guide for kushalkafle.com

Personal academic website of Kushal Kafle. A small Python static generator renders
`_site/`, which GitHub Actions deploys to GitHub Pages (custom domain via `CNAME`).

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python build.py                          # render into _site/
.venv/bin/python -m http.server 8000 -d _site      # preview at http://localhost:8000
.venv/bin/python build.py --cv-dir <cv-repo>       # also write <cv-repo>/pubs.tex and transfers.tex
python3 tools/fetch_bib.py <arXiv id | DOI | CVF/NeurIPS/ACL URL>   # official BibTeX + TO CHECK note
```

There are no tests. Verify changes by building, opening the preview (desktop and a ~390px
phone width), and checking that links and images resolve.

## Where things live

| Edit this | For |
|---|---|
| `pubs.bib` | All publications (site + CV), plain official BibTeX only. |
| `src/papers.yml` | Website-only paper data keyed by BibTeX key: tabs, Selected, thumbnails, links, awards. |
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

- **BibTeX is copied, never generated.** Copy each entry verbatim from the venue's official export
  (CVF Open Access, ACL Anthology, PMLR, NeurIPS proceedings, OpenReview, Springer/AAAI/publisher
  "export citation"). Use arXiv BibTeX only for papers that exist only on arXiv. Google Scholar blocks
  automated access; don't try to get around it (the owner can paste Scholar BibTeX themselves).
  - Every entry an agent copies gets a note on the line directly above it, and the owner reviews it once:
    `% TO CHECK (copied by agent) | source: <exact URL the BibTeX came from> | changes: <edits, or none>`
    The owner replaces it with `% Checked` after reviewing. Never mark an entry Checked yourself, and
    keep existing `% Checked` notes when editing an entry (switch back to TO CHECK if you change its
    standard fields).
  - `tools/fetch_bib.py` fetches official exports (CVF, ACL Anthology, Springer/ECCV, Frontiers, NeurIPS,
    arXiv) and prints the note line for you. AAAI is behind a bot check and BMVC/RIT have no export:
    ask the owner to paste those.
  - Springer's `year` is sometimes the print year; the conference year comes from its booktitle
    ("Computer Vision -- ECCV 2024"), so leave `year` as exported.
  - After copying, formatting edits are fine: protecting capitalization (`{DVQA}`), renaming keys, and
    dropping noise fields like `abstract`. Never add website fields to `pubs.bib`; they go in
    `src/papers.yml`.
  - Venue labels are derived from `booktitle`/`journal` (acronyms like "(CVPR)" or "ECCV 2024" are used
    directly). If the build warns about a new venue, add a row to `VENUE_LUT` in `build.py`.
  - The owner may hand-write BibTeX; agents (LLMs) may not. Entries the owner wrote, including those in
    this repo's git history (e.g. the BibTeX blocks in the pre-rebuild `index.html` and project pages),
    count as sources and can be copied.
  - An agent writing or reconstructing an entry needs the owner's explicit OK **for that specific
    entry**, marked with a `% TO CHECK: agent-written, source: <url>` comment.
- **Publications:** in `src/papers.yml`, `topic` uses the tab ids in `build.py` `TOPICS` (`mllm`, `vlrep`,
  `gen`, `bias`, `vqa`). `selected: true` + `thumb` puts a paper in the Selected tab. Paper list entries have no
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
