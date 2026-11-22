# Earth Decoded

Faceless Earth & geography videos for the YouTube channel **Earth Decoded**:
GeoGlobeTales-style Shorts (one question, one map, ~60–80 s) and
"Why You'd Never…" long videos (8–12 min, 16:9).

**To upload: open [UPLOAD.md](UPLOAD.md).** Every row has the video, the text to paste
(title, description, tags, Spanish translations) and English + Spanish subtitle files.

## How it works
1. Scripts: `shorts/sNNN-name.json` and `longform/<slug>.json`. Every segment has `text` (English narration)
   and `es` (Spanish subtitle text).
2. Pushing a script starts the GitHub Action **Render videos** (free on public repos):
   - voice: [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) AI voice, run locally
   - images: Wikipedia/Wikimedia Commons (free licenses only, credited) and NASA (public domain)
   - maps: Natural Earth country shapes, drawn with a highlighted country, pin and border lines
   - word-by-word captions, animated number cards, comment-question cards
3. Output in `videos/` (Shorts) and `videos/long/` (long videos): `.mp4`, `.en.srt`, `.es.srt`, `.upload.txt`,
   `.credits.txt`; thumbnails and contact sheets in `previews/`. `UPLOAD.md` is rebuilt after every render.

## Visual types
| `visual.type` | Shows |
|---|---|
| `title` | photo + kicker pill + big title + question |
| `image` | photo from `wiki` (article lead image), `commons` (search), `files` (exact Commons files) or NASA `query`; optional `headline` |
| `map` | `extent`, `highlight` countries, `highlight_box`, `marker` + `label`, `line` + `line_label` |
| `card` | big animated number: `big`, `label`, `sub` |
| `question` (long only) | comment prompt: `q`, `sub` |
| `end` | photo + `big` + FOLLOW / SUBSCRIBE prompt |

Fonts: Inter (SIL Open Font License). Map data: Natural Earth (public domain).
