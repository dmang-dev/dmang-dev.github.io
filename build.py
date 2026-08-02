#!/usr/bin/env python3
"""
Generate index.html for dmang-dev.github.io from live GitHub metadata.

Run:  python build.py           (re-fetches from the API, rewrites index.html)

Descriptions, languages, stars and fork status all come from the API rather than
being hand-written, so the page cannot drift from reality. Section blurbs are the
only prose kept here, because those express intent the API does not carry.

⚠️ sj-mosquito-maps is deliberately absent and must stay absent. That project was
separated from this identity on purpose -- its git history was rewritten to remove
every dmang-dev trace. Do not add it here or on dmang.com.

⚠️ No CNAME file is written. Adding one would apply the custom domain to the WHOLE
account and 301 dmang-dev.github.io/ca-grid-weather-map/ and /kobofix/ to paths that
do not exist on dmang.com.
"""
import html
import json
import subprocess
import sys

OWNER = 'dmang-dev'

SECTIONS = [
    {
        'id': 'psp',
        'title': 'PSP Development',
        'blurb': 'Toolchain work and homebrew for the Sony PSP — including a one-command '
                 'native Windows build of the pspdev toolchain, which historically required '
                 'a Linux box or WSL.',
        'repos': ['pspdev-win', 'btc-miner-psp', 'pspdev'],
    },
    {
        'id': 'kobo',
        'title': 'Kobo E-Readers',
        'blurb': 'Kobo readers use Adobe RMSDK, which chokes on CSS that every other reader '
                 'handles. These find the breakage and fix it.',
        'repos': ['kobofix', 'epubcheck-kobo'],
    },
    {
        'id': 'mcp',
        'title': 'MCP Servers for Emulators',
        'blurb': 'Model Context Protocol servers that let an AI client drive a running '
                 'emulator — read and write memory, press buttons, save state, step frames. '
                 'One per emulator family, covering most consoles from the NES to the PS3.',
        'repos': ['mcp-retroarch', 'mcp-bizhawk', 'mcp-dolphin', 'mcp-ppsspp', 'mcp-mgba', 'mcp-pine'],
    },
    {
        'id': 'totp',
        'title': 'TOTP Authenticators',
        'blurb': 'RFC 6238 two-factor authenticators running natively on retro handhelds. '
                 'Real HMAC-SHA1 on hardware that predates the standard by decades — a Game '
                 'Boy generating the same six digits as your phone.',
        'repos': ['totp-gb', 'totp-3ds', 'totp-nds', 'totp-gba', 'totp-psp'],
    },
    {
        'id': 'hashbench',
        'title': 'Hash Benchmark ROMs',
        'blurb': 'The same 32 hash algorithms, measured on seven generations of console '
                 'silicon — from a 1.79 MHz 6502 to a 268 MHz ARM11. Native code on each, '
                 'no emulation shortcuts.',
        'repos': ['hash-bench', 'hash-bench-nes', 'hash-bench-gb', 'hash-bench-gba',
                  'hash-bench-nds', 'hash-bench-dsi', 'hash-bench-3ds',
                  'hash-bench-n64', 'hash-bench-n64-optimized', 'hash-bench-psp'],
    },
    {
        'id': 'weather',
        'title': 'California Grid & Weather',
        'blurb': 'A live map of California utility outages, PSPS shutoff events, NWS alerts, '
                 'wildfires and NOAA imagery, in one view.',
        'repos': ['ca-grid-weather-map'],
    },
]

LANG_COLOR = {
    'C': '#555555', 'TypeScript': '#3178c6', 'Python': '#3572A5', 'Java': '#b07219',
    'Shell': '#89e051', 'HTML': '#e34c26', 'JavaScript': '#f1e05a', 'C++': '#f34b7d',
    'Assembly': '#6E4C13', 'Makefile': '#427819',
}


