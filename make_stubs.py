#!/usr/bin/env python3
"""
Create the redirect stubs that must survive the domain move.

WHY THESE THREE AND ONLY THESE THREE
When an account's user site holds a custom domain, GitHub serves that account's
project pages under the domain automatically. So once dmang-dev.github.io holds
dmang.com:
    dmang.com/ca-grid-weather-map/  -> served natively, no stub needed
    dmang.com/kobofix/              -> served natively, no stub needed

But privacypolicy, leaflet-kmz-koppen and salesforce-enphase live on the OTHER
account (dk-dev). They were reachable at dmang.com only because dk-dev used to hold
the domain. After the move they have no route at all, so they need stubs here.

privacypolicy is the one that actually matters: that URL is typically registered in
an app-store listing or OAuth consent screen that cannot easily be edited, and some
of those auto-check the URL and flag the listing when it stops resolving.

A static host cannot issue a 301, so each stub redirects three independent ways --
canonical link, meta refresh, and location.replace() carrying query+fragment -- with
a visible link if all three are blocked.
"""
import io
import os

STUBS = {
    'privacypolicy': 'https://dk-dev.github.io/privacypolicy/',
    'leaflet-kmz-koppen': 'https://dk-dev.github.io/leaflet-kmz-koppen/',
    'salesforce-enphase': 'https://dk-dev.github.io/salesforce-enphase/',
}

TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Moved - {name}</title>
<link rel="canonical" href="{url}" />
<meta name="robots" content="noindex" />
<meta http-equiv="refresh" content="0; url={url}" />
<script>location.replace("{url}" + location.search + location.hash);</script>
<style>
  body {{ font: 16px/1.5 system-ui, sans-serif; margin: 3rem auto; max-width: 34rem;
         padding: 0 1rem; color: #222; }}
  a {{ color: #1a5fb4; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0d1117; color: #e6edf3; }}
    a {{ color: #4493f8; }}
  }}
</style>
</head>
<body>
<h1>This page has moved</h1>
<p><strong>{name}</strong> is now at:</p>
<p><a href="{url}">{url}</a></p>
<p>The old address still works and will send you there automatically. If it did
not, follow the link above.</p>
</body>
</html>
'''

for name, url in STUBS.items():
    os.makedirs(name, exist_ok=True)
    p = os.path.join(name, 'index.html')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(TPL.format(name=name, url=url))
    print('  wrote %s -> %s' % (p, url))

# .nojekyll: this is a plain static site, not Jekyll. Without it GitHub runs the
# Jekyll build, which ignores files and directories beginning with an underscore and
# adds a build step that can fail on content it does not expect.
with io.open('.nojekyll', 'w', encoding='utf-8') as f:
    f.write('')
print('  wrote .nojekyll (skip the Jekyll build; this is plain static HTML)')
print('\n  NOTE: no CNAME written by this script - that is a separate deliberate step.')
