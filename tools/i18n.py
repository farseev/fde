#!/usr/bin/env python3
"""Faith Driven Singapore (faithdriven.sg) multilingual build — standard library only.

Adapted from exostride.sg tools/i18n.py. English pages at the site root are the template and the
source text. Every translatable piece of text (visible text runs, alt/aria/title attributes, meta
descriptions, OG/Twitter text, JSON-LD text) is a *segment*, keyed by a hash of its English text.
Translations live in i18n/<code>.json ({id: text}); i18n/source.json holds the English.

Commands
  python3 tools/i18n.py extract                 refresh i18n/source.json + i18n/pages.json
  python3 tools/i18n.py todo <code> [page ...]  print untranslated segments as  id<TAB>English
  python3 tools/i18n.py merge <code> <file>     merge  id<TAB>translation  lines (placeholders checked)
  python3 tools/i18n.py build                   render every language page that is 100% translated,
                                                hreflang clusters, switchers, sitemaps, llms.txt
  python3 tools/i18n.py status                  coverage per language

Translated pages: home, /our-story/, /voices/, /gatherings/, /articles/ and the 10 articles.
English-only (research documents / funnel pages): /guide/ (facilitator guide, session, people and
data pages), the root session-*.html / people.html / data.html copies (canonical -> /guide/),
/thank-you-giving/ and 404.html.

Existing hand-made language pages (/zh/, /ms/, /ta/ and any page whose translation went stale) are
KEPT as they are — only their <head> hreflang/og:locale, language switchers and "Also available in"
links are refreshed — until every segment of the page is in the translation memory; from then on
the page is rendered from the English template like every other language.

Inline markup inside a segment appears as <g1>…</g1> (paired tags) and <x1/> (void tags).
"""
import hashlib, html, json, os, re, sys, glob, posixpath
from html.parser import HTMLParser
from urllib.parse import quote, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://faithdriven.sg"
I18N = os.path.join(ROOT, "i18n")
TODAY = "2026-11-08"

# code, url dir, hreflang, <html lang>, og:locale, native name, short label, "Language" label, extra Google font
LANGS = [
    ("en", "", "en", "en-SG", "en_SG", "English", "EN", "Language", None),
    ("zh-hans", "zh", "zh-Hans", "zh-Hans-SG", "zh_SG", "简体中文", "简中", "语言", None),
    ("ms", "ms", "ms", "ms-SG", "ms_SG", "Bahasa Melayu", "BM", "Bahasa", None),
    ("ta", "ta", "ta", "ta-SG", "ta_SG", "தமிழ்", "தமிழ்", "மொழி", None),
    ("zh-hant", "zh-hant", "zh-Hant", "zh-Hant", "zh_TW", "繁體中文", "繁中", "語言", "Noto+Sans+TC:wght@400;500;700;900"),
    ("ja", "ja", "ja", "ja", "ja_JP", "日本語", "日本語", "言語", "Noto+Sans+JP:wght@400;500;700;900"),
    ("ko", "ko", "ko", "ko", "ko_KR", "한국어", "한국어", "언어", "Noto+Sans+KR:wght@400;500;700;900"),
    ("th", "th", "th", "th", "th_TH", "ไทย", "ไทย", "ภาษา", "Noto+Sans+Thai:wght@400;500;700;900"),
    ("vi", "vi", "vi", "vi", "vi_VN", "Tiếng Việt", "VI", "Ngôn ngữ", None),
    ("id", "id", "id", "id", "id_ID", "Bahasa Indonesia", "ID", "Bahasa", None),
    ("hi", "hi", "hi", "hi", "hi_IN", "हिन्दी", "हिन्दी", "भाषा", "Noto+Sans+Devanagari:wght@400;500;700;900"),
    ("fil", "fil", "fil", "fil", "tl_PH", "Filipino", "FIL", "Wika", None),
    ("es", "es", "es", "es", "es_ES", "Español", "ES", "Idioma", None),
    ("fr", "fr", "fr", "fr", "fr_FR", "Français", "FR", "Langue", None),
    ("de", "de", "de", "de", "de_DE", "Deutsch", "DE", "Sprache", None),
    ("pt", "pt", "pt", "pt", "pt_BR", "Português", "PT", "Idioma", None),
    ("ar", "ar", "ar", "ar", "ar_AR", "العربية", "عربي", "اللغة", "Noto+Sans+Arabic:wght@400;500;700;900"),
    ("ru", "ru", "ru", "ru", "ru_RU", "Русский", "RU", "Язык", "Noto+Sans:wght@400;500;700;900"),
]
L = {l[0]: dict(code=l[0], dir=l[1], hreflang=l[2], html=l[3], og=l[4], name=l[5], short=l[6], label=l[7], font=l[8])
     for l in LANGS}
CODES = [l[0] for l in LANGS]
SETLANG = {c: (L[c]["dir"] or "en") for c in CODES}          # data-setlang / localStorage value
LEGACY = ("zh-hans", "ms", "ta")                              # languages that existed before this tool
PILL = {"zh-hans": "中文"}                                     # labels of the original 4-language pill switcher
SUFFIX = " | Faith Driven Singapore"
SUFFIX_KEY = "| Faith Driven Singapore"
SHARED_FRAGS = {"organization", "website", "aleks-farseev", "org"}
SKIP_LD_TYPES = {"Organization", "NGO", "WebSite", "Person", "Place", "Country", "ContactPoint", "PostalAddress"}

