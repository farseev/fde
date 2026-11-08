#!/usr/bin/env python3
"""Site checker (stdlib only). Run from anywhere:  python3 tools/check_site.py
Checks every *.html page in the repo (except 404.html for canonical/hreflang). Pages without any
hreflang alternates are English-only (facilitator guide, thank-you page) and only need a canonical;
the root copies of the guide pages (session-*.html, people.html, data.html) canonicalise to /guide/.
  - exactly one <h1>
  - every JSON-LD block parses; FAQPage questions match visible <summary> text count
  - canonical present, absolute, self-referencing (URL maps to this file)
  - every hreflang alternate points to a file that exists, cluster includes self and x-default,
    and the cluster is identical (reciprocal) on every page it lists
  - <html lang> matches the page's own hreflang entry; dir="rtl" on Arabic
  - every internal href/src resolves to a file (and #anchors to an id on the target page)
  - sitemap.xml and every sitemap-*.xml parse as XML and every <loc> exists on disk
  - every page loads /track.js and (except 404) the GA4 tag
Exit code 1 on any error.
"""
import html, json, os, re, sys, glob
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://faithdriven.sg"
errors = []


def err(page, msg):
    errors.append("%s: %s" % (os.path.relpath(page, ROOT), msg))


def url_to_file(url):
    p = urlsplit(url)
    if p.netloc and p.netloc != "faithdriven.sg":
        return None
    path = unquote(p.path)
    f = os.path.join(ROOT, path.lstrip("/"))
    if path.endswith("/") or path == "":
        f = os.path.join(f, "index.html")
    return f


def file_to_url(f):
    rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    return SITE + "/" + rel


ids_cache = {}


def ids_of(f):
    if f not in ids_cache:
        try:
            ids_cache[f] = set(a or b for a, b in re.findall(r'\sid=(?:"([^"]+)"|([^\s>"\']+))', open(f, encoding="utf-8").read()))
        except OSError:
            ids_cache[f] = set()
    return ids_cache[f]


def main():
    pages = [p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
             if "/.git/" not in p and "/tools/" not in p and "/i18n/" not in p]
    clusters = {}
    for f in sorted(pages):
        h = open(f, encoding="utf-8").read()
        is404 = f.endswith("404.html")
        if "track.js" not in h:
            err(f, "track.js (GA4 events) missing")
        if not is404 and "G-4MDEPHJHBF" not in h:
            err(f, "GA4 tag missing")
        n = len(re.findall(r"<h1[\s>]", h))
        if n != 1:
            err(f, "%d <h1> elements" % n)
        faq_ld = 0
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                d = json.loads(m.group(1))
            except ValueError as e:
                err(f, "JSON-LD does not parse: %s" % e)
                continue
            if isinstance(d, dict) and d.get("@type") == "FAQPage":
                faq_ld = len(d["mainEntity"])
        if faq_ld and faq_ld != h.count("<summary>"):
            err(f, "FAQPage has %d questions, page shows %d" % (faq_ld, h.count("<summary>")))
        lang = re.search(r'<html lang="([^"]+)"', h)
        lang = lang.group(1) if lang else None
        if lang and lang.startswith("ar") and 'dir="rtl"' not in h[:300]:
            err(f, 'Arabic page without dir="rtl"')
        if not is404:
            c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
            alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', h)
            if not c:
                err(f, "no canonical")
            elif c.group(1) != file_to_url(f):
                t = url_to_file(c.group(1))
                if not t or not os.path.exists(t):
                    err(f, "canonical %s is not self and does not exist" % c.group(1))
                elif alts and sorted(alts) != sorted(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', open(t, encoding="utf-8").read())):
                    err(f, "canonical %s is not self and the hreflang cluster differs from it" % c.group(1))
                alts = []  # duplicate that canonicalises to another page: its cluster is that page's
            codes = dict(alts)
            if alts and "x-default" not in codes:
                err(f, "no x-default hreflang")
            if alts and file_to_url(f) not in codes.values():
                err(f, "hreflang cluster does not include self")
            elif alts and lang:
                own = [k for k, v in alts if v == file_to_url(f)]
                if not any(lang == k or lang.startswith(k + "-") for k in own):
                    err(f, "html lang %s does not match own hreflang entry %s" % (lang, own))
            for code, u in alts:
                t = url_to_file(u)
                if not t or not os.path.exists(t):
                    err(f, "hreflang %s -> missing %s" % (code, u))
            if alts:
                clusters[file_to_url(f)] = tuple(sorted(alts))
        # internal links
        for attr, u in re.findall(r'\s(href|src)="([^"]+)"', h):
            u = html.unescape(u)
            if re.match(r"^(https?:|mailto:|tel:|data:|//|javascript:)", u):
                if u.startswith(SITE):
                    t = url_to_file(u)
                    if t and not os.path.exists(t) and not os.path.splitext(t)[1] in (".xml", ".txt"):
                        if not os.path.exists(t):
                            err(f, "absolute link to missing %s" % u)
                continue
            path, _, frag = u.partition("#")
            if path == "":
                tgt = f
            else:
                base = ROOT if path.startswith("/") else os.path.dirname(f)
                tgt = os.path.normpath(os.path.join(base, unquote(path).lstrip("/")))
                if path.endswith("/") or os.path.isdir(tgt):
                    tgt = os.path.join(tgt, "index.html")
            if not os.path.exists(tgt):
                err(f, "broken link %s" % u)
            elif frag and tgt.endswith(".html") and frag not in ids_of(tgt):
                err(f, "missing anchor #%s in %s" % (frag, os.path.relpath(tgt, ROOT)))
    # reciprocity
    for url, cl in clusters.items():
        for code, u in cl:
            if code == "x-default":
                continue
            other = clusters.get(u)
            if other is not None and other != cl:
                err(url_to_file(url), "hreflang cluster differs from %s" % u)
                break
    # sitemaps
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for sm in glob.glob(os.path.join(ROOT, "sitemap*.xml")):
        try:
            t = ET.parse(sm)
        except ET.ParseError as e:
            err(sm, "XML does not parse: %s" % e)
            continue
        for loc in t.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            tf = url_to_file(loc.text)
            if not tf or not os.path.exists(tf):
                err(sm, "loc missing on disk: %s" % loc.text)
    for e in errors:
        print("ERROR", e)
    print("%d pages checked, %d errors" % (len(pages), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
