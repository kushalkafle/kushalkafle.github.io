#!/usr/bin/env python3
"""Fetch the official BibTeX for a paper, ready to paste into pubs.bib.

    python3 tools/fetch_bib.py 2509.01610                      # arXiv id (arXiv-only papers)
    python3 tools/fetch_bib.py 10.18653/v1/2020.acl-main.727  # DOI (ACL, Springer/ECCV, AAAI, Frontiers, CVF)
    python3 tools/fetch_bib.py https://openaccess.thecvf.com/content/CVPR2024/html/...html
    python3 tools/fetch_bib.py https://proceedings.neurips.cc/paper_files/paper/2020/hash/...-Abstract.html

The entry is printed verbatim from the source, preceded by the review note required by AGENTS.md:
    % TO CHECK (copied by agent) | source: <url> | changes: none
Only stdlib is used. If a source has no machine-readable export (e.g. Elsevier), it says so; ask the
owner to paste the BibTeX instead of writing it yourself.
"""
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) kushalkafle-site-fetch-bib"


def get(url, accept=None):
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=40) as r:
        return r.read().decode("utf-8", "replace"), r.geturl()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", html.unescape(s).lower())


def from_arxiv(aid):
    url = f"https://arxiv.org/bibtex/{aid}"
    return get(url)[0], url


def from_acl(anthology_id):
    url = f"https://aclanthology.org/{anthology_id}.bib"
    return get(url)[0], url


def from_springer(doi):
    url = f"https://citation-needed.springer.com/v2/references/{doi}?format=bibtex&flavour=citation"
    return get(url)[0], url


def from_aaai(doi):
    page, landing = get(f"https://doi.org/{doi}")
    if "not a bot" in page:
        raise SystemExit(f"AAAI is behind a bot check; don't bypass it. Ask the owner to paste the BibTeX "
                         f"from https://doi.org/{doi}")
    m = re.search(r"/article/view/(\d+)", landing) or re.search(r"/article/view/(\d+)", page)
    if not m:
        raise SystemExit(f"could not find the AAAI article id for {doi}")
    url = f"https://ojs.aaai.org/index.php/AAAI/citationstylelanguage/download/bibtex?submissionId={m.group(1)}"
    return get(url)[0], url


def from_frontiers(doi):
    _, landing = get(f"https://doi.org/{doi}")
    url = re.sub(r"/(full|abstract)?$", "", landing.split("?")[0]) + "/bibTex"
    return get(url)[0], url


def from_cvf_page(url):
    page, url = get(url)
    m = re.search(r'<div class="bibref[^"]*">(.*?)</div>', page, re.S)
    if not m:
        raise SystemExit(f"no BibTeX block on {url}")
    return html.unescape(re.sub(r"<br\s*/?>", "\n", m.group(1))).strip(), url


def cvf_listing_pages(conf):
    base = f"https://openaccess.thecvf.com/{conf}"
    page, _ = get(base + "?day=all")
    if page.count('class="ptitle"') > 20:
        return [page]
    page, _ = get(base)
    pages = [page]
    for day_link in sorted(set(re.findall(rf'href="/?({conf}(?:\.py)?\?day=[0-9-]+)"', page))):
        pages.append(get(f"https://openaccess.thecvf.com/{day_link}")[0])
    return pages


def cvpr_workshop_pages(year):
    menu, _ = get(f"https://openaccess.thecvf.com/CVPR{year}_workshops/menu")
    links = sorted(set(re.findall(r'href="(/?CVPR' + year + r'_workshops/[^"]+)"', menu)))
    return [get("https://openaccess.thecvf.com/" + h.lstrip("/"))[0] for h in links if not h.endswith("menu")]


def from_cvf_doi(doi):
    m = re.match(r"10\.1109/(CVPRW|CVPR|ICCV|WACV)[0-9]*\.(\d{4})", doi, re.I)
    conf, year = m.group(1).upper(), m.group(2)
    meta = json.loads(get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")[0])["message"]
    want = norm(meta["title"][0])
    pages = cvpr_workshop_pages(year) if conf == "CVPRW" else cvf_listing_pages(f"{conf}{year}")
    for page in pages:
        for href, title in re.findall(r'<dt class="ptitle"><br><a href="([^"]+)">(.*?)</a>', page, re.S):
            if norm(re.sub(r"<[^>]+>", "", title)) == want:
                return from_cvf_page("https://openaccess.thecvf.com/" + href.lstrip("/"))
    raise SystemExit(f"'{meta['title'][0]}' not found on CVF Open Access ({conf} {year})")


def from_neurips_page(url):
    page, url = get(url)
    m = re.search(r'href="([^"]*(?:-Bibtex\.bib|/bibtex))"', page, re.I)
    if not m:
        raise SystemExit(f"no BibTeX link on {url}")
    bib_url = urllib.parse.urljoin(url, m.group(1))
    return get(bib_url)[0], bib_url


def fetch(ref):
    ref = ref.strip()
    if ref.startswith("http"):
        if "openaccess.thecvf.com" in ref:
            return from_cvf_page(ref)
        if "neurips.cc" in ref or "nips.cc" in ref:
            return from_neurips_page(ref)
        if "aclanthology.org" in ref:
            return from_acl(ref.rstrip("/").rsplit("/", 1)[-1])
        if "arxiv.org" in ref:
            return from_arxiv(re.sub(r"v\d+$", "", ref.rstrip("/").rsplit("/", 1)[-1]))
        raise SystemExit(f"no exporter for {ref}; ask the owner to paste the BibTeX")
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", ref):
        return from_arxiv(re.sub(r"v\d+$", "", ref))
    doi = ref.removeprefix("doi:").removeprefix("https://doi.org/")
    if doi.startswith("10.18653/v1/"):
        return from_acl(doi.split("/", 2)[2])
    if doi.startswith("10.1007/"):
        return from_springer(doi)
    if doi.startswith("10.1609/"):
        return from_aaai(doi)
    if doi.startswith("10.3389/"):
        return from_frontiers(doi)
    if re.match(r"10\.1109/(CVPRW|CVPR|ICCV|WACV)", doi, re.I):
        return from_cvf_doi(doi)
    raise SystemExit(f"no official exporter for {doi}; ask the owner to paste the BibTeX")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    bib, url = fetch(sys.argv[1])
    if not bib.lstrip().startswith("@"):
        raise SystemExit(f"{url} did not return BibTeX")
    print(f"% TO CHECK (copied by agent) | source: {url} | changes: none")
    print(bib.strip())


if __name__ == "__main__":
    main()