INLINE = {"a", "abbr", "b", "br", "code", "em", "i", "mark", "q", "s", "small", "span", "strong", "sub", "sup",
          "time", "u", "wbr", "img", "cite", "dfn", "kbd", "var", "bdi", "bdo"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "param"}
SKIP = {"script", "style", "svg", "noscript", "template"}
ATTRS = ("alt", "title", "aria-label", "placeholder")
META_NAMES = {"description", "twitter:title", "twitter:description", "twitter:image:alt", "apple-mobile-web-app-title"}
META_PROPS = {"og:title", "og:description", "og:image:alt", "article:section"}
LD_TEXT_KEYS = {"name", "headline", "description", "abstract", "text", "articleSection", "caption",
                "alternativeHeadline", "disambiguatingDescription", "educationalLevel", "timeRequired", "about_text"}
NAMES = ("Faith Driven Singapore", "Faith Driven SG", "Faith Driven Entrepreneur", "FDE", "FDE Singapore", "FDE Asia",
         "BLOCK71", "Suntec", "Browzwear", "Marina One", "YMCA", "Kampung Siglap", "Henry Kaestner", "Aleks Farseev",
         "SOMIN", "Grab", "Endowus", "New Taipei Kings", "Human Nature", "Salt&Light", "Forbes", "YouTube", "WhatsApp",
         "Eventbrite", "FAITH DRI", "EN", "SINGAPORE", "Faith Driven Singapore — Articles", "llms.txt")
