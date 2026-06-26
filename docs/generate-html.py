#!/usr/bin/env python3
"""
Render docs/USER_GUIDE.md to a self-contained docs/user-guide.html.

Output is a single HTML file with embedded CSS, a sticky TOC sidebar,
auto light/dark theme (prefers-color-scheme), styled tables, code
blocks with horizontal scroll, and self-link anchors next to headings.

Re-run this script after editing USER_GUIDE.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SRC = HERE / "USER_GUIDE.md"
DST = HERE / "user-guide.html"

CSS = """
:root {
  --bg: #0f1115;
  --bg-elev: #161922;
  --bg-code: #11141b;
  --fg: #e6e9ef;
  --fg-muted: #8b93a6;
  --border: #232838;
  --accent: #62b4ff;
  --accent-soft: #2a3548;
  --shadow: 0 1px 0 0 rgba(0,0,0,0.04);
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #fdfdfd;
    --bg-elev: #f6f7f9;
    --bg-code: #f3f5f8;
    --fg: #1f2330;
    --fg-muted: #5b6478;
    --border: #e1e4ec;
    --accent: #1e6ad6;
    --accent-soft: #e2eeff;
  }
}

* { box-sizing: border-box; }

html { scroll-behavior: smooth; scroll-padding-top: 16px; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI",
    Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 16px;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}

.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  max-width: 1400px;
  margin: 0 auto;
}

aside.toc {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow-y: auto;
  padding: 32px 20px 32px 24px;
  border-right: 1px solid var(--border);
  background: var(--bg-elev);
}

aside.toc .brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0 0 6px;
  color: var(--fg);
}
aside.toc .brand-sub {
  font-size: 12px;
  color: var(--fg-muted);
  margin: 0 0 20px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

aside.toc ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
aside.toc li { margin: 0; }
aside.toc a {
  display: block;
  padding: 6px 10px;
  border-radius: 6px;
  color: var(--fg-muted);
  text-decoration: none;
  font-size: 14px;
  line-height: 1.4;
  border-left: 2px solid transparent;
}
aside.toc a:hover {
  color: var(--fg);
  background: var(--accent-soft);
}
aside.toc ul ul {
  margin-left: 14px;
  border-left: 1px solid var(--border);
  padding-left: 4px;
}
aside.toc ul ul a {
  font-size: 13px;
  padding: 4px 10px;
}

main {
  padding: 48px 56px 96px;
  max-width: 900px;
  min-width: 0;
}

h1, h2, h3, h4, h5, h6 {
  margin: 2em 0 0.6em;
  line-height: 1.25;
  letter-spacing: -0.01em;
  scroll-margin-top: 16px;
  position: relative;
}
h1 { font-size: 36px; margin-top: 0.2em; }
h2 {
  font-size: 26px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
h3 { font-size: 20px; }
h4 { font-size: 17px; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.06em; }

h1 a.anchor, h2 a.anchor, h3 a.anchor, h4 a.anchor {
  position: absolute;
  left: -22px;
  width: 22px;
  text-align: center;
  text-decoration: none;
  color: var(--accent);
  opacity: 0;
  transition: opacity 0.12s ease;
}
h1:hover a.anchor, h2:hover a.anchor, h3:hover a.anchor, h4:hover a.anchor { opacity: 1; }

p { margin: 0.85em 0; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; }
a:hover { border-bottom-color: var(--accent); }

ul, ol { padding-left: 1.4em; }
li { margin: 0.2em 0; }

hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 3em 0;
}

blockquote {
  margin: 1em 0;
  padding: 12px 16px;
  background: var(--accent-soft);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  color: var(--fg);
}
blockquote p { margin: 0.3em 0; }

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Cascadia Code",
    "Roboto Mono", Consolas, "Liberation Mono", monospace;
  font-size: 0.9em;
  background: var(--bg-code);
  padding: 0.15em 0.4em;
  border-radius: 4px;
  border: 1px solid var(--border);
}

pre {
  margin: 1em 0;
  padding: 16px 18px;
  background: var(--bg-code);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.55;
}
pre code {
  background: transparent;
  border: none;
  padding: 0;
  font-size: inherit;
}

table {
  border-collapse: collapse;
  margin: 1.4em 0;
  font-size: 14.5px;
  width: 100%;
  display: block;
  overflow-x: auto;
}
table thead { background: var(--bg-elev); }
th, td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
th {
  font-weight: 600;
  font-size: 13.5px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--fg-muted);
}
tbody tr:hover { background: var(--bg-elev); }

img { max-width: 100%; border-radius: 6px; }

.footer-meta {
  margin-top: 4em;
  padding-top: 1.5em;
  border-top: 1px solid var(--border);
  font-size: 13px;
  color: var(--fg-muted);
}

/* Mobile: hide sidebar, stack content */
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  aside.toc {
    position: static;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  main { padding: 32px 20px 64px; }
  h1 a.anchor, h2 a.anchor, h3 a.anchor, h4 a.anchor { display: none; }
}
"""


def slugify(text: str) -> str:
    """Match python-markdown's TOC slug behaviour reasonably."""
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s


def render() -> None:
    md_text = SRC.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=[
        "extra",          # tables, footnotes, attr_list, fenced_code…
        "sane_lists",
        "toc",
    ], extension_configs={
        "toc": {
            "permalink": "#",
            "permalink_class": "anchor",
            "permalink_title": "Link to this section",
        },
    })
    html_body = md.convert(md_text)
    toc_html = md.toc  # full nested <ul> with anchors

    # Remove the title-level entry from TOC (h1) to keep it tight
    toc_html = re.sub(
        r'^<div class="toc">\s*<ul>\s*<li><a[^>]*>[^<]*</a>(.*)</li>\s*</ul>\s*</div>$',
        r'<div class="toc"><ul>\1</ul></div>',
        toc_html.strip(),
        flags=re.DOTALL,
    )

    out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pcreative Studio — User Guide</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
  <aside class="toc">
    <h2 class="brand">Pcreative Studio</h2>
    <p class="brand-sub">User guide</p>
    {toc_html}
  </aside>
  <main>
    {html_body}
    <p class="footer-meta">Generated from <code>USER_GUIDE.md</code> by
    <code>generate-html.py</code>. Re-run after editing the markdown.</p>
  </main>
</div>
</body>
</html>
"""
    DST.write_text(out, encoding="utf-8")
    print(f"✓ wrote {DST.relative_to(HERE.parent)}  ({len(out):,} bytes)")


if __name__ == "__main__":
    render()
