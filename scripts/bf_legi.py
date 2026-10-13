#!/usr/bin/env python3
"""Burkina Faso: texts from the former official legal portal LegiBurkina (www.legiburkina.bf, Secrétariat
général du Gouvernement et du Conseil des ministres), which is no longer reachable; Internet Archive captures
of the official pages/PDFs are used (the archived URL is recorded in each file).

Selected: the Constitution (consolidated PDF of 2012 and HTML version), the codes published as PDF/HTML,
and the laws ("Loi_...") published as HTML pages of the Journal officiel or as PDF.
Usage: python3 bf_legi.py [--no-download]"""
import os
import re
import sys
import time
import urllib.parse

import requests
from lxml import html as LH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bf_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "bf", "legi")
os.environ.setdefault("LC_TESSDATA", os.path.join(os.path.dirname(RAW), "tessdata"))
RETRIEVED = os.environ.get("LC_RETRIEVED", "2026-10-13")
WB = "https://web.archive.org/web/%sid_/%s"
DL = "--no-download" not in sys.argv
CODE_NAMES = {
    "CODE CIVIL": "code-civil", "CODE DE L'ENVIRONNEMENT": "code-de-l-environnement",
    "CODE DE L'INFORMATION": "code-de-l-information", "CODE DE SECURITE SOCIALE": "code-de-securite-sociale",
    "CODE DES IMPÔTS": "code-des-impots", "CODE DES PERSONNES ET DE LA FAMILLE": "code-des-personnes-et-de-la-famille",
    "CODE DU TRAVAIL": "code-du-travail", "CODE FONCIER": "code-foncier", "CODE MINIER": "code-minier",
    "CODE PENAL": "code-penal",
}


def cdx_rows():
    path = os.path.join(RAW, "cdx_full.txt")
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        s = requests.Session()
        s.headers["User-Agent"] = T.UA
        url = ("https://web.archive.org/cdx/search/cdx?url=legiburkina.bf&matchType=domain&output=txt"
               "&filter=statuscode:200&fl=original,timestamp,length,mimetype&limit=200000")
        for i in range(5):
            try:
                r = s.get(url, timeout=600)
                r.raise_for_status()
                break
            except Exception as e:  # noqa
                print("retry", e)
                time.sleep(30)
        open(path, "w").write(r.text)
    best = {}
    for line in open(path):
        p = line.split()
        if len(p) < 4 or not p[2].isdigit() or int(p[2]) < 800:
            continue
        key = re.sub(r"^https?://(www\.)?legiburkina\.bf(:80)?", "", p[0]).lower()
        if key not in best or p[1] > best[key][1]:
            best[key] = (p[0], p[1], p[3])
    return best


def select(best):
    out = []
    for key, (orig, ts, mime) in best.items():
        name = urllib.parse.unquote(key.rsplit("/", 1)[-1]).split("?")[0]
        if key.startswith("/documents/code") and key.endswith(".pdf"):
            out.append(("code", orig, ts))
        elif key in ("/sitepages/constitution/c-2012.pdf",):
            out.append(("constitution", orig, ts))
        elif key.startswith("/codes/") and key.endswith(".htm") and not re.search(r"(sommaire|affichage|cadre)_codes", key):
            out.append(("code-htm", orig, ts))
        elif re.match(r"^loi[_ ]", name) and (name.endswith(".htm") or name.endswith(".pdf")):
            out.append(("loi", orig, ts))
    return sorted(out)


def htm_lines(path):
    raw = open(path, "rb").read()
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000])
    enc = (m.group(1).decode() if m else "windows-1252").lower()
    try:
        txt = raw.decode("utf-8") if enc == "utf-8" else raw.decode("windows-1252" if enc in ("iso-8859-1", "windows-1252") else enc)
    except (UnicodeDecodeError, LookupError):
        txt = raw.decode("windows-1252", "replace")
    doc = LH.fromstring(txt)
    for bad in doc.xpath("//script|//style|//head"):
        bad.getparent().remove(bad)
    for b in doc.xpath("//br"):
        b.tail = "\n" + (b.tail or "")
    out = []
    for el in doc.xpath("//p|//h1|//h2|//h3|//h4|//h5|//h6|//li|//tr"):
        if el.xpath("ancestor::p|ancestor::li"):
            continue
        for ln in el.text_content().split("\n"):
            out.append(T.norm(ln))
        out.append("")
    if sum(len(x) for x in out) < 200:
        out = [T.norm(x) for x in doc.text_content().split("\n")]
    return out