KEEP_RE = re.compile(r"^(?:" + "|".join(re.escape(n) for n in NAMES) + r"|[\d\s.,:;+×x–\-−%°~<>/()·$#|→←↓↑…'\"]*[MKk]?\+?[\d\s.,:+%]*)$")
PH_RE = re.compile(r"</?g\d+>|<x\d+/>")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def sid(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def norm(s):
    return re.sub(r"[ \t\n\r\f\v]+", " ", s).strip(" \t\n\r\f\v")


def translatable(t):
    return bool(t) and bool(re.search(r"[^\W\d_]", t)) and not KEEP_RE.match(t)


# ---------------------------------------------------------------- parsing
class Tok:
    __slots__ = ("kind", "tag", "attrs", "start", "end", "raw", "el")

    def __init__(self, kind, tag, attrs, start):
        self.kind, self.tag, self.attrs, self.start, self.end, self.raw, self.el = kind, tag, attrs, start, None, None, None


class El:
    __slots__ = ("tag", "attrs", "open", "close", "children", "parent")

    def __init__(self, tag, attrs, open_i, parent):
        self.tag, self.attrs, self.open, self.close, self.children, self.parent = tag, dict(attrs), open_i, None, [], parent


class Parser(HTMLParser):
    def __init__(self, doc):
        super().__init__(convert_charrefs=False)
        self.lines = [0]
        for m in re.finditer("\n", doc):
            self.lines.append(m.end())
        self.toks = []

    def off(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def add(self, kind, tag=None, attrs=()):
        self.toks.append(Tok(kind, tag, attrs, self.off()))

    def handle_starttag(self, tag, attrs): self.add("start", tag, attrs)
    def handle_startendtag(self, tag, attrs): self.add("startend", tag, attrs)
    def handle_endtag(self, tag): self.add("end", tag)
    def handle_data(self, d): self.add("data")
    def handle_entityref(self, n): self.add("data")
    def handle_charref(self, n): self.add("data")
    def handle_comment(self, d): self.add("other")
    def handle_decl(self, d): self.add("other")
    def handle_pi(self, d): self.add("other")
    def unknown_decl(self, d): self.add("other")


def parse(doc):
    p = Parser(doc)
    p.feed(doc)
    p.close()
    toks = p.toks
    for i, t in enumerate(toks):
        t.end = toks[i + 1].start if i + 1 < len(toks) else len(doc)
        t.raw = doc[t.start:t.end]
    root = El("#root", (), -1, None)
    cur = root
    for i, t in enumerate(toks):
        if t.kind in ("start", "startend"):
            el = El(t.tag, t.attrs, i, cur)
            t.el = el
            cur.children.append(("el", el))
            if t.kind == "start" and t.tag not in VOID:
                cur = el
            else:
                el.close = i
        elif t.kind == "end":
            x = cur
            while x is not root and x.tag != t.tag:
                x = x.parent
            if x is not root:
                x.close = i
                cur = x.parent
        elif t.kind == "data":
            cur.children.append(("tok", i))
    return toks, root


# ---------------------------------------------------------------- segmentation
class Seg:
    __slots__ = ("kind", "text", "id", "a", "b", "tags", "lead", "trail", "suffix", "tok", "attr")


def text_of_children(toks, children, tagmap):
    out = []

    def ser(kind, x):
        if kind == "tok":
            out.append(html.unescape(toks[x].raw))
        else:
            n = len(tagmap) + 1
            if x.close is None or x.close == x.open or x.tag in VOID:
                tagmap.append(("x", x.open, None))
                out.append("<x%d/>" % n)
            else:
                tagmap.append(("g", x.open, x.close))
                out.append("<g%d>" % n)
                for c in x.children:
                    ser(*c)
                out.append("</g%d>" % n)
    for c in children:
        ser(*c)
    return "".join(out)


def is_inline(child):
    kind, x = child
    return kind == "tok" or (x.tag in INLINE and x.attrs.get("translate") != "no")


def has_direct_text(toks, run):
    return any(k == "tok" and toks[x].raw.strip() for k, x in run)


def segments(doc):
    toks, root = parse(doc)
    segs = []

    def visit(el):
        if el.tag in SKIP or el.attrs.get("translate") == "no":
            return
        runs, run = [], []
        for c in el.children:
            if is_inline(c) and not (c[0] == "el" and c[1].tag in SKIP):
                run.append(c)
            else:
                if run:
                    runs.append(("run", run)); run = []
                runs.append(("blk", c))
        if run:
            runs.append(("run", run))
        for kind, r in runs:
            if kind == "blk":
                if r[0] == "el":
                    visit(r[1])
                continue
            if has_direct_text(toks, r):
                make_run_seg(r)
            else:
                for k, x in r:
                    if k == "el":
                        visit(x)

    def first_tok(c):
        return c[1] if c[0] == "tok" else c[1].open

    def last_tok(c):
        return c[1] if c[0] == "tok" else (c[1].close if c[1].close is not None else c[1].open)

    def make_run_seg(r):
        while r and r[0][0] == "tok" and not toks[r[0][1]].raw.strip():
            r = r[1:]
        while r and r[-1][0] == "tok" and not toks[r[-1][1]].raw.strip():
            r = r[:-1]
        if not r:
            return
        tagmap = []
        raw_text = text_of_children(toks, r, tagmap)
        a, b = toks[first_tok(r[0])].start, toks[last_tok(r[-1])].end
        lead = re.match(r"\s*", doc[a:b]).group(0)
        trail = re.search(r"\s*$", doc[a:b]).group(0)
        t = norm(raw_text)
        s = Seg()
        s.kind, s.a, s.b, s.tags, s.lead, s.trail, s.tok, s.attr = "run", a, b, tagmap, lead, trail, None, None
        s.suffix = ""
        if t.endswith(SUFFIX) and not tagmap:
            t, s.suffix = t[: -len(SUFFIX)], SUFFIX
        s.text = t
        s.id = sid(t) if translatable(PH_RE.sub("", t)) else None
        segs.append(s)

    visit(root)
    for i, t in enumerate(toks):
        if t.kind not in ("start", "startend") or t.tag in ("link", "script", "iframe"):
            continue
        at = dict(t.attrs)
        names = [a for a in ATTRS if at.get(a) and not (t.tag == "meta")]
        if t.tag == "meta" and at.get("content") and (at.get("name") in META_NAMES or at.get("property") in META_PROPS):
            names.append("content")
        if t.tag == "a" and at.get("href", "").startswith("https://wa.me/") and "?text=" in at.get("href", ""):
            names.append("wa")
        for a in names:
            val = unquote(at["href"].split("?text=", 1)[1]) if a == "wa" else at[a]
            val = norm(val)
            s = Seg()
            s.kind, s.tok, s.attr, s.tags, s.lead, s.trail, s.a, s.b = "attr", i, a, [], "", "", None, None
            s.suffix = ""
            if val.endswith(SUFFIX):
                val, s.suffix = val[: -len(SUFFIX)], SUFFIX
            s.text = val
            s.id = sid(val) if translatable(val) else None
            segs.append(s)
    for i, t in enumerate(toks):
        if t.kind == "start" and t.tag == "script" and dict(t.attrs).get("type") == "application/ld+json":
            d = json.loads(toks[i + 1].raw)
            for val in ld_texts(d):
                s = Seg()
                s.kind, s.tok, s.attr, s.tags, s.lead, s.trail, s.a, s.b, s.suffix = "ld", i + 1, None, [], "", "", None, None, ""
                s.text = val
                s.id = sid(val) if translatable(val) else None
                segs.append(s)
    return toks, segs


def ld_skip(d):
    t = d.get("@type")
    ts = t if isinstance(t, list) else [t]
    return any(x in SKIP_LD_TYPES for x in ts)


def ld_texts(d, skip=False):
    out = []
    if isinstance(d, dict):
        skip = skip or ld_skip(d)
        for k, v in d.items():
            if isinstance(v, str):
                if not skip and k in LD_TEXT_KEYS:
                    v2 = v[: -len(SUFFIX)] if v.endswith(SUFFIX) else v
                    out.append(norm(v2))
            elif k != "keywords":
                out += ld_texts(v, skip)
    elif isinstance(d, list):
        for v in d:
            out += ld_texts(v, skip)
    return out


# ---------------------------------------------------------------- pages
def en_pages():
    pages = ["index.html", "our-story/index.html", "voices/index.html", "gatherings/index.html", "articles/index.html"]
    pages += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "articles", "*", "index.html")))
    return pages


def page_path(rel):
    return "/" + rel[: -len("index.html")]


