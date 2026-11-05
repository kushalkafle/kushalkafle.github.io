Source for my website, hosted at [kushalkafle.com](https://kushalkafle.com).

## Layout

| Path | What it is |
|---|---|
| `pubs.bib` | All publications (website **and** CV). Custom fields are documented at the top of the file. |
| `src/news.yml` | News, newest first. Items can link to a page (`link`) and to papers (`papers: [bibkeys]` → [1] [2]). |
| `src/transfers.yml` | Tech Transfers cards (product, time span, description, links). |
| `src/site.yml` | Title shown in the header/About, and the highlighted banner (set `banner: null` to hide). |
| `src/_base.html.j2`, `src/_macros.html.j2` | Shared layout (head, nav, footer) and helpers used by every page. |
| `src/index.html.j2` | Home page (About text, section order, Misc). |
| `src/projects/*.html.j2` | Project pages (DVQA, TDIUC); built to `projects/*.html`. |
| `src/talks.yml` | Talks section, newest first. |
| `src/style.css`, `src/site.js` | Styling and the research tabs. |
| `images/`, `data/` | Static files copied as-is (`data/KushalKafle_CV.pdf` is the linked CV). |
| `build.py` | Renders everything into `_site/`. |

## Common tasks

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once

.venv/bin/python build.py                          # build into _site/
.venv/bin/python -m http.server 8000 -d _site      # preview at http://localhost:8000
```

- **Add a paper:** add an entry to the top of the matching section in `pubs.bib`. Set `topic`, plus
  `selected = {true}` and a `thumb` image if it should appear in the ★ Selected tab.
- **Add news:** add an item at the top of `src/news.yml`. Single-paper announcements belong in Research, not News.
- **Update the CV:** `.venv/bin/python build.py --cv-dir <overleaf-repo>` regenerates `pubs.tex` (from `pubs.bib`)
  and `transfers.tex` (from `src/transfers.yml`); then commit/push the Overleaf repo (its `main.tex` `\input`s both).

Pushing to `master` builds and deploys via GitHub Actions (`.github/workflows/pages.yml`).
Repository Settings → Pages → Source must be set to **GitHub Actions**.
