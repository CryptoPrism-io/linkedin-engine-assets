#!/usr/bin/env python3
"""Render an HTML animation to a small mp4 for the linkedin-engine Buffer pipeline.

Flow:
  1. Opens the HTML in a headless browser at 1080x1350, records the animation
     via Playwright's record_video.
  2. Converts the recorded webm to mp4 with ffmpeg (small, H.264).
  3. Writes it to videos/<name>.mp4 (or videos/page/<name>.mp4 for the Page),
     then prints the public raw.githubusercontent URL to use in the post.

The git push is intentionally left to the user (no auto-push). Keep clips short
(30-90s) so the mp4 stays well under GitHub's 100MB per-file limit.

Usage:
  python scripts/make_video.py --html path/to/animation.html --out slot-27.mp4
  python scripts/make_video.py --html path/to/page_anim.html --out page/slot-21.mp4
  # optional: --duration 45 (seconds to record; defaults to 45)
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
W, H = 1080, 1350

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright not installed: pip install playwright && playwright install chromium")


def main():
    ap = argparse.ArgumentParser(description="Render HTML animation to mp4")
    ap.add_argument("--html", required=True, help="path to the HTML animation file")
    ap.add_argument("--out", required=True, help="output name, e.g. slot-27.mp4 or page/slot-21.mp4")
    ap.add_argument("--duration", type=int, default=45, help="seconds to record (default 45)")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        sys.exit(f"html not found: {html_path}")

    out = REPO / "videos" / args.out
    if out.suffix.lower() != ".mp4":
        sys.exit("--out must end in .mp4")
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp_webm = out.with_suffix(".webm")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=str(tmp_webm.parent),
            record_video_size={"width": W, "height": H},
        )
        page = ctx.new_page()
        page.goto(html_path.as_uri())
        page.wait_for_timeout(args.duration * 1000)
        video = page.video
        page.close()
        ctx.close()
        browser.close()
        if video is None:
            sys.exit("no video captured")
        recorded = video.path()

    # record_video writes to a temp dir; convert the webm to the final mp4
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(recorded), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "28", "-movflags", "+faststart", str(out)],
        check=True,
    )

    size_mb = out.stat().st_size / (1024 * 1024)
    url = f"https://raw.githubusercontent.com/CryptoPrism-io/linkedin-engine-assets/main/videos/{args.out}"
    print(f"wrote {out} ({size_mb:.1f} MB)")
    print(f"public url: {url}")
    print("next: git add videos/ && git commit && git push  (in this repo)")


if __name__ == "__main__":
    main()