def lang_path(code, path):
    d = L[code]["dir"]
    return ("/" + d + path) if d else path


def lang_file(code, path):
    return os.path.join(ROOT, lang_path(code, path).lstrip("/"), "index.html")


def load_tm(code):
    p = os.path.join(I18N, code + ".json")
    return json.loads(read(p)) if os.path.exists(p) else {}


def save_tm(code, tm):
    write(os.path.join(I18N, code + ".json"), json.dumps(dict(sorted(tm.items())), ensure_ascii=False, indent=0) + "\n")


# ---------------------------------------------------------------- normalisation (any language page -> template form)
SW_RE = re.compile(r'<div class="(lang|m-lang|foot-lang)" role="group" aria-label="[^"]*"(?: translate="no")?>.*?</div>', re.S)
ALSO_RE = re.compile(r'(<div class="alsoin"><span>[^<]*</span>)(?:<a [^>]*>[^<]*</a>|<!--alsoin-->)*(</div>)')
REDIR_RE = re.compile(r"<script>try\{if\(!localStorage\.getItem\('fds-lang'\)\).*?</script>|<!--i18n:redirect-->")


def sw_placeholder(kind):
    return '<!--i18n:sw:%s-->' % kind


def normalise(doc):
    doc = SW_RE.sub(lambda m: sw_placeholder(m.group(1)), doc)
    doc = ALSO_RE.sub(lambda m: m.group(1) + "<!--alsoin-->" + m.group(2), doc)
    doc = REDIR_RE.sub("<!--i18n:redirect-->", doc, count=1)
    doc = re.sub(r'<a class="wordmark( gold)?" href', lambda m: '<a class="wordmark%s" translate="no" href' % (m.group(1) or ""), doc)
    return doc


