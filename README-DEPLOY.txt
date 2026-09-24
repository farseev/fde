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
