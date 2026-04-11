#!/usr/bin/env python3
"""
Recipe Box — Rename Site
Updates the site title in all post HTML files to match index.html.

Usage:
    python3 rename_site.py

Run from inside your gh-pages-site/ folder.
"""

import re
import sys
from pathlib import Path


def main():
    site_root  = Path('.')
    index_path = site_root / 'index.html'
    posts_dir  = site_root / 'posts'

    if not index_path.exists() or not posts_dir.exists():
        print("Error: couldn't find index.html and posts/ in the current directory.")
        sys.exit(1)

    # Read site title from index.html
    content = index_path.read_text(encoding='utf-8')
    h1_match = re.search(r'<header><h1>(.*?)</h1>', content)
    if not h1_match:
        print("Error: couldn't find the site title in index.html.")
        sys.exit(1)
    site_title = h1_match.group(1)
    print(f"\nUpdating all posts to site title: '{site_title}'\n")

    updated = 0
    for post_dir in posts_dir.iterdir():
        if not post_dir.is_dir():
            continue
        html_file = post_dir / 'index.html'
        if not html_file.exists():
            continue

        html = html_file.read_text(encoding='utf-8')

        # Update <title> tag (replaces "Whatever — Old Name" with "Whatever — New Name")
        html = re.sub(
            r'(<title>.*? — ).*?(</title>)',
            lambda m: m.group(1) + site_title + m.group(2),
            html
        )

        # Update header h1 link text
        html = re.sub(
            r'(<header><h1><a[^>]+>).*?(</a></h1></header>)',
            lambda m: m.group(1) + site_title + m.group(2),
            html
        )

        html_file.write_text(html, encoding='utf-8')
        print(f"  ✓ posts/{post_dir.name}/index.html")
        updated += 1

    print(f"\n✓ Done! Updated {updated} post files.\n")


if __name__ == '__main__':
    main()