# ---------------------------------------------------------------- rendering helpers
def esc_text(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\xa0", "&nbsp;")


def rebuild_tag(tok, new_attrs):
    raw = tok.raw
    for name, val in new_attrs.items():
        pat = re.compile(r'(\s%s=")([^"]*)(")' % re.escape(name))
        raw, n = pat.subn(lambda m: m.group(1) + val + m.group(3), raw, count=1)
    return raw


def relpath(from_dir, target):
    r = posixpath.relpath(target, from_dir)
    if r == ".":
        return "./"
    if target.endswith("/") and not r.endswith("/"):
        r += "/"
    return r


def resolve(base_dir, href):
    parts = [p for p in base_dir.split("/") if p]
    path, frag = href.split("#", 1) if "#" in href else (href, None)
    out = list(parts) if not path.startswith("/") else []
    for s in path.split("/"):
        if s == "..":
            if out:
                out.pop()
        elif s in (".", ""):
            continue
        else:
            out.append(s)
    trailing = path.endswith("/") or path == "" or path.endswith("..") or path.endswith(".")
    res = "/" + "/".join(out) + ("/" if trailing and out else "")
    return res, frag


class Ctx:
    def __init__(self, code, avail, live=None):
        self.code, self.avail, self.live = code, avail, live

    def map_page(self, path):
        if self.code == "en" or path not in self.avail:
            return path
        return lang_path(self.code, path)

    def map_url(self, url):
        if not url.startswith(SITE):
            return url
        rest = url[len(SITE):]
        path, _, frag = rest.partition("#")
        if frag in SHARED_FRAGS or not path.endswith("/"):
            return url
        return SITE + self.map_page(path) + (("#" + frag) if frag else "")


def live_codes(clusters):
    return clusters.get("/", ["en"])


def pill_mode(clusters):
    return set(live_codes(clusters)) <= {"en"} | set(LEGACY)


def switcher(kind, code, en_path, out_path, clusters):
    shipped = live_codes(clusters)
    have = clusters.get(en_path, ["en"])
    pill = pill_mode(clusters)
    links = []
    for c in shipped:
        tgt = lang_path(c, en_path) if c in have else lang_path(c, "/")
        act = ' class="active" aria-current="true"' if c == code else ""
        if pill:
            text = PILL.get(c) or (L[c]["name"] if kind == "m-lang" else L[c]["short"])
        else:
            text = L[c]["name"]
        links.append('<a href="%s" hreflang="%s" lang="%s" data-setlang="%s"%s>%s</a>' % (
            relpath(out_path, tgt), L[c]["hreflang"], L[c]["hreflang"], SETLANG[c], act, text))
    label = L[code]["label"]
    if pill or kind == "m-lang":
        return '<div class="%s" role="group" aria-label="%s"%s>%s</div>' % (
            kind, label, "" if pill else ' translate="no"', "".join(links))
    lis = "".join("<li>%s</li>" % a for a in links)
    return ('<div class="%s" role="group" aria-label="%s" translate="no"><details class="langsw"><summary aria-label="%s: %s">'
            '<span>%s</span><svg class="langsw-ic" viewBox="0 0 24 32" aria-hidden="true"><path d="M5 3.5 L19 16 L5 28.5"/></svg>'
            '</summary><ul>%s</ul></details></div>' % (kind, label, label, L[code]["name"], L[code]["short"], lis))


def alsoin_links(code, en_path, out_path, clusters):
    pill = pill_mode(clusters)
    out = []
    for c in clusters.get(en_path, ["en"]):
        if c == code:
            continue
        text = PILL.get(c, L[c]["name"]) if pill else L[c]["name"]
        out.append('<a href="%s" hreflang="%s" lang="%s" data-setlang="%s">%s</a>' % (
            relpath(out_path, lang_path(c, en_path)), L[c]["hreflang"], L[c]["hreflang"], SETLANG[c], text))
    return "".join(out)


ORIG_REDIRECT = ("<script>try{if(!localStorage.getItem('fds-lang')){var n=(navigator.language||'').toLowerCase(),"
                 "m=n.indexOf('zh')===0?'zh':(n.indexOf('ms')===0||n.indexOf('id')===0)?'ms':n.indexOf('ta')===0?'ta':'';"
                 "if(m){location.replace(m+'/');}}}catch(e){}</script>")


def redirect_script(clusters):
    live = live_codes(clusters)
    if pill_mode(clusters):
        return ORIG_REDIRECT
    mp = {}
    for c in live:
        if c in ("en", "zh-hans", "zh-hant"):
            continue
        mp["tl" if c == "fil" else c] = L[c]["dir"]
        if c == "fil":
            mp["fil"] = "fil"
    if "id" not in mp and "ms" in mp:
        mp["id"] = "ms"
    hant = "zh-hant" if "zh-hant" in live else "zh"
    js = ("<script>try{if(!localStorage.getItem('fds-lang')){var n=(navigator.language||'').toLowerCase(),p=n.split('-')[0],"
          "m=p==='zh'?%s:(%s)[p]||'';"
          "if(m){location.replace(m+'/');}}}catch(e){}</script>") % (
        "(/^zh-(tw|hk|mo|hant)/.test(n)?'zh-hant':'zh')" if hant == "zh-hant" else "'zh'",
        json.dumps(mp, separators=(",", ":"), sort_keys=True))
    return js


def fill_chrome(doc, code, en_path, out_path, clusters):
    for kind in ("lang", "m-lang", "foot-lang"):
        doc = doc.replace(sw_placeholder(kind), switcher(kind, code, en_path, out_path, clusters))
    links = alsoin_links(code, en_path, out_path, clusters)
    if links:
        doc = doc.replace("<!--alsoin-->", links)
    else:
        doc = re.sub(r'<div class="alsoin"><span>[^<]*</span><!--alsoin--></div>', "", doc)
    doc = doc.replace("<!--i18n:redirect-->", redirect_script(clusters) if code == "en" and en_path == "/" else "")
    doc = re.sub(r'<a class="wordmark( gold)?" translate="no" href', lambda m: '<a class="wordmark%s" href' % (m.group(1) or ""), doc)
    return doc


def head_fixups(doc, code, en_path, out_path, cluster):
    lg = L[code]
    url = SITE + out_path
    attrs = 'lang="%s"' % lg["html"] + (' dir="rtl"' if code == "ar" else "")
    doc = re.sub(r'<html lang="[^"]*"(?: dir="rtl")?>', "<html %s>" % attrs, doc, count=1)
    doc = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, doc, count=1)
    alts = "".join('<link rel="alternate" hreflang="%s" href="%s%s">' % (L[c]["hreflang"], SITE, lang_path(c, en_path)) for c in cluster)
    alts += '<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, en_path)
    doc = re.sub(r'(?:<link rel="alternate" hreflang="[^"]*" href="[^"]*">)+', lambda m: alts, doc, count=1)
    doc = re.sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, doc, count=1)
    loc = '<meta property="og:locale" content="%s">' % lg["og"] + "".join(
        '<meta property="og:locale:alternate" content="%s">' % L[c]["og"] for c in cluster if c != code)
    doc = re.sub(r'<meta property="og:locale" content="[^"]*">(?:<meta property="og:locale:alternate" content="[^"]*">)*',
                 lambda m: loc, doc, count=1)
    if lg["font"]:
        doc = re.sub(r'(<link href="https://fonts\.googleapis\.com/css2\?[^"]*?)(&display=swap" rel="stylesheet">)',
                     lambda m: m.group(1) + ("" if lg["font"] in m.group(1) else "&family=" + lg["font"]) + m.group(2), doc, count=1)
    return doc


def ld_transform(d, ld_map, ctx, code, en_path, skip=False):
    if isinstance(d, dict):
        skip2 = skip or ld_skip(d)
        o = {}
        for k, v in d.items():
            if isinstance(v, str):
                if k == "inLanguage":
                    o[k] = L[code]["hreflang"]
                elif not skip2 and k in LD_TEXT_KEYS:
                    suf = SUFFIX if v.endswith(SUFFIX) else ""
                    key = norm(v[: -len(suf)] if suf else v)
                    o[k] = ld_map.get(key, key) + (ld_map.get("\0suffix", SUFFIX) if suf else "")
                elif v.startswith(SITE) and not skip2:
                    o[k] = ctx.map_url(v)
                else:
                    o[k] = v
            elif k == "keywords":
                o[k] = v
            elif k == "inLanguage" and isinstance(v, list) and ctx.live:
                o[k] = [L[c]["hreflang"] for c in ctx.live]
            else:
                o[k] = ld_transform(v, ld_map, ctx, code, en_path, skip2)
        ts = d.get("@type") if isinstance(d.get("@type"), list) else [d.get("@type")]
        if code != "en" and any(t in ("BlogPosting", "Article") for t in ts) and "@id" in d and "translationOfWork" not in d:
            o["translationOfWork"] = {"@id": d["@id"]}
        return o
    if isinstance(d, list):
        return [ld_transform(v, ld_map, ctx, code, en_path, skip) for v in d]
    return d


