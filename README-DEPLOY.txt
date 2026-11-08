FAITH DRIVEN SINGAPORE — MULTI-PAGE SITE · DEPLOYMENT NOTES
===========================================================
Canonical domain: https://faithdriven.sg   (built 24 Sep 2026)

WHAT THIS IS
------------
A static, multi-page, multi-language site. 15 pages × 4 languages = 60 pages:

  /                       Home (refreshed)
  /our-story/             Founding story (Aleks Farseev, Henry Kaestner, co-builders)
  /voices/                Quotes & insights from 22 recorded Foundations sessions
  /gatherings/            Every session 2024–2026: dates, venues, recordings
  /articles/              Article hub + 10 articles:
     what-is-faith-driven-entrepreneur/
     faith-driven-singapore-founding-story/
     aleks-farseev-prayer-for-ducks/          (Salt&Light story)
     redemptive-marketing/                    (Forbes concept)
     faith-driven-entrepreneurs-in-asia/
     anthony-tan-grab-faith-driven-entrepreneur/
     phil-chen-new-taipei-kings/
     foundation-course-8-sessions-explained/
     what-singapore-founders-say/
     dont-worship-work-burnout-sabbath/

  Languages: English at /, 中文 at /zh/, Bahasa Melayu at /ms/, தமிழ் at /ta/
  (same page structure in every language, e.g. /zh/articles/redemptive-marketing/).

UPLOAD
------
Upload EVERYTHING in this folder to the web root, keeping the folder structure.
The host must serve folder/index.html for folder/ URLs (Netlify, Vercel,
Cloudflare Pages, GitHub Pages and most hosts do this by default).
404.html is picked up automatically by Netlify / GitHub Pages / Cloudflare Pages.
The old single-page index.html is replaced by the new home page.

SEO / AEO / GEO BUILT IN
------------------------
- Unique title, description, keywords, canonical per page and per language
- hreflang alternates (en, zh-Hans, ms, ta + x-default) on every page and in sitemap.xml
- Real, crawlable HTML per language (no JS-only translation)
- JSON-LD: Organization/NGO (with founder + founding date), Person, WebSite,
  WebPage/AboutPage/CollectionPage, BlogPosting (with about/mentions entities,
  translationOfWork links), BreadcrumbList, FAQPage (every page has an FAQ),
  Speakable (the "Quick answer" boxes)
- Answer-first "Quick answer" box at the top of every article (what AI answer
  engines quote), question-style H2s, cited sources on every article
- sitemap.xml (60 URLs with alternates), feed.xml (Atom), robots.txt welcoming
  AI crawlers, llms.txt + llms-full.txt (full English text for LLM grounding)
- Open Graph / Twitter cards, geo meta, favicons, manifest, Google Analytics (G-4MDEPHJHBF)

AFTER DEPLOY
------------
1. Google Search Console + Bing Webmaster Tools: submit https://faithdriven.sg/sitemap.xml
2. Rich Results Test on /articles/what-is-faith-driven-entrepreneur/ (FAQ, Article, Breadcrumb)
3. Request indexing for / , /zh/ , /ms/ , /ta/ and /articles/

TO EDIT
-------
Source + generator live in the companion "faithdriven-site-source" folder:
content/<lang>/(pages|articles)/*.html, strings.py, build.py → `python3 build.py prod`.

LANGUAGES (tools/i18n.py, Nov 2026)
-----------------------------------
The English pages in this repo are now the template for every language (Python 3, standard library only):

  python3 tools/i18n.py status                     coverage per language
  python3 tools/i18n.py todo <code> [/path/ ...]   untranslated segments as  id<TAB>English
  python3 tools/i18n.py merge <code> <file.tsv>    merge  id<TAB>translation  (keep <g1>…</g1> / <x1/>)
  python3 tools/i18n.py build                      render languages, hreflang, switchers, sitemaps, llms.txt
  python3 tools/check_site.py                      must end with "0 errors"

- Translated: home, our-story, voices, gatherings, articles hub + 10 articles (15 pages).
  English-only by design: /guide/ (facilitator guide, sessions, people, data — research documents with
  coded transcripts), the root session-*/people/data copies (canonical -> /guide/), /thank-you-giving/, 404.
- URLs: English at /, Simplified Chinese at /zh/, Malay /ms/, Tamil /ta/ (extra language, kept), and
  /zh-hant/ /ja/ /ko/ /th/ /vi/ /id/ /hi/ /fil/ /es/ /fr/ /de/ /pt/ /ar/ (rtl) /ru/ with the same paths.
- Translation memory: i18n/<code>.json; English segments: i18n/source.json; i18n/pages.json lists ids per page.
  The existing zh/ms/ta pages were imported (tools/i18n_import_legacy.py, aligned with commit cc95725).
- A page is rendered in a language only when 100% of its segments are translated; a language goes live
  with its home page. Existing language pages that are not 100% (e.g. zh/ms/ta until the rewritten English
  titles/descriptions are translated) are kept as they are; only their hreflang, og:locale, language
  switchers and "Also available in" links are refreshed.
- While only EN/zh/ms/ta are live the original pill switcher is kept unchanged; from the 5th language on,
  the header and footer show a dropdown (details.langsw) and the mobile menu lists every language.
  Clicks fire the GA4 event language_switch (track.js).
- Sitemaps: sitemap.xml is an index of sitemap-en.xml (incl. the guide pages) and sitemap-<code>.xml.
