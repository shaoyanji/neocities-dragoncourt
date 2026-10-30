#!/usr/bin/env python3
"""lint.py — the site's own rules, runnable anywhere: CI, a laptop, the deploy script.

Checks, all against the files on disk:

  * the required pages exist (index.html, not_found.html, feed.xml);
  * every internal reference resolves — Neocities serves `foo.html` at `/foo`, so both
    spellings count, and a directory resolves through its index;
  * nothing is loaded from another origin (stylesheets, scripts, images, fonts);
  * feed.xml is well-formed and every item link points at a page that exists;
  * every post in site/blog/ carries a complete <!--post {...}--> header.

Usage: lint.py [site-dir]        (default: <this repo>/site)
Exit 0 = clean; exit 1 = problems, each printed on stderr.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("index.html", "not_found.html", "feed.xml")
POST_META = re.compile(r"^<!--post (\{.*\})-->\s*$", re.M)
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "//", "#")
SITE_ORIGIN = "dragoncourt.neocities.org"
ASSET_TAGS = {"script", "img", "iframe", "video", "audio", "source"}


class Refs(HTMLParser):
    """Collect links and assets with the tag that carried them."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        found = {key: value for key, value in attrs if value}
        href = found.get("href")
        src = found.get("src")
        if tag == "a" and href:
            self.links.append(href)
        if src and tag in ASSET_TAGS:
            self.assets.append(src)
        if tag == "link" and href and found.get("rel", "").split():
            if set(found["rel"].split()) & {"stylesheet", "icon", "preload", "manifest"}:
                self.assets.append(href)


def resolve(site: Path, target: str) -> Path | None:
    candidates = [target + "index.html"] if target.endswith("/") else [target, target + ".html"]
    for candidate in candidates:
        disk = site / candidate.lstrip("/")
        if disk.is_file():
            return disk
        index = disk / "index.html"
        if disk.is_dir() and index.is_file():
            return index
    return None


def check_posts(site: Path, problems: list[str]) -> int:
    posts = 0
    for page in sorted((site / "blog").glob("*.html")):
        if page.name == "index.html":
            continue
        posts += 1
        relative = page.relative_to(site)
        match = POST_META.search(page.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{relative}: no <!--post {{...}}--> header")
            continue
        try:
            meta = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            problems.append(f"{relative}: header is not JSON ({exc})")
            continue
        for field in ("title", "date", "tags", "summary"):
            if not meta.get(field):
                problems.append(f"{relative}: header is missing '{field}'")
        try:
            dt.date.fromisoformat(meta.get("date", ""))
        except ValueError:
            problems.append(f"{relative}: date '{meta.get('date')}' is not YYYY-MM-DD")
        if not isinstance(meta.get("tags"), list):
            problems.append(f"{relative}: tags must be a list")
    return posts


def lint(site: Path) -> tuple[list[str], int, int]:
    problems: list[str] = []

    for name in REQUIRED:
        if not (site / name).is_file():
            problems.append(f"{name} is missing")

    pages = sorted(site.rglob("*.html"))
    for page in pages:
        relative = page.relative_to(site)
        parser = Refs()
        parser.feed(page.read_text(encoding="utf-8"))
        parser.close()

        for link in parser.links:
            if link.startswith(SKIP_SCHEMES):
                continue
            target = link.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if not target.startswith("/"):
                problems.append(f"{relative}: relative link '{link}' (use a root-relative path)")
            elif resolve(site, target) is None:
                problems.append(f"{relative}: dead link '{link}'")

        for asset in parser.assets:
            if asset.startswith(("http://", "https://", "//")):
                problems.append(f"{relative}: asset loaded from another origin: {asset}")

    feed = site / "feed.xml"
    if feed.is_file():
        try:
            tree = ET.parse(feed)
        except ET.ParseError as exc:
            problems.append(f"feed.xml: not well-formed ({exc})")
        else:
            for item in tree.findall("./channel/item"):
                link = (item.findtext("link") or "").strip()
                if not link:
                    problems.append("feed.xml: an item has no <link>")
                    continue
                path = urlparse(link)
                if path.netloc and path.netloc != SITE_ORIGIN:
                    problems.append(f"feed.xml: item link is off-site: {link}")
                elif resolve(site, path.path) is None:
                    problems.append(f"feed.xml: item link does not resolve: {link}")

    posts = check_posts(site, problems)
    return problems, len(pages), posts


def main() -> int:
    site = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "site"
    if not site.is_dir():
        print(f"lint: {site} is not a directory", file=sys.stderr)
        return 1

    problems, page_count, post_count = lint(site)
    if problems:
        print(f"lint: FAILED — {len(problems)} problem(s) in {site}", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(
        f"lint: ok — {page_count} pages ({post_count} posts), all references resolve, "
        "feed parses, no off-site assets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
