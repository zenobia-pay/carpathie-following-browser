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
    username = obj.get('username', '')
    name = html.escape(obj.get('name', ''))
    bio = html.escape(obj.get('bio', ''))
    followers = obj.get('followersCount', '?')
    following = obj.get('followingCount', '?')

    tweet_items = []
    for t in obj.get('tweets', []):
        text = html.escape((t.get('text') or '').strip()[:260])
        tweet_items.append(
            f"<li><span class='excerpt'>{text}</span><a target='_blank' href='{t['url']}'>view tweet</a></li>"
        )
    tweets = ''.join(tweet_items) if tweet_items else "<li class='muted'>No tweets captured in this pass.</li>"

    cards.append(f"""
    <article class='card' data-filter='{html.escape((username + ' ' + name + ' ' + bio).lower())}'>
      <header class='card-head'>
        <h3><a target='_blank' href='{obj['profileUrl']}'>@{username}</a></h3>
        <a class='raw' target='_blank' href='data/accounts/{username}.json'>raw json</a>
      </header>
      <p class='name'>{name}</p>
      <p class='bio'>{bio}</p>
      <p class='meta'>Followers {followers} · Following {following}</p>
      <details>
        <summary>Recent tweets ({len(obj.get('tweets', []))})</summary>
        <ol>{tweets}</ol>
      </details>
    </article>
    """)

index = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'/>
  <meta name='viewport' content='width=device-width,initial-scale=1'/>
  <title>Carpathie Following Browser</title>
  <link rel='preconnect' href='https://fonts.googleapis.com'>
  <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
  <link href='https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Instrument+Serif:ital@0;1&display=swap' rel='stylesheet'>
  <style>
    :root {{
      --bg:#f3efe8;
      --panel:#fffdfa;
      --line:#ddd2c1;
      --ink:#191712;
      --muted:#6f6659;
      --accent:#1f4ad6;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:'Space Grotesk',sans-serif; background:linear-gradient(180deg,#f7f4ee 0%,#f0e9de 100%); color:var(--ink); }}
    .wrap {{ max-width:1280px; margin:0 auto; padding:24px 18px 48px; }}
    .top {{ position:sticky; top:0; z-index:3; backdrop-filter:blur(8px); background:rgba(243,239,232,.88); border-bottom:1px solid var(--line); padding:14px 0 12px; margin-bottom:16px; }}
    h1 {{ margin:0; font-family:'Instrument Serif',serif; font-size:2.2rem; letter-spacing:.2px; }}
    .meta {{ color:var(--muted); margin:.35rem 0 0; font-size:.95rem; }}
    .controls {{ margin-top:12px; display:flex; gap:10px; align-items:center; }}
    input {{ width:min(520px,100%); border:1px solid var(--line); border-radius:10px; background:#fff; padding:10px 12px; font:inherit; }}
    a {{ color:var(--accent); text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:12px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:12px; }}
    .card-head {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
    .card h3 {{ margin:0; font-size:1.05rem; }}
    .raw {{ font-size:.82rem; color:var(--muted); }}
    .name {{ margin:.3rem 0 0; font-weight:500; }}
    .bio {{ margin:.5rem 0 .6rem; line-height:1.45; color:#2d2923; }}
    details {{ border-top:1px solid var(--line); padding-top:8px; }}
    summary {{ cursor:pointer; color:var(--muted); }}
    ol {{ margin:.6rem 0 0 1rem; padding:0; }}
    li {{ margin:.45rem 0; }}
    .excerpt {{ display:block; margin-bottom:.15rem; color:#2a251f; }}
    .muted {{ color:var(--muted); }}
  </style>
</head>
<body>
  <main class='wrap'>
    <section class='top'>
      <h1>Following Network Browser — @{manifest['targetHandle']}</h1>
      <p class='meta'>Accounts discovered: {manifest['totalFollowing']} · Profiles processed: {len(manifest['accounts'])} · Generated: {manifest['generatedAt']}</p>
      <div class='controls'>
        <input id='q' placeholder='Filter by handle, name, or bio...' />
        <a target='_blank' href='data/manifest.json'>manifest.json</a>
        <a target='_blank' href='data/journal.json'>journal.json</a>
        <a target='_blank' href='data/raw/following.json'>following.json</a>
      </div>
    </section>
    <section class='grid' id='grid'>
      {''.join(cards)}
    </section>
  </main>
  <script>
    const input = document.getElementById('q');
    const cards = Array.from(document.querySelectorAll('.card'));
    input.addEventListener('input', () => {{
      const q = input.value.trim().toLowerCase();
      cards.forEach(c => c.style.display = c.dataset.filter.includes(q) ? '' : 'none');
    }});
  </script>
</body>
</html>"""

(PUB / 'index.html').write_text(index)
(PUB / 'data').mkdir(parents=True, exist_ok=True)
(PUB / 'data' / 'manifest.json').write_text((DATA / 'manifest.json').read_text())
if (DATA / 'journal.json').exists():
    (PUB / 'data' / 'journal.json').write_text((DATA / 'journal.json').read_text())
print('built public/index.html')
