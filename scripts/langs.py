"""リポジトリの言語比率をドーナツグラフの SVG に書き出す。"""
import json
import math
import os
import sys
import urllib.request

USER = os.environ["GITHUB_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]
PRIVATE = bool(os.environ.get("INCLUDE_PRIVATE"))
OUT = sys.argv[1]

# マークアップや設定ファイルは比率を歪めるので除外する
EXCLUDE = {"HTML", "CSS", "SCSS", "MDX", "Shell", "Makefile", "Dockerfile", "HCL", "Jupyter Notebook"}
COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#a371f7", "Go": "#00add8",
    "Swift": "#f05138", "Astro": "#ff5a03", "Rust": "#dea584", "Java": "#b07219",
    "Kotlin": "#a97bff", "Ruby": "#701516", "PHP": "#4f5d95",
}
FALLBACK = ["#8b949e", "#6e7681", "#484f58"]
TOP = 5


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def repos():
    base = "https://api.github.com/user/repos?affiliation=owner&visibility=all" if PRIVATE else f"https://api.github.com/users/{USER}/repos?type=owner"
    page = 1
    while True:
        batch = get(f"{base}&per_page=100&page={page}")
        if not batch:
            return
        yield from (r for r in batch if not r["fork"] and not r["archived"])
        page += 1


totals = {}
for repo in repos():
    for lang, size in get(repo["languages_url"]).items():
        if lang not in EXCLUDE:
            totals[lang] = totals.get(lang, 0) + size

ranked = sorted(totals.items(), key=lambda kv: -kv[1])
items = ranked[:TOP]
rest = sum(v for _, v in ranked[TOP:])
if rest:
    items.append(("Other", rest))
total = sum(v for _, v in items)

cx, cy, r, stroke = 80, 80, 56, 24
circ = 2 * math.pi * r
arcs, legend, offset = [], [], 0.0
for i, (lang, size) in enumerate(items):
    color = COLORS.get(lang, FALLBACK[i % len(FALLBACK)])
    length = circ * size / total
    arcs.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-dasharray="{length:.2f} {circ - length:.2f}" stroke-dashoffset="{-offset:.2f}" '
        f'transform="rotate(-90 {cx} {cy})"/>'
    )
    offset += length
    y = 80 - (len(items) - 1) * 12 + i * 24
    legend.append(
        f'<circle cx="190" cy="{y}" r="5" fill="{color}"/>'
        f'<text x="204" y="{y + 4}">{lang}</text>'
        f'<text x="330" y="{y + 4}" text-anchor="end">{size / total * 100:.1f}%</text>'
    )

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="160" viewBox="0 0 340 160">'
    '<style>text{font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:#8b949e}</style>'
    + "".join(arcs) + "".join(legend) + "</svg>"
)
with open(OUT, "w") as f:
    f.write(svg)
