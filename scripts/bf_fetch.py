#!/usr/bin/env python3
"""Burkina Faso: laws promulgated, as published by the Assemblée législative de transition /
Assemblée nationale (https://www.assembleenationale.bf/loip, "Lois promulguées").
Each law page links the law PDF (/storage/Loi/...). Extra documents (constitution, charter)
are listed in EXTRA.
Usage: python3 bf_fetch.py [--no-download] [--download-only]"""
import html
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bf_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "bf")
BASE = "https://www.assembleenationale.bf/"
RETRIEVED = os.environ.get("LC_RETRIEVED", "2026-10-13")
os.environ.setdefault("LC_TESSDATA", os.path.join(RAW, "tessdata"))
DL = "--no-download" not in sys.argv
EXTRA = []  # (url, record page, title, kind)

MONTHS = {"janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
          "aout": 8, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12}


def page(url, dest):
    if DL:
        T.fetch(url, dest, delay=2)
    return open(dest, encoding="utf-8", errors="replace").read() if os.path.exists(dest) else ""


def listing():
    out = []
    p = 1
    last = 1
    while p <= last:
        s = page(BASE + "loip" + ("?page=%d" % p if p > 1 else ""), os.path.join(RAW, "list", "%d.html" % p))
        last = max([last] + [int(x) for x in re.findall(r"loip\?page=(\d+)", s)])
        for m in re.finditer(r'<a href="https://www\.assembleenationale\.bf/(loip/\d+)"[^>]*>\s*(.*?)\s*</a>\s*</td>\s*<td[^>]*>\s*([\d/]+)', s, re.S):
            t = html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", "", m.group(2)))).strip()
            if m.group(1) not in [o[0] for o in out]:
                out.append((m.group(1), t, m.group(3)))
        p += 1
    return out


def parse_title(t):
    m = re.search(r"(?:Loi|LOI)\s+(organique\s+|constitutionnelle\s+)?n\s*[°o]\s*([0-9]{2,4}\s*[-–]\s*[0-9]{4})\s*/?\s*([A-Z]+)?\s*du\s+(\d{1,2})(?:er)?\s+([a-zéû]+)\s+(\d{4})", t, re.I)
    if not m:
        return None, None, None
    num = re.sub(r"\s", "", m.group(2)).replace("–", "-") + ("/" + m.group(3) if m.group(3) else "")
    d = None
    if m.group(5).lower() in MONTHS:
        d = "%s-%02d-%02d" % (m.group(6), MONTHS[m.group(5).lower()], int(m.group(4)))
    kind = (m.group(1) or "").strip().lower()
    return num, d, kind


def main():
    laws = listing()
    print("laws", len(laws), flush=True)
    used = {}
    n = 0
    for rec, title, dstr in laws:
        s = page(BASE + rec, os.path.join(RAW, "rec", rec.replace("/", "-") + ".html"))
        m = re.search(r'href="(/storage/Loi/[^"]+\.pdf)"', s, re.I)
        if not m:
            print("NOPDF", rec, title, flush=True)
            continue
        url = urllib.parse.urljoin(BASE, m.group(1))
        dest = os.path.join(RAW, "pdf", rec.replace("/", "-") + ".pdf")
        if DL:
            T.fetch(url, dest, delay=2, check_pdf=True, timeout=300)
        if not os.path.exists(dest) or not T.pdf_ok(dest):
            print("MISSING/BAD", url, flush=True)
            continue
        if "--download-only" in sys.argv:
            continue
        pages, ocr = T.pdf_text(dest, "fra", tmpdir=RAW)
        lines = T.clean_pages(pages)
        body = T.structure(lines, "fr")
        if sum(len(x) for x in body) < 200:
            print("SHORT", rec, title, flush=True)
            continue
        num, date, kind = parse_title(title)
        if not date:
            dm = re.match(r"(\d{2})/(\d{2})/(\d{4})", dstr or "")
            date = "%s-%s-%s" % (dm.group(3), dm.group(2), dm.group(1)) if dm else None
        cat, typ = {"organique": ("lois-organiques", "organic_law"),
                    "constitutionnelle": ("lois-constitutionnelles", "constitutional_law")}.get(kind, ("lois", "act"))
        year = (date or "undated")[:4]
        base = ("loi-" + num.replace("/", "-").lower()) if num else T.slug(title, 80)
        rel = "%s/%s/%s.md" % (cat, year, base)
        if rel in used:
            rel = rel[:-3] + "-" + rec.split("/")[1] + ".md"
        used[rel] = 1
        meta = {"title": title, "identifier": ("Loi n° " + num) if num else None, "type": typ, "jurisdiction": "bf",
                "language": "fr", "date": date, "status": "unknown", "source": url, "record": BASE + rec,
                "retrieved": RETRIEVED,
                "note": "Text as published by the Assemblée (as enacted)" + ("; OCR" if ocr else "")}
        T.write_md(os.path.join(REPO, rel), meta, title, body)
        n += 1
        print("OK", rel, flush=True)
    print("written", n)


if __name__ == "__main__":
    main()
