# dragoncourt.neocities.org

The outpost site: hand-written HTML, one stylesheet, one small script, published to
Neocities. Nothing is generated — `site/` **is** the artifact, so what you edit is what
gets served.

| | |
| :--- | :--- |
| Live | https://dragoncourt.neocities.org |
| Site name | `dragoncourt` (Neocities account, created 2024-10-19) |
| Source | `projects/neocities-dragoncourt/site/` |
| Deploy | `task neocities:deploy` (in `nixconfig`; this repo holds content, not keys) |
| Credential | `NEOCITIES.API.KEY` in `modules/secrets/apikeys.yaml` (nixconfig) |

The authoring tasks and the deploy script live in the nixconfig task plane, because that
is where the encrypted API key and the shared gates are. This repository is the site
source, checked out at `projects/neocities-dragoncourt` as a submodule.

## Pages

| Path | What |
| :--- | :--- |
| `index.html` | landing page: hero, latest entries, audit block, the court |
| `blog/index.html` | the log, newest first |
| `blog/*.html` | one file per entry, dated, never edited after the fact |

Neocities serves `foo.html` at `/foo` and 301s the `.html` form, so every internal
link, canonical URL and feed `<guid>` uses the extensionless path — the links resolve
in one request, and the canonical URL is the one the server actually returns.
| `about.html` | what the site is plus the colophon |
| `not_found.html` | Neocities' custom 404 — the filename is the contract |
| `feed.xml` | RSS 2.0, three entries |
| `style.css`, `app.js` | the only shared assets; no external origins |

`neocities.png` is the host's own badge and is not edited here.

## Write

`task neocities:menu` is the gum TUI for all of it; each item is also its own task.

| Task | What it does |
| :--- | :--- |
| `neocities:new` | gum form (title, date, tags, summary, body) → `drafts/<slug>.html`, offers to publish |
| `neocities:edit` | metadata form, body in `$EDITOR`, or both; offers an upload |
| `neocities:publish` | moves a draft into `site/blog/` and re-renders |
| `neocities:draft` | moves an entry back to `drafts/` and re-renders |
| `neocities:delete` | confirm prompt, then delete the file and re-render |
| `neocities:list` | date, title, status, tags |
| `neocities:render` | rebuild the log rows, home cards, feed and entry count |
| `neocities:preview` | serve `site/` on 127.0.0.1:8080 |
| `neocities:deploy` | render, then the verified push below |

A post carries its own metadata in the first line, and the listings are projections of
it — never hand-edited:

```html
<!--post {"title": "…", "date": "2026-10-30", "tags": ["court"],
          "status": "published", "summary": "…"}-->
```

`drafts/` is local state: the push only walks `site/`, so an unpublished draft cannot
leak. The generated regions are `<!-- entries:start|end -->` in `site/blog/index.html`,
`<!-- latest:start|end -->` in `site/index.html`, and `<!-- count -->` in the log's
status bar.

## Deploy

`task dev:site:deploy:neocities` runs `scripts/task/neocities-push.sh`, which:

1. runs `scripts/lint.py` here — the same script `.github/workflows/lint.yml` runs on
   every push, so CI and deploy cannot disagree about what is valid: references resolve,
   the feed parses and its items resolve, every post has a complete header, and nothing
   is loaded from another origin;
2. asks the API which local files already match by SHA-1 (`/api/upload_hash`) and uploads
   only the differences — one multipart request, never a burst;
3. downloads every uploaded path back and compares bytes (`/api/download`), so the claim
   "deployed" is backed by the served file, not by the upload's own message.

Remote files that no longer exist locally are **not** deleted. Pruning is destructive and
Neocities' delete endpoint cannot be undone, so it is a deliberate separate act
(`--prune`, which lists before it removes).

Manual equivalents for a quick look:

```bash
curl -H "Authorization: Bearer $KEY" https://neocities.org/api/list | jq
curl -H "Authorization: Bearer $KEY" https://neocities.org/api/info | jq .info
```

## Rules for edits

- Keep the page shell identical across files (header, status bar, footer) — it is copied
  by hand, so a change belongs in every page at once.
- New entry: add `blog/<slug>.html`, a row in `blog/index.html`, a card on `index.html`,
  an `<item>` in `feed.xml`, and update the `entries` count in the two status bars. Link it
  as `/blog/<slug>`, never `/blog/<slug>.html`.
- Nothing loads from another origin. No analytics, no cookies, no CDN fonts.
- The site targets old browsers: root-relative links, no modules, no `color-mix`, and
  every animation is disabled under `prefers-reduced-motion`.
