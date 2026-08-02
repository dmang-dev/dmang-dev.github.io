#!/usr/bin/env python3
"""Validate the generated page before it is published."""
import io
import re

src = io.open('index.html', encoding='utf-8').read()
raw = open('index.html', 'rb').read()

print('=== encoding ===')
# Mojibake signature: UTF-8 bytes decoded as cp1252 then re-encoded.
bad = [s for s in ('â€', 'Ã¢', 'ï¿½') if s in src]
print('  mojibake sequences: %s' % (bad or 'none'))
print('  em-dashes (U+2014): %d' % src.count('—'))
print('  decodes as UTF-8  : %s' % (raw.decode('utf-8') == src))
print('  has BOM           : %s' % raw.startswith(b'\xef\xbb\xbf'))

print('\n=== content ===')
print('  cards              : %d' % len(re.findall(r'<article class="card">', src)))
print('  sections           : %d' % len(re.findall(r'<section id=', src)))
print('  nav links          : %d' % len(re.findall(r'<a href="#', src)))
print('  unreplaced {{...}} : %d' % len(re.findall(r'\{\{', src)))

print('\n=== fork labelling (honesty check) ===')
for m in re.findall(r'fork of ([^<]*)', src):
    print('  %s' % m)

print('\n=== live demo links (should be real demos, not github.com) ===')
for m in re.findall(r'btn primary" href="([^"]*)"', src):
    flag = '  <-- points at github, should not be a "Live" button' if 'github.com/dmang-dev/' in m and '.io' not in m else ''
    print('  %s%s' % (m, flag))

print('\n=== tag balance ===')
for t in ('article', 'section', 'div', 'main', 'header', 'footer', 'h2', 'h3', 'p'):
    o = len(re.findall(r'<%s[ >]' % t, src))
    c = len(re.findall(r'</%s>' % t, src))
    print('  %-8s %3d open / %3d close  %s' % (t, o, c, 'OK' if o == c else 'MISMATCH'))

print('\n=== safety: sj-mosquito-maps must NOT appear ===')
for term in ('sj-mosquito', 'mosquito', 'dk-dev'):
    n = src.lower().count(term)
    print('  %-14s %d %s' % (term, n, 'OK' if n == 0 else '<-- MUST BE ZERO'))

print('\n=== external requests (should be none - CSP/perf) ===')
ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', src)
allowed = ('https://dmang.com/', 'https://github.com/dmang-dev')
unexpected = [u for u in ext if not u.startswith(allowed)]
print('  outbound links: %d' % len(ext))
print('  non-link assets (script/style/img from CDN): %d'
      % len(re.findall(r'<(?:script|link|img)[^>]+(?:src|href)="https?://', src)))

print('\n  size: %d bytes' % len(raw))