MONTHS = {"janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
          "aout": 8, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12}


def main():
    best = cdx_rows()
    sel = select(best)
    print("selected", len(sel), flush=True)
    used = {}
    n = 0
    for kind, orig, ts in sel:
        fn = urllib.parse.unquote(orig.rsplit("/", 1)[-1]).split("?")[0]
        dest = os.path.join(RAW, "files", T.slug(fn.rsplit(".", 1)[0], 100) + "." + fn.rsplit(".", 1)[-1].lower())
        if DL:
            T.fetch(WB % (ts, orig), dest, delay=3, check_pdf=dest.endswith(".pdf"), timeout=300)
        if not os.path.exists(dest) or (dest.endswith(".pdf") and not T.pdf_ok(dest)):
            print("MISSING/BAD", orig, flush=True)
            continue
        if dest.endswith(".pdf"):
            pages, ocr = T.pdf_text(dest, "fra", tmpdir=RAW)
            lines = T.clean_pages(pages)
        else:
            lines, ocr = htm_lines(dest), False
        nz = [x for x in lines if x]
        if sum(len(x) for x in nz) < 300:
            print("SHORT", orig, flush=True)
            continue
        head = next((x for x in nz[:40] if re.match(r"^(LOI|Loi|loi)\s+(ORGANIQUE|organique|CONSTITUTIONNELLE|constitutionnelle)?\s*N", x)), None)
        num, date = None, None
        if head:
            m = re.search(r"N\s*[°o]\s*0*(\d{1,3}\s*[-–]\s*\d{4})\s*/?\s*([A-Z]+)?", head, re.I)
            if m:
                a, b = re.sub(r"\s", "", m.group(1)).replace("–", "-").split("-")
                num = "%03d-%s" % (int(a), b) + ("/" + m.group(2).upper() if m.group(2) else "")
            d = re.search(r"du\s+(\d{1,2})(?:er)?\s+([a-zéû]+)\s+(\d{4})", head, re.I)
            if d and d.group(2).lower() in MONTHS:
                date = "%s-%02d-%02d" % (d.group(3), MONTHS[d.group(2).lower()], int(d.group(1)))
        if kind == "code":
            cname = re.sub(r"\.pdf$", "", fn, flags=re.I).upper()
            title = cname.capitalize()
            rel = "codes/%s.md" % CODE_NAMES.get(cname, T.slug(cname))
            typ = "code"
        elif kind == "constitution":
            title = "Constitution du Burkina Faso (texte de 2012)"
            rel = "constitution/constitution-1991-version-2012.md"
            typ = "constitution"
        elif kind == "code-htm":
            title = nz[0][:200]
            rel = "codes/legiburkina-htm/%s.md" % T.slug(fn.rsplit(".", 1)[0])
            typ = "code" if "constitution" not in fn.lower() else "constitution"
            if typ == "constitution":
                rel = "constitution/%s-htm.md" % T.slug(fn.rsplit(".", 1)[0])
        else:
            title = head or nz[0][:200]
            m = re.search(r"loi_(?:[a-z]+_)?(\d{4})_0*(\d+)", fn, re.I)
            year = date[:4] if date else (m.group(1) if m else "undated")
            base = ("loi-" + num.replace("/", "-").lower()) if num else ("loi-%s-%s" % (m.group(2), m.group(1)) if m else T.slug(fn))
            rel = "lois/%s/%s.md" % (year, base)
            typ = "act"
        if rel in used:
            continue  # same law captured under several URLs: keep the first
        tgt = os.path.join(REPO, rel)
        if os.path.exists(tgt) and "assembleenationale.bf" in open(tgt, encoding="utf-8").read(3000):
            print("SKIP (Assemblée version kept)", rel, flush=True)
            continue
        used[rel] = orig
        body = T.structure(lines, "fr")
        meta = {"title": title, "identifier": ("Loi n° " + num) if num else None, "type": typ, "jurisdiction": "bf",
                "language": "fr", "date": date, "status": "unknown", "source": orig,
                "archived_source": "https://web.archive.org/web/%s/%s" % (ts, orig), "retrieved": RETRIEVED,
                "note": ("Text from the former official portal LegiBurkina (capture of %s-%s-%s); may be outdated" % (ts[:4], ts[4:6], ts[6:8]))
                + ("; OCR" if ocr else "")}
        T.write_md(os.path.join(REPO, rel), meta, title, body)
        n += 1
        print("OK", rel, flush=True)
    print("written", n)


if __name__ == "__main__":
    main()
