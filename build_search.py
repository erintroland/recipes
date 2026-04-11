#!/usr/bin/env python3
"""
Recipe Box — Search Setup
Run this once to rebuild your index.html with the search box and
embedded search index. After this, new_post.py keeps it up to date.

Usage:
    python3 build_search.py

Run from inside your gh-pages-site/ folder.
"""

import re
import sys
import json
from pathlib import Path


def strip_html(html):
    return re.sub(r'<[^>]+>', '', html or '').strip()

def build_index_from_posts(posts_dir):
    entries = []
    for post_dir in sorted(posts_dir.iterdir(), reverse=True):
        if not post_dir.is_dir():
            continue
        html_file = post_dir / 'index.html'
        if not html_file.exists():
            continue

        slug = post_dir.name
        html = html_file.read_text(encoding='utf-8')

        title_match = re.search(r'<article>\s*<h1>(.*?)</h1>', html, re.DOTALL)
        title = strip_html(title_match.group(1)) if title_match else slug

        date_match = re.search(r'<div class="meta"><span>(.*?)</span>', html)
        date_str = date_match.group(1) if date_match else ''

        url_match = re.search(r'href="([^"]+)"[^>]*>→ View recipe', html)
        url = url_match.group(1) if url_match else ''

        content_match = re.search(r'<div class="content">(.*?)</div>\s*</article>', html, re.DOTALL)
        notes_plain = strip_html(content_match.group(1)) if content_match else ''
        notes_plain = re.sub(r'\s+', ' ', notes_plain).strip()

        entries.append({
            'title':   title,
            'slug':    slug,
            'date':    date_str,
            'url':     url,
            'notes':   notes_plain,
            'excerpt': notes_plain[:180],
        })
        print(f"  ✓ {slug}")
    return entries

def rebuild_index_with_search(index_path, search_index):
    content = index_path.read_text(encoding='utf-8')

    h1_match = re.search(r'<header><h1>(.*?)</h1>', content)
    site_title = h1_match.group(1) if h1_match else 'My Recipe Box'

    entries_match = re.search(r'<ul class="index-list"[^>]*>(.*?)</ul>', content, re.DOTALL)
    entries_html = entries_match.group(1).strip() if entries_match else ''

    index_json = json.dumps(search_index, ensure_ascii=False)

    new_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{site_title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="page-wrap">
  <header><h1>{site_title}</h1></header>
  <div class="search-wrap">
    <input type="search" id="search" placeholder="Search recipes…" autocomplete="off">
    <div id="search-results" class="search-results" style="display:none;"></div>
  </div>
  <ul class="index-list" id="post-list">
{entries_html}
  </ul>
</div>
<script>
const index = {index_json};
const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
const postList = document.getElementById('post-list');

searchInput.addEventListener('input', function() {{
  const q = this.value.trim().toLowerCase();
  if (!q) {{
    searchResults.style.display = 'none';
    searchResults.innerHTML = '';
    postList.style.display = '';
    return;
  }}
  postList.style.display = 'none';
  const matches = index.filter(p =>
    p.title.toLowerCase().includes(q) ||
    p.notes.toLowerCase().includes(q) ||
    p.url.toLowerCase().includes(q)
  );
  if (!matches.length) {{
    searchResults.innerHTML = '<p class="no-results">No recipes found.</p>';
  }} else {{
    searchResults.innerHTML = matches.map(p => `
      <div class="search-result">
        <a href="posts/${{p.slug}}/index.html">
          <div class="index-meta">${{p.date}}</div>
          <div class="post-title">${{p.title}}</div>
          ${{p.excerpt ? `<p class="post-excerpt">${{p.excerpt}}...</p>` : ''}}
        </a>
      </div>`).join('');
  }}
  searchResults.style.display = '';
}});
</script>
</body>
</html>
"""
    index_path.write_text(new_content, encoding='utf-8')

def main():
    site_root  = Path('.')
    index_path = site_root / 'index.html'
    posts_dir  = site_root / 'posts'

    if not index_path.exists() or not posts_dir.exists():
        print("Error: couldn't find index.html and posts/ in the current directory.")
        print("Run this script from inside your recipe box folder.")
        sys.exit(1)

    print("\nBuilding search index from existing posts…\n")
    search_index = build_index_from_posts(posts_dir)

    print(f"\nRebuilding index.html with embedded search…")
    rebuild_index_with_search(index_path, search_index)

    print(f"✓ Done! {len(search_index)} posts indexed.")
    print("Open index.html and try the search box.")
    print("From now on, new_post.py will keep the search index up to date automatically.\n")

if __name__ == '__main__':
    main()
