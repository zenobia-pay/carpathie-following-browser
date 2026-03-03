#!/usr/bin/env python3
import json, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PUB = ROOT / 'public'
manifest = json.loads((DATA / 'manifest.json').read_text())

cards = []
for a in manifest['accounts']:
    fp = DATA / a['file']
    if not fp.exists():
        continue
    obj = json.loads(fp.read_text())
    tweets = ''.join([
        f"<li><a target='_blank' href='{t['url']}'>tweet</a> — {html.escape((t.get('text') or '')[:220])}</li>" for t in obj.get('tweets', [])
    ])
    cards.append(f"""
    <article class='card'>
      <h3><a target='_blank' href='{obj['profileUrl']}'>@{obj['username']}</a> — {html.escape(obj.get('name',''))}</h3>
      <p>{html.escape(obj.get('bio',''))}</p>
      <p class='meta'>Followers: {obj.get('followersCount','?')} · Following: {obj.get('followingCount','?')} · <a target='_blank' href='data/accounts/{obj['username']}.json'>raw file</a></p>
      <details><summary>10 recent tweets ({len(obj.get('tweets',[]))})</summary><ol>{tweets}</ol></details>
    </article>
    """)

index = f"""<!doctype html><html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Carpathie Following Browser</title>
<style>body{{font-family:system-ui;background:#faf8f5;margin:0}}.wrap{{max-width:1100px;margin:0 auto;padding:24px}}.card{{background:#fff;border:1px solid #e9e1d6;border-radius:12px;padding:12px;margin:10px 0}}.meta{{color:#6a6258}}</style>
</head><body><main class='wrap'>
<h1>Following Network Browser — @{manifest['targetHandle']}</h1>
<p class='meta'>Accounts scraped: {manifest['totalFollowing']} · Generated: {manifest['generatedAt']}</p>
<p><a href='data/manifest.json' target='_blank'>manifest.json</a></p>
{''.join(cards)}
</main></body></html>"""

(PUB / 'index.html').write_text(index)
(PUB / 'data').mkdir(parents=True, exist_ok=True)
(PUB / 'data' / 'manifest.json').write_text((DATA / 'manifest.json').read_text())
print('built public/index.html')