def gh(path):
    r = subprocess.run(['gh', 'api', path], capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        print('  WARN: %s -> %s' % (path, r.stderr.strip()[:90]))
        return None
    return json.loads(r.stdout)


def live_demo(d):
    """URL for the 'Live' button, or None.

    Preferred source is the PAGES API, not the homepage field:
      * it is authoritative -- a repo either publishes or it does not
      * it returns the CANONICAL url, which now means dmang.com/<repo>/ rather than
        dmang-dev.github.io/<repo>/. Using the homepage field instead sent visitors
        through a 301 hop, because those fields still hold the pre-domain addresses.
      * any repo published later gets a Live button with no edit here

    The homepage field is only a fallback, for a demo hosted somewhere that is not
    GitHub Pages.

    Excluded either way:
      * github.com/... homepages -- that duplicates the Source button
      * FORKS. `pspdev` is a fork of pspdev/pspdev and its homepage is the UPSTREAM
        project's site; showing that as "Live" would present someone else's work as
        a demo of this repo.
    """
    if d.get('fork'):
        return None
    if d.get('has_pages'):
        p = gh('repos/%s/%s/pages' % (OWNER, d['name']))
        if p and p.get('html_url'):
            return p['html_url']
    hp = (d.get('homepage') or '').strip()
    if not hp or 'github.com' in hp:
        return None
    return hp


def card(d):
    name = html.escape(d['name'])
    desc = html.escape((d.get('description') or '').strip()) or '<em>No description</em>'
    lang = d.get('language')
    stars = d.get('stargazers_count', 0)
    demo = live_demo(d)

    chips = []
    if lang:
        chips.append('<span class="chip"><i style="background:%s"></i>%s</span>'
                     % (LANG_COLOR.get(lang, '#8b949e'), html.escape(lang)))
    if stars:
        chips.append('<span class="chip star">&#9733; %d</span>' % stars)
    if d.get('fork'):
        parent = (d.get('parent') or {}).get('full_name', 'upstream')
        chips.append('<span class="chip fork">fork of %s</span>' % html.escape(parent))
    if d.get('archived'):
        chips.append('<span class="chip archived">archived</span>')

    links = ['<a class="btn" href="%s">Source</a>' % html.escape(d['html_url'])]
    if demo:
        links.insert(0, '<a class="btn primary" href="%s">Live&nbsp;&rarr;</a>' % html.escape(demo))

    return ('<article class="card">\n'
            '  <h3><a href="%s">%s</a></h3>\n'
            '  <p>%s</p>\n'
            '  <div class="chips">%s</div>\n'
            '  <div class="links">%s</div>\n'
            '</article>' % (html.escape(d['html_url']), name, desc,
                            ''.join(chips), ''.join(links)))


def main():
    print('fetching %s repo metadata...' % OWNER)
    sections_html = []
    nav = []
    total = 0
    for s in SECTIONS:
        cards = []
        for name in s['repos']:
            d = gh('repos/%s/%s' % (OWNER, name))
            if d is None:
                continue
            if d.get('private'):
                print('  skipping private: %s' % name)
                continue
            cards.append(card(d))
            total += 1
        if not cards:
            continue
        nav.append('<a href="#%s">%s</a>' % (s['id'], html.escape(s['title'])))
        sections_html.append(
            '<section id="%s">\n  <h2>%s</h2>\n  <p class="blurb">%s</p>\n'
            '  <div class="grid">\n%s\n  </div>\n</section>'
            % (s['id'], html.escape(s['title']), html.escape(s['blurb']),
               '\n'.join(cards)))
        print('  %-28s %d repos' % (s['title'], len(cards)))

    page = TEMPLATE.replace('{{NAV}}', '\n      '.join(nav)) \
                   .replace('{{SECTIONS}}', '\n\n'.join(sections_html)) \
                   .replace('{{COUNT}}', str(total))
    # newline='' keeps LF endings on Windows; a web asset should not ship CRLF.
    with open('index.html', 'w', encoding='utf-8', newline='') as f:
        f.write(page)
    print('\nwrote index.html  (%d repos, %d sections, %d bytes)'
          % (total, len(sections_html), len(page)))


TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dmang-dev — projects</title>
<meta name="description" content="Open-source projects: retro-console homebrew, MCP servers for emulators, TOTP authenticators, hash benchmarks, and a California grid/weather map.">
<meta property="og:title" content="dmang-dev — projects">
<meta property="og:description" content="Retro-console homebrew, MCP servers for emulators, TOTP authenticators on hardware that predates the standard, and hash benchmarks across seven console generations.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#127918;</text></svg>">
<style>
  :root{
    --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0;
    --card:#ffffff; --card-hover:#f6f8fa; --accent:#0969da; --chip:#f6f8fa;
    --shadow:0 1px 3px rgba(31,35,40,.08);
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d;
      --card:#151b23; --card-hover:#1c2128; --accent:#4493f8; --chip:#212830;
      --shadow:0 1px 3px rgba(1,4,9,.5);
    }
  }
  :root[data-theme="light"]{
    --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0;
    --card:#ffffff; --card-hover:#f6f8fa; --accent:#0969da; --chip:#f6f8fa;
  }
  :root[data-theme="dark"]{
    --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d;
    --card:#151b23; --card-hover:#1c2128; --accent:#4493f8; --chip:#212830;
  }
  *{box-sizing:border-box}
  body{
    margin:0; background:var(--bg); color:var(--fg);
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased;
  }
  .wrap{max-width:1080px;margin:0 auto;padding:0 20px}
  header{border-bottom:1px solid var(--line);padding:56px 0 32px;margin-bottom:8px}
  h1{margin:0 0 10px;font-size:2.1rem;letter-spacing:-.02em}
  h1 .at{color:var(--muted);font-weight:400}
  .tagline{margin:0 0 20px;color:var(--muted);font-size:1.06rem;max-width:62ch}
  .toplinks{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
  nav{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);
      padding:12px 0;z-index:10;overflow-x:auto;white-space:nowrap}
  nav a{color:var(--muted);text-decoration:none;margin-right:18px;font-size:.9rem}
  nav a:hover{color:var(--accent)}
  section{padding:38px 0 8px;scroll-margin-top:60px}
  h2{margin:0 0 8px;font-size:1.35rem;letter-spacing:-.01em}
  .blurb{margin:0 0 22px;color:var(--muted);max-width:74ch}
  .grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(310px,1fr))}
  .card{
    background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:16px 18px;display:flex;flex-direction:column;box-shadow:var(--shadow);
    transition:background .15s,border-color .15s,transform .15s;
  }
  .card:hover{background:var(--card-hover);border-color:var(--accent);transform:translateY(-2px)}
  .card h3{margin:0 0 8px;font-size:1.02rem;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .card h3 a{color:var(--accent);text-decoration:none}
  .card h3 a:hover{text-decoration:underline}
  .card p{margin:0 0 14px;color:var(--muted);font-size:.92rem;flex:1}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
  .chip{display:inline-flex;align-items:center;gap:5px;background:var(--chip);
        border:1px solid var(--line);border-radius:20px;padding:2px 9px;
        font-size:.74rem;color:var(--muted)}
  .chip i{width:9px;height:9px;border-radius:50%;display:inline-block}
  .chip.fork{font-style:italic}
  .chip.archived{opacity:.75}
  .links{display:flex;gap:8px;flex-wrap:wrap}
  .btn{display:inline-block;padding:5px 13px;border:1px solid var(--line);
       border-radius:6px;text-decoration:none;color:var(--fg);font-size:.85rem;
       background:var(--chip);transition:border-color .15s,color .15s}
  .btn:hover{border-color:var(--accent);color:var(--accent)}
  .btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
  .btn.primary:hover{opacity:.9;color:#fff}
  footer{border-top:1px solid var(--line);margin-top:56px;padding:28px 0 48px;
         color:var(--muted);font-size:.88rem}
  footer a{color:var(--accent)}
  #themeBtn{position:fixed;right:16px;bottom:16px;width:42px;height:42px;border-radius:50%;
    border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer;
    font-size:1.1rem;box-shadow:var(--shadow)}
  @media (max-width:520px){ h1{font-size:1.7rem} .grid{grid-template-columns:1fr} }
</style>
</head>
<body>

<header>
  <div class="wrap">
    <h1><span class="at">@</span>dmang-dev</h1>
    <p class="tagline">
      Open-source work, mostly about making modern things run on hardware that was
      never asked to do them — two-factor auth on a Game Boy, SHA-256 on a 6502,
      an AI client driving a PlayStation&nbsp;2 emulator.
    </p>
    <div class="toplinks">
      <a class="btn primary" href="https://dmang.com/">dmang.com</a>
      <a class="btn" href="https://github.com/dmang-dev">GitHub profile</a>
    </div>
  </div>
</header>

<nav>
  <div class="wrap">
      {{NAV}}
  </div>
</nav>

<main class="wrap">

{{SECTIONS}}

</main>

<footer>
  <div class="wrap">
    <p>{{COUNT}} public repositories. Everything here is MIT licensed unless its own
       repository says otherwise.</p>
    <p>More at <a href="https://dmang.com/">dmang.com</a> ·
       <a href="https://github.com/dmang-dev">github.com/dmang-dev</a></p>
  </div>
</footer>

<button id="themeBtn" title="Toggle theme" aria-label="Toggle colour theme">&#9681;</button>
<script>
  // Respect the OS preference by default; the button pins an explicit override.
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem('theme'); } catch (e) {}
  if (saved) root.setAttribute('data-theme', saved);
  document.getElementById('themeBtn').addEventListener('click', function () {
    var cur = root.getAttribute('data-theme');
    if (!cur) {
      cur = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    var next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) {}
  });
</script>
</body>
</html>
'''

if __name__ == '__main__':
    main()