def render(doc, en_rel, code, tm, avail, clusters):
    """Render normalised EN template doc in language code. Returns (html, missing_ids)."""
    ctx = Ctx(code, avail, live_codes(clusters))
    en_path = page_path(en_rel)
    out_path = lang_path(code, en_path)
    toks, segs = segments(doc)
    missing = set()
    suffix_tr = SUFFIX if code == "en" else tm.get(sid(SUFFIX_KEY), SUFFIX)
    if code != "en" and sid(SUFFIX_KEY) not in tm and any(x.suffix for x in segs):
        missing.add(sid(SUFFIX_KEY))

    def tr(seg):
        if seg.id is None or code == "en":
            return seg.text
        v = tm.get(seg.id)
        if v is None:
            missing.add(seg.id)
            return seg.text
        return v

    if code == "en":
        out = head_fixups(doc, code, en_path, out_path, clusters.get(en_path, ["en"]))
        out = website_languages(out, clusters)
        return fill_chrome(out, code, en_path, out_path, clusters), missing

    newtag, attr_tr = {}, {}
    for s in segs:
        if s.kind == "attr":
            attr_tr.setdefault(s.tok, {})[s.attr] = tr(s) + (suffix_tr if s.suffix else "")
    for i, t in enumerate(toks):
        if t.kind not in ("start", "startend"):
            continue
        at = dict(t.attrs)
        repl = {}
        for a, v in attr_tr.get(i, {}).items():
            if a == "wa":
                base = at["href"].split("?text=", 1)[0]
                repl["href"] = html.escape(base + "?text=" + quote(v, safe=""), quote=True)
            else:
                repl[a] = html.escape(v, quote=True)
        for a in ("href", "src"):
            v = at.get(a)
            if v is None or re.match(r"^(?:[a-z]+:|//|#)", v):
                continue
            path, frag = resolve(en_path, v)
            tgt = ctx.map_page(path) if path.endswith("/") else path
            if v.startswith("/"):
                newv = tgt + (("#" + frag) if frag else "")
            else:
                newv = relpath(out_path, tgt) + (("#" + frag) if frag else "")
            repl[a] = html.escape(newv, quote=True)
        newtag[i] = rebuild_tag(t, repl) if repl else t.raw

    edits, covered = [], []
    for s in segs:
        if s.kind != "run":
            continue
        txt = tr(s)
        pieces, pos = [], 0
        for m in PH_RE.finditer(txt):
            pieces.append(esc_text(txt[pos:m.start()]))
            ph = m.group(0)
            n = int(re.search(r"\d+", ph).group(0)) - 1
            kind, o, c = s.tags[n]
            pieces.append(toks[c].raw if ph.startswith("</") else newtag.get(o, toks[o].raw))
            pos = m.end()
        pieces.append(esc_text(txt[pos:]))
        edits.append((s.a, s.b, s.lead + "".join(pieces) + esc_text(suffix_tr if s.suffix else "") + s.trail))
        covered.append((s.a, s.b))
    for i, t in enumerate(toks):
        if t.kind in ("start", "startend") and newtag[i] != t.raw:
            if not any(a <= t.start < b for a, b in covered):
                edits.append((t.start, t.end, newtag[i]))
    ld_map = {s.text: tr(s) for s in segs if s.kind == "ld"}
    ld_map["\0suffix"] = suffix_tr
    for i, t in enumerate(toks):
        if t.kind == "start" and t.tag == "script" and dict(t.attrs).get("type") == "application/ld+json":
            d = ld_transform(json.loads(toks[i + 1].raw), ld_map, ctx, code, en_path)
            edits.append((toks[i + 1].start, toks[i + 1].end, json.dumps(d, ensure_ascii=False, indent=1)))
    edits.sort(key=lambda e: e[0])
    res, pos = [], 0
    for a, b, txt in edits:
        if a < pos:
            raise RuntimeError("overlapping edits in %s" % en_rel)
        res.append(doc[pos:a]); res.append(txt); pos = b
    res.append(doc[pos:])
    out = "".join(res)
    out = head_fixups(out, code, en_path, out_path, clusters.get(en_path, ["en"]))
    return fill_chrome(out, code, en_path, out_path, clusters), missing


def website_languages(doc, clusters):
    """Keep the WebSite node's inLanguage list in step with the live languages (pretty-printed JSON-LD)."""
    if pill_mode(clusters):
        return doc
    langs = [L[c]["hreflang"] for c in live_codes(clusters)]

    def fix(m):
        ind = m.group(2)
        return m.group(1) + "[\n" + ",\n".join(ind + " " + json.dumps(x) for x in langs) + "\n" + ind + "]"
    return re.sub(r'("@type": "WebSite",(?:(?!"@type").)*?"inLanguage": )\[[^\]]*\n( *)\]', fix, doc, count=1, flags=re.S)


