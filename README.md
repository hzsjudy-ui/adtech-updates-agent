# AdTech Updates Agent (Free Stack)

This starter pulls RSS feeds, sorts them by platform, and writes a Markdown digest to `output/digest.md`. It uses GitHub Actions on a daily schedule, so you pay nothing.

## Quick start
1. Create a new public repo.
2. Upload these files to the repo root.
3. Edit `feeds.yaml` and add real RSS URLs for each platform.
4. Enable GitHub Actions in the repo settings.
5. The digest will update daily around 09:05 SGT.
6. Optional: wire a Slack incoming webhook in a second job if you want push notifications.

## Local run
```bash
pip install -r requirements.txt
python agent.py
```

The digest is minimal by design. Summaries are taken from the feed and trimmed. You can later add model-based summarisation.
