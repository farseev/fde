FAITH DRIVEN SINGAPORE — DEPLOYMENT NOTES
=========================================

Canonical domain: https://faithdriven.sg

WHAT TO UPLOAD
--------------
Upload ALL of these files to your web ROOT (the same folder, so they sit at
https://faithdriven.sg/<filename>):

  index.html              the website (single self-contained page)
  favicon.svg             modern vector favicon
  favicon-16x16.png       favicon (small)
  favicon-32x32.png       favicon (standard)
  favicon-192x192.png     Android / PWA icon
  favicon-512x512.png     Android / PWA icon (large) + used as logo in structured data
  apple-touch-icon.png    iOS home-screen icon (180x180)
  og-image.png            social-share preview image (1200x630)
  site.webmanifest        PWA manifest (installable app metadata)
  robots.txt              crawler rules (search + AI/LLM crawlers welcomed)
  sitemap.xml             XML sitemap
  llms.txt                curated context for AI / LLM crawlers (GEO)
  llms-full.txt           fuller content for AI / LLM grounding (GEO)
  humans.txt              credits (optional but nice)

Keep every file in the SAME folder as index.html. The favicon/manifest/og
references use relative paths and will resolve automatically once uploaded.

TURN ON HTTPS
-------------
Your site currently shows "Not secure" on http://faithdriven.sg. Enable HTTPS
(free & automatic on Netlify, Vercel, Cloudflare Pages, or via Let's Encrypt).
HTTPS is what lets WhatsApp / Facebook / LinkedIn / X render the share preview,
and search engines strongly prefer it.

IF YOU CHANGE DOMAINS
---------------------
Search-and-replace https://faithdriven.sg in these files:
  index.html, sitemap.xml, robots.txt, llms.txt, llms-full.txt

AFTER DEPLOY — TELL SEARCH ENGINES
----------------------------------
1. Google Search Console (search.google.com/search-console): add the property,
   then submit https://faithdriven.sg/sitemap.xml under Sitemaps.
2. Bing Webmaster Tools (bing.com/webmasters): add the site and submit the same
   sitemap. (Bing also powers ChatGPT/Copilot search results.)
3. Test the share preview at opengraph.xyz or the Facebook Sharing Debugger.
4. Test structured data at search.google.com/test/rich-results (you should see
   Organization and FAQ).

WHAT'S ALREADY DONE FOR SEO / GEO
---------------------------------
- Title, meta description, keywords, author, canonical URL
- Open Graph + Twitter Card tags with a branded 1200x630 preview image
- Geo meta tags (region SG)
- Favicon set + web manifest (installable)
- JSON-LD structured data: Organization/NGO, WebSite, WebPage, FAQPage
- A crawlable, multilingual FAQ section (great for Google FAQ results and for
  being quoted by AI assistants)
- robots.txt that explicitly ALLOWS AI crawlers (GPTBot, ClaudeBot,
  PerplexityBot, Google-Extended, Applebot-Extended, CCBot, and more)
- llms.txt and llms-full.txt so AI assistants can understand and cite the site