def patch_kept(doc, code, en_path, clusters):
    """Existing language page that is not (yet) fully in the TM: refresh head + chrome only."""
    out_path = lang_path(code, en_path)
    doc = normalise(doc)
    doc = head_fixups(doc, code, en_path, out_path, clusters.get(en_path, ["en"]))
    doc = website_languages(doc, clusters)
    return fill_chrome(doc, code, en_path, out_path, clusters)


# ---------------------------------------------------------------- commands
def cmd_extract(quiet=False):
    src, pages = {}, {}
    for rel in en_pages():
        _, segs = segments(normalise(read(os.path.join(ROOT, rel))))
        ids = []
        for s in segs:
            if s.id:
                src[s.id] = s.text
                if s.id not in ids:
                    ids.append(s.id)
        if any(s.suffix for s in segs) and sid(SUFFIX_KEY) not in ids:
            ids.append(sid(SUFFIX_KEY)); src[sid(SUFFIX_KEY)] = SUFFIX_KEY
        pages[page_path(rel)] = ids
    write(os.path.join(I18N, "source.json"), json.dumps(dict(sorted(src.items())), ensure_ascii=False, indent=0) + "\n")
    write(os.path.join(I18N, "pages.json"), json.dumps(pages, ensure_ascii=False, indent=0) + "\n")
    if not quiet:
        print("%d pages, %d unique segments, %d words" % (len(pages), len(src), sum(len(v.split()) for v in src.values())))
    return src, pages


def availability(code, pages, tm):
    """(complete, kept): pages rendered from the TM, and existing language pages kept as they are."""
    if code == "en":
        return set(pages), set()
    complete = {p for p, ids in pages.items() if all(i in tm for i in ids)}
    kept = {p for p in pages if p not in complete and os.path.exists(lang_file(code, p))}
    if "/" not in complete and "/" not in kept:
        return set(), set()
    return complete, kept


def cmd_todo(code, which, out=sys.stdout):
    src, pages = cmd_extract(quiet=True)
    tm = load_tm(code)
    seen = set()
    n = 0
    for path in (which or list(pages)):
        if not path.startswith("/"):
            path = "/" + path.strip("/") + "/" if path.strip("/") else "/"
        for i in pages[path]:
            if i not in tm and i not in seen:
                seen.add(i)
                out.write("%s\t%s\n" % (i, src[i]))
                n += 1
    return n


def check_ph(en, tr):
    return sorted(PH_RE.findall(en)) == sorted(PH_RE.findall(tr))


def cmd_merge(code, f):
    src = json.loads(read(os.path.join(I18N, "source.json")))
    tm = load_tm(code)
    bad = n = 0
    for ln in read(f).splitlines():
        if not ln.strip() or "\t" not in ln:
            continue
        i, t = ln.split("\t", 1)
        i, t = i.strip(), t.strip()
        if i not in src:
            print("unknown id", i); bad += 1; continue
        if not t or not check_ph(src[i], t):
            print("placeholder mismatch/empty", i, src[i][:60], "||", t[:60]); bad += 1; continue
        tm[i] = t; n += 1
    save_tm(code, tm)
    print("merged %d, rejected %d -> i18n/%s.json (%d entries)" % (n, bad, code, len(tm)))


def cmd_status():
    src, pages = cmd_extract(quiet=True)
    need = set(i for ids in pages.values() for i in ids)
    for code in CODES[1:]:
        tm = load_tm(code)
        comp, kept = availability(code, pages, tm)
        print("%-8s %4d/%4d segments  %2d/%2d pages from TM  %2d kept as-is" % (
            code, len(need & set(tm)), len(need), len(comp), len(pages), len(kept)))


def cmd_build():
    src, pages = cmd_extract(quiet=True)
    tms = {c: load_tm(c) for c in CODES[1:]}
    comp, kept, avail = {"en": set(pages)}, {"en": set()}, {"en": set(pages)}
    for c in CODES[1:]:
        comp[c], kept[c] = availability(c, pages, tms[c])
        avail[c] = comp[c] | kept[c]
    clusters = {path: [c for c in CODES if path in avail[c]] for path in pages}
    changed, written = set(), []

    def put(dest, s, url):
        old = read(dest) if os.path.exists(dest) else None
        if old != s:
            write(dest, s)
            changed.add(url)
        written.append(url)

    for rel in en_pages():
        en_path = page_path(rel)
        base = normalise(read(os.path.join(ROOT, rel)))
        for c in CODES:
            if en_path in comp[c]:
                out, missing = render(base, rel, c, tms.get(c, {}), avail[c], clusters)
                if missing:
                    raise RuntimeError("%s %s missing %d" % (c, en_path, len(missing)))
            elif en_path in kept[c]:
                out = patch_kept(read(lang_file(c, en_path)), c, en_path, clusters)
            else:
                continue
            put(lang_file(c, en_path), out, SITE + lang_path(c, en_path))
    # never drop a language page silently
    stale = []
    for c in CODES[1:]:
        d = os.path.join(ROOT, L[c]["dir"])
        for f in glob.glob(os.path.join(d, "**", "index.html"), recursive=True):
            u = SITE + "/" + os.path.relpath(f, ROOT)[: -len("index.html")]
            if u not in written:
                stale.append(u)
    if stale:
        sys.exit("language pages without an English template: %s" % ", ".join(stale[:5]))
    write_sitemaps(pages, avail, clusters, changed)
    write_llms(avail)
    print("built %d pages (%d changed); languages live: %s" % (len(written), len(changed), ", ".join(
        "%s(%d%s)" % (c, len(avail[c]), (", %d kept" % len(kept[c])) if kept[c] else "") for c in CODES if avail[c])))
    for c in CODES[1:]:
        if kept[c] and c not in LEGACY:
            print("WARNING %s: %d page(s) kept with an outdated translation (run todo): %s" % (c, len(kept[c]), ", ".join(sorted(kept[c]))))


