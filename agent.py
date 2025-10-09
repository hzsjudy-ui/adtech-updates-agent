
import os, sys, time, json, yaml, hashlib, re, feedparser, markdownify
from datetime import datetime, timedelta, timezone

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def hash_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]

def within_lookback(published_parsed, lookback_hours, tz_offset_hours=8):
    if not published_parsed:
        return True  # keep if unknown
    published = datetime(*published_parsed[:6], tzinfo=timezone(timedelta(hours=0)))
    now = datetime.now(timezone.utc)
    return (now - published) <= timedelta(hours=lookback_hours)

def classify(entry, platforms):
    text = " ".join([entry.get("title",""), entry.get("summary","")]).lower()
    best = "industry"
    for k, v in platforms.items():
        kws = v.get("keywords", [])
        score = sum(1 for w in kws if w in text)
        if score >= 1:
            best = k
            break
    return best

def collect(feeds_cfg):
    lookback_hours = feeds_cfg.get("lookback_hours", 48)
    platforms = feeds_cfg.get("platforms", {})
    items = []
    for platform_key, cfg in platforms.items():
        for feed in cfg.get("feeds", []):
            try:
                d = feedparser.parse(feed)
            except Exception as e:
                print(f"[warn] failed feed {feed}: {e}", file=sys.stderr)
                continue
            for e in d.entries:
                if not within_lookback(e.get("published_parsed"), lookback_hours):
                    continue
                url = e.get("link") or ""
                title = e.get("title") or "(no title)"
                desc = e.get("summary") or ""
                cat = classify(e, platforms)
                uid = hash_id(url + title)
                items.append({
                    "id": uid,
                    "title": title.strip(),
                    "url": url,
                    "published": e.get("published") or "",
                    "platform": cat,
                    "source_feed": d.feed.get("title", feed),
                    "summary_html": desc
                })
    # de-duplicate by URL+title hash
    uniq = {}
    for it in items:
        uniq[it["id"]] = it
    return list(uniq.values())

def render_markdown(items, tz="Asia/Singapore"):
    from datetime import datetime
    by_platform = {}
    for it in items:
        by_platform.setdefault(it["platform"], []).append(it)
    # sort within platform by published string if present
    for k in by_platform:
        by_platform[k].sort(key=lambda x: x.get("published",""), reverse=True)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    out = [f"# AdTech Updates Digest\n\nGenerated: {now}\n"]
    platforms_order = sorted(by_platform.keys())
    for plat in platforms_order:
        out.append(f"## {plat.upper()} ({len(by_platform[plat])})\n")
        for it in by_platform[plat]:
            text = markdownify.markdownify(it["summary_html"], strip=["a","img"]) if it.get("summary_html") else ""
            blurb = re.sub(r"\s+", " ", text).strip()
            if len(blurb) > 400:
                blurb = blurb[:400] + "…"
            out.append(f"- **{it['title']}**  \n  Source: {it['source_feed']}  \n  Link: {it['url']}  \n  Published: {it.get('published','')}  \n  Summary: {blurb}")
        out.append("")
    return "\n".join(out)

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    feeds_cfg = load_yaml(os.path.join(repo_dir, "feeds.yaml"))
    items = collect(feeds_cfg)
    md = render_markdown(items, tz=feeds_cfg.get("timezone","Asia/Singapore"))
    outdir = os.path.join(repo_dir, "output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "digest.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {len(items)} items to output/digest.md")

if __name__ == "__main__":
    main()
