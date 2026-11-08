Source for my website, hosted at [kushalkafle.com](https://kushalkafle.com).

## Layout

| Path | What it is |
|---|---|
| `pubs.bib` | All publications (website **and** CV), as plain official BibTeX. |
| `src/papers.yml` | Website-only paper data: tabs, Selected, thumbnails, links, awards. |
| `src/news.yml` | News, newest first. Items can link to a page (`link`) and to papers (`papers: [bibkeys]` → [1] [2]). |
| `src/transfers.yml` | Tech Transfers cards (product, time span, description, links). |
| `src/site.yml` | Title shown in the header/About, and the highlighted banner (set `banner: null` to hide). |
| `src/_base.html.j2`, `src/_macros.html.j2` | Shared layout (head, nav, footer) and helpers used by every page. |
| `src/index.html.j2` | Home page (About text, section order, Misc). |
| `src/projects/*.html.j2` | Project pages (DVQA, TDIUC); built to `projects/*.html`. |
| `src/talks.yml` | Talks section, newest first (also in the CV). |
| `src/service.yml` | Service (site, CV, resume). |
| `src/cv.yml` | CV-only content (experience, education, interests, skills); `src/cv/*.tex.j2` and `src/cv.html.j2` are the CV/resume templates and the `/cv` page. |
| `src/interns.yml` | Internships and Mentoring section: one entry per internship (`year`, `name`, `homepage`), grouped by year on the page. |
| `src/style.css`, `src/site.js` | Styling and the research tabs. |
| `images/`, `data/`, `assets/` | Static files copied as-is (`data/` holds the generated CV and resume PDFs). |
| `build.py` | Renders everything into `_site/`. |

## Common tasks

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once

.venv/bin/python build.py                          # build into _site/
.venv/bin/python -m http.server 8000 -d _site      # preview at http://localhost:8000
```

- **Add a paper:** paste its official BibTeX at the top of the matching section in `pubs.bib`
  (`python3 tools/fetch_bib.py <arXiv id | DOI | proceedings URL>` fetches it), then add its `topic`
  (and `selected: true` + `thumb` to feature it) under the same key in `src/papers.yml`.
- **Add news:** add an item at the top of `src/news.yml`. Single-paper announcements belong in Research, not News.
- **Update the CV/resume:** edit the data files, then `.venv/bin/python build.py --pdf` rebuilds both PDFs into
  `data/` (needs [tectonic](https://tectonic-typesetting.github.io) and the Fontin `.otf` files in `fonts/`, which
  are not in git; get them from [exljbris](https://www.exljbris.com/fontin.html)). Any field can have `-cv` / `-resume`
  variants, and `hide: [site, cv, resume]` drops an item from an output.

Pushing to `master` builds and deploys via GitHub Actions (`.github/workflows/pages.yml`).
Repository Settings → Pages → Source must be set to **GitHub Actions**.
