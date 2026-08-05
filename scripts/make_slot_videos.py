#!/usr/bin/env python3
"""Batch-generate storytelling videos from existing slot HTML files.

Injects a staggered reveal animation (masthead -> badge -> headline -> body
zones -> takeaway -> footer) into each static slot HTML, then records ~10s of
video at 1080x1350 via Playwright + ffmpeg.

Usage:
  python make_slot_videos.py --dir <out|out_page> --out-suffix <personal|page> --slots 31,32,33
  # renders videos/eli5-style: videos/<suffix>/slot-NN.mp4  (flat: videos/slot-NN.mp4 if no suffix)
"""
import argparse
import re
import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent.parent  # linkedin-engine-assets
ENGINE = HERE.parent / "linkedin-engine"        # sibling repo with the HTML
SRC_DIR = ENGINE / "assets" / "infographics"
VID = HERE / "videos"

ANIM = """
<style>
/* storytelling reveal: zones fade in staggered, hold at full */
@keyframes reveal { from{opacity:0; transform:translateY(14px)} to{opacity:1; transform:none} }
@keyframes revealCard { from{opacity:0; transform:translateY(18px)} to{opacity:1; transform:none} }
.canvas > .masthead { opacity:0; animation:reveal .6s .1s forwards; }
.canvas > .mastrule { opacity:0; animation:reveal .5s .5s forwards; }
.canvas > .badgerow { opacity:0; animation:reveal .5s .9s forwards; }
.canvas > .badge { opacity:0; animation:reveal .5s .9s forwards; }
.canvas > .headline { opacity:0; animation:reveal .6s 1.3s forwards; }
.canvas > .body { opacity:0; animation:reveal .6s 2.0s forwards; }
.body > * { opacity:0; animation:revealCard .6s ease both; }
.body > *:nth-child(1) { animation-delay:2.0s; }
.body > *:nth-child(2) { animation-delay:2.7s; }
.body > *:nth-child(3) { animation-delay:3.4s; }
.body > *:nth-child(4) { animation-delay:4.1s; }
.body > *:nth-child(5) { animation-delay:4.8s; }
.body > *:nth-child(6) { animation-delay:5.5s; }
.canvas > .takeaway { opacity:0; animation:reveal .6s 6.2s forwards; }
.canvas > .footer { opacity:0; animation:reveal .5s 6.8s forwards; }
</style>
"""


def inject_animation(html: str) -> str:
    """Insert the reveal CSS before </head>."""
    if "</head>" in html:
        return html.replace("</head>", ANIM + "</head>", 1)
    return ANIM + html


def to_mp4(webm: Path, out: Path):
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "28", "-movflags", "+faststart", str(out)],
        check=True, capture_output=True,
    )


def record(html: Path, out: Path, duration: int = 10):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 1080, "height": 1350},
            record_video_dir=str(VID),
            record_video_size={"width": 1080, "height": 1350},
        )
        page = ctx.new_page()
        page.goto(html.as_uri())
        page.wait_for_timeout(duration * 1000)
        video = page.video
        page.close()
        ctx.close()
        browser.close()
        if video is None:
            raise RuntimeError("no video captured")
        recorded = Path(video.path())
        to_mp4(recorded, out)
        # clean the webm intermediate
        if recorded.exists():
            recorded.unlink()
    print(f"[ok] {out.name} ({out.stat().st_size/1024:.0f} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="out or out_page")
    ap.add_argument("--prefix", default="slot-", help="html filename prefix")
    ap.add_argument("--slots", required=True, help="comma list of slot numbers, or 'all'")
    ap.add_argument("--subdir", default=None, help="videos subdir: page/ or None")
    ap.add_argument("--duration", type=int, default=10)
    a = ap.parse_args()

    src = SRC_DIR / a.dir
    slots = list(range(0, 999)) if a.slots == "all" else [int(s) for s in a.slots.split(",")]

    vdir = VID / a.subdir if a.subdir else VID
    vdir.mkdir(parents=True, exist_ok=True)

    tmp = VID / "_anim.html"
    for n in slots:
        html = src / f"{a.prefix}{n:02d}.html"
        if not html.exists():
            print(f"[skip] {html.name} not found")
            continue
        out = vdir / f"slot-{n:02d}.mp4"
        if out.exists():
            print(f"[skip] {out.name} exists")
            continue
        injected = inject_animation(html.read_text(encoding="utf-8"))
        tmp.write_text(injected, encoding="utf-8")
        record(tmp, out, a.duration)
    if tmp.exists():
        tmp.unlink()
    print("done")


if __name__ == "__main__":
    main()
