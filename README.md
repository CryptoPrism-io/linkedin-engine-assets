# linkedin-engine-assets

Public media hosting for the `linkedin-engine` Buffer post pipeline. Buffer's API requires
posted media to be a publicly reachable URL (no upload endpoint) — this repo holds only
infographic PNGs and short videos, no post text, credentials, or other business content.

Images: `infographics/slot-NN.png` (personal) and `infographics/page/slot-NN.png` (Page),
referenced from Buffer posts via
`https://raw.githubusercontent.com/CryptoPrism-io/linkedin-engine-assets/main/infographics/slot-NN.png`.

Videos: `videos/slot-NN.mp4` (personal) and `videos/page/slot-NN.mp4` (Page), referenced via
`https://raw.githubusercontent.com/CryptoPrism-io/linkedin-engine-assets/main/videos/slot-NN.mp4`.

Guidelines for videos:
- Keep files small (well under GitHub's 100MB per-file limit; aim < 50MB). These are
  30-90 second 1080x1350 HTML-rendered clips.
- Must be a publicly fetchable mp4 so Buffer can read it (no auth, no signed URLs).
- Generate locally (Playwright `record_video` + ffmpeg), then `git add videos/ && git push`.