# English-only URLs listed in the English sitemap (facilitator guide)
def english_only_urls():
    urls = ["/guide/"] + ["/guide/%s" % os.path.basename(p) for p in sorted(glob.glob(os.path.join(ROOT, "guide", "session-*.html")))]
    urls += ["/guide/people.html", "/guide/data.html"]
    return [u for u in urls if os.path.exists(os.path.join(ROOT, u.lstrip("/"), "index.html") if u.endswith("/") else os.path.join(ROOT, u.lstrip("/")))]


def old_lastmods():
    lm = {}
    for f in glob.glob(os.path.join(ROOT, "sitemap*.xml")):
        for loc, mod in re.findall(r"<loc>([^<]+)</loc>\s*(?:<xhtml:link[^>]*/>\s*)*<lastmod>([^<]+)</lastmod>", read(f)):
            lm[loc] = mod
    return lm


def write_sitemaps(pages, avail, clusters, changed):
    lm = old_lastmods()
    files = []
    for c in CODES:
        if not avail[c]:
            continue
        rows = []
        for path in pages:
            if path not in avail[c]:
                continue
            loc = SITE + lang_path(c, path)
            alts = "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>' % (L[x]["hreflang"], SITE, lang_path(x, path)) for x in clusters[path])
            alts += '<xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>' % (SITE, path)
            pr = "1.0" if path == "/" and c == "en" else ("0.9" if path in ("/", "/articles/") else "0.8")
            cf = "weekly" if path in ("/", "/articles/", "/gatherings/") else "monthly"
            mod = TODAY if (loc in changed or loc not in lm) else lm[loc]
            rows.append("<url><loc>%s</loc>%s<lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>" % (loc, alts, mod, cf, pr))
        if c == "en":
            for u in english_only_urls():
                loc = SITE + u
                rows.append('<url><loc>%s</loc><xhtml:link rel="alternate" hreflang="en" href="%s"/><xhtml:link rel="alternate" hreflang="x-default" href="%s"/>'
                            "<lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>" % (
                                loc, loc, loc, lm.get(loc, TODAY), "0.9" if u == "/guide/" else "0.8"))
        name = "sitemap-%s.xml" % c
        write(os.path.join(ROOT, name), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")
        files.append(name)
    for f in glob.glob(os.path.join(ROOT, "sitemap-*.xml")):
        if os.path.basename(f) not in files:
            os.remove(f)
    idx = '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(
        "<sitemap><loc>%s/%s</loc><lastmod>%s</lastmod></sitemap>" % (SITE, f, TODAY) for f in files) + "\n</sitemapindex>\n"
    write(os.path.join(ROOT, "sitemap.xml"), idx)
    rp = os.path.join(ROOT, "robots.txt")
    r = read(rp)
    if "# Sitemap index" not in r:
        r = r.replace("Sitemap: %s/sitemap.xml" % SITE,
                      "# Sitemap index: sitemap-en.xml plus one sitemap per language (sitemap-<code>.xml)\nSitemap: %s/sitemap.xml" % SITE)
        write(rp, r)


def write_llms(avail):
    p = os.path.join(ROOT, "llms.txt")
    t = read(p)
    live = [c for c in CODES if avail[c]]
    t = re.sub(r"^- Languages: .*$", "- Languages: " + ", ".join(
        "%s%s" % (L[c]["name"], (" (/%s/)" % L[c]["dir"]) if L[c]["dir"] else "") for c in live), t, count=1, flags=re.M)
    block = ["## Other languages", ""]
    for c in live[1:]:
        block.append("- %s: %s%s%s" % (L[c]["name"], SITE, lang_path(c, "/"),
                     (" · %s%s" % (SITE, lang_path(c, "/articles/"))) if "/articles/" in avail[c] else ""))
    t = re.sub(r"## Other languages\n.*?\n\n(?=## )", lambda m: "\n".join(block) + "\n\n", t, flags=re.S)
    write(p, t)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    if a[0] == "extract":
        cmd_extract()
    elif a[0] == "todo":
        cmd_todo(a[1], a[2:])
    elif a[0] == "merge":
        cmd_merge(a[1], a[2])
    elif a[0] == "status":
        cmd_status()
    elif a[0] == "build":
        cmd_build()
    else:
        print(__doc__)
