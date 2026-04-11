#!/usr/bin/env python3
"""
Recipe Box — New Post Creator
Prompts for a recipe title, URL, and notes, then creates a new post
HTML file and updates index.html (with embedded search index).

Usage:
    python3 new_post.py

Run this from inside your gh-pages-site/ folder.
"""

import re
import sys
import json
from pathlib import Path
from datetime import datetime


# ── Helpers ────────────────────────────────────────────────────────────────────

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def format_date(dt):
    return dt.strftime('%B %-d, %Y')

def ask(prompt, required=True):
    while True:
        val = input(prompt).strip()
        if val or not required:
            return val
        print("  (this field is required, please enter a value)")

def ask_multiline(prompt):
    print(prompt)
    print("  (press Enter twice when done)")
    lines = []
    while True:
        line = input()
        if line == '' and lines and lines[-1] == '':
            break
        lines.append(line)
    return '\n'.join(lines).strip()

def notes_to_html(notes):
    if not notes:
        return ''
    paras = [p.strip() for p in re.split(r'\n{2,}', notes) if p.strip()]
    html_paras = []
    for p in paras:
        p_with_breaks = p.replace('\n', '<br>')
        html_paras.append(f'    <p>{p_with_breaks}</p>')
    return '\n'.join(html_paras)

def strip_html(html):
    return re.sub(r'<[^>]+>', '', html or '').strip()


# ── Search index builder ───────────────────────────────────────────────────────

def build_index_from_posts(posts_dir, new_entry=None):
    """Scan all post folders and build a search index list."""
    entries = []

    # Add new entry first (newest)
    if new_entry:
        entries.append(new_entry)

    for post_dir in sorted(posts_dir.iterdir(), reverse=True):
        if not post_dir.is_dir():
            continue
        slug = post_dir.name
        if new_entry and slug == new_entry['slug']:
            continue
        html_file = post_dir / 'index.html'
        if not html_file.exists():
            continue

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

    return entries


# ── HTML builders ──────────────────────────────────────────────────────────────

def build_post_html(title, recipe_url, notes_html, date_str, site_title, prev_post=None, next_post=None):
    recipe_link = f'<p><a href="{recipe_url}" target="_blank" rel="noopener">→ View recipe</a></p>' if recipe_url else ''
    prev_link = f'<a href="../../posts/{prev_post["slug"]}/index.html">← {prev_post["title"]}</a>' if prev_post else '<span></span>'
    next_link = f'<a href="../../posts/{next_post["slug"]}/index.html">{next_post["title"]} →</a>' if next_post else '<span></span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — {site_title}</title>
<link rel="stylesheet" href="../../style.css">
</head>
<body>
<div class="page-wrap">
  <header><h1><a href="../../index.html">{site_title}</a></h1></header>
  <article>
    <h1>{title}</h1>
    <div class="meta"><span>{date_str}</span></div>
    <div class="content">
{recipe_link}
{notes_html}
    </div>
  </article>
  <nav class="post-nav">
    {prev_link}
    {next_link}
  </nav>
</div>
</body>
</html>
"""

def rebuild_index(site_title, new_entry_html, existing_entries_html, search_index):
    new_list = new_entry_html + '\n' + existing_entries_html if existing_entries_html else new_entry_html
    index_json = json.dumps(search_index, ensure_ascii=False)
    return f"""<!DOCTYPE html>
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
{new_list}
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


# ── Index reader ───────────────────────────────────────────────────────────────

def read_index_entries(index_path):
    content = index_path.read_text(encoding='utf-8')
    h1_match = re.search(r'<header><h1>(.*?)</h1>', content)
    site_title = h1_match.group(1) if h1_match else 'My Recipe Box'
    entries_match = re.search(r'<ul class="index-list"[^>]*>(.*?)</ul>', content, re.DOTALL)
    entries_html = entries_match.group(1).strip() if entries_match else ''
    return site_title, entries_html

def build_new_index_entry(title, slug, date_str, excerpt):
    excerpt_html = f'<p class="post-excerpt">{excerpt[:180]}…</p>' if excerpt else ''
    return f"""  <li>
    <a href="posts/{slug}/index.html">
      <div class="index-meta">{date_str}</div>
      <div class="post-title">{title}</div>
      {excerpt_html}
    </a>
  </li>"""

def get_first_post_from_index(entries_html):
    match = re.search(r'href="posts/([^/]+)/index\.html"[^>]*>.*?<div class="post-title">(.*?)</div>', entries_html, re.DOTALL)
    if match:
        return {'slug': match.group(1), 'title': re.sub(r'<[^>]+>', '', match.group(2)).strip()}
    return None


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    site_root  = Path('.')
    index_path = site_root / 'index.html'
    posts_dir  = site_root / 'posts'

    if not index_path.exists() or not posts_dir.exists():
        print("Error: couldn't find index.html and posts/ in the current directory.")
        print("Run this script from inside your recipe box folder.")
        sys.exit(1)

    print("\n── New Recipe Post ──────────────────────────\n")

    title      = ask("Recipe name: ")
    recipe_url = ask("Recipe URL (leave blank if none): ", required=False)
    print()
    notes      = ask_multiline("Your notes:")

    now        = datetime.now()
    date_str   = format_date(now)
    slug       = slugify(title)
    notes_html = notes_to_html(notes)
    excerpt    = strip_html(notes_to_html(notes))[:180] if notes else ''

    site_title, existing_entries = read_index_entries(index_path)
    prev_post = get_first_post_from_index(existing_entries)

    # Write new post file
    post_dir = posts_dir / slug
    if post_dir.exists():
        print(f"\nWarning: posts/{slug}/ already exists.")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Cancelled.")
            sys.exit(0)
    post_dir.mkdir(parents=True, exist_ok=True)

    post_html = build_post_html(title, recipe_url, notes_html, date_str, site_title, next_post=prev_post)
    (post_dir / 'index.html').write_text(post_html, encoding='utf-8')
    print(f"\n✓ Created posts/{slug}/index.html")

    # Update prev post's next-link
    if prev_post:
        prev_post_path = posts_dir / prev_post['slug'] / 'index.html'
        if prev_post_path.exists():
            prev_html = prev_post_path.read_text(encoding='utf-8')
            new_next_link = f'<a href="../../posts/{slug}/index.html">{title} →</a>'
            prev_html = re.sub(
                r'(<nav class="post-nav">.*?)(<span></span>)(.*?</nav>)',
                lambda m: m.group(1) + new_next_link + m.group(3),
                prev_html, flags=re.DOTALL, count=1
            )
            prev_post_path.write_text(prev_html, encoding='utf-8')
            print(f"✓ Updated next-link in posts/{prev_post['slug']}/index.html")

    # Build search index from all posts
    new_search_entry = {
        'title':   title,
        'slug':    slug,
        'date':    date_str,
        'url':     recipe_url or '',
        'notes':   strip_html(notes_html),
        'excerpt': excerpt,
    }
    search_index = build_index_from_posts(posts_dir, new_entry=new_search_entry)

    # Rebuild index.html with embedded search index
    new_entry_html = build_new_index_entry(title, slug, date_str, excerpt)
    new_index = rebuild_index(site_title, new_entry_html, existing_entries, search_index)
    index_path.write_text(new_index, encoding='utf-8')
    print(f"✓ Updated index.html (search index embedded)")

    print(f"\nDone! New post: posts/{slug}/index.html")
    print(f"Open index.html in your browser to see it.\n")


if __name__ == '__main__':
    main()
