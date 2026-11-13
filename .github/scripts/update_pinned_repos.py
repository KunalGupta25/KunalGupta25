#!/usr/bin/env python3
"""Refresh the profile's featured-repositories SVG from GitHub pinned repositories."""
import html
import json
import os
import urllib.request

LOGIN = os.environ.get("GH_USER", "KunalGupta25")
TOKEN = os.environ["GH_TOKEN"]
QUERY = """query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 4, types: [REPOSITORY]) {
      nodes {
        ... on Repository {
          name
          description
          url
          stargazerCount
          primaryLanguage { name }
        }
      }
    }
  }
}"""

def esc(value):
    return html.escape(str(value or ""), quote=True)

payload = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "profile-widget-refresh",
    },
)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)
if result.get("errors"):
    raise RuntimeError("GitHub GraphQL failed: " + json.dumps(result["errors"]))
nodes = (result.get("data") or {}).get("user", {}).get("pinnedItems", {}).get("nodes") or []
repos = [node for node in nodes if node and node.get("name")]

cards = []
positions = [(20, 58), (510, 58), (20, 215), (510, 215)]
for i, repo in enumerate(repos):
    x, y = positions[i]
    name = esc(repo.get("name"))
    desc = (repo.get("description") or "No repository description added yet.")
    # Keep the card text short enough to remain readable.
    desc = esc(desc[:76] + ("…" if len(desc) > 76 else ""))
    lang = esc((repo.get("primaryLanguage") or {}).get("name") or "GitHub repository")
    stars = int(repo.get("stargazerCount") or 0)
    url = esc(repo.get("url"))
    cards.append(f"""
    <rect class="card" x="{x}" y="{y}" width="470" height="140" rx="5"/>
    <text x="{x+22}" y="{y+29}" class="accent" font-size="12">{i+1:02d} / PINNED REPOSITORY</text>
    <text x="{x+22}" y="{y+58}" class="white title">{name}</text>
    <text x="{x+22}" y="{y+83}" class="muted body">{desc}</text>
    <text x="{x+22}" y="{y+119}" class="accent tag">{lang.upper()}  ·  ★ {stars}</text>
    <text x="{x+445}" y="{y+119}" text-anchor="end" class="muted tiny">PINNED</text>
    """)
if not cards:
    cards.append('<text x="500" y="210" text-anchor="middle" class="mono muted" font-size="16">No public pinned repositories were returned by GitHub.</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="390" viewBox="0 0 1000 390" role="img" aria-labelledby="title desc">
<title id="title">GitHub pinned repositories — {esc(LOGIN)}</title>
<desc id="desc">Automatically refreshed cards generated from the public pinned repositories on the GitHub profile.</desc>
<defs><style>.bg{{fill:#0d1117}}.card{{fill:#101820;stroke:#30363d;stroke-width:1}}.accent{{fill:#ffa657}}.muted{{fill:#8b949e}}.white{{fill:#e6edf3}}.mono{{font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace}}.title{{font-size:17px;font-weight:700}}.body{{font-size:12px}}.tag{{font-size:10px;letter-spacing:.6px}}.tiny{{font-size:10px}}</style></defs>
<rect class="bg" width="1000" height="390" rx="6"/><rect x="1" y="1" width="998" height="388" rx="6" fill="none" stroke="#30363d"/>
<path d="M1 38H999" stroke="#30363d"/><circle cx="20" cy="19" r="4" fill="#f85149"/><circle cx="35" cy="19" r="4" fill="#d29922"/><circle cx="50" cy="19" r="4" fill="#3fb950"/>
<text x="70" y="24" class="mono muted" font-size="12">kunal@github: ~/pinned-repositories</text><text x="972" y="24" text-anchor="end" class="mono accent" font-size="11">LIVE PINNED DATA</text>
{''.join(cards)}
</svg>'''
os.makedirs("assets", exist_ok=True)
with open("assets/featured-repos.svg", "w", encoding="utf-8") as output:
    output.write(svg)
print(f"Updated pinned repositories widget with {len(repos)} repositories.")
