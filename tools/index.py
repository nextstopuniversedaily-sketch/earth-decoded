"""Write UPLOAD.md: one row per rendered video with download links and its publish slot."""
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get("GITHUB_REPOSITORY", "nextstopuniversedaily-sketch/earth-decoded")
RAW = f"https://github.com/{REPO}/raw/main/"


def row(publish, kind, title, base, mp4):
    if not os.path.exists(os.path.join(ROOT, mp4)):
        return f"| {publish} | {kind} | {title} | rendering… | | | |"
    return (f"| {publish} | {kind} | {title} | [video]({RAW}{mp4}) | [title, description, tags]({RAW}{base}.upload.txt)"
            f" | [EN]({RAW}{base}.en.srt) | [ES]({RAW}{base}.es.srt) |")


rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "shorts", "*.json"))):
    ep = json.load(open(f))
    stem = f"videos/s{ep['number']:03d}"
    rows.append((ep.get("publish", "~"), row(ep.get("publish", "—"), "Short", ep.get("yt_title", ep["title"]), stem, stem + ".mp4")))
for f in sorted(glob.glob(os.path.join(ROOT, "longform", "*.json"))):
    ep = json.load(open(f))
    stem = f"videos/long/{ep['slug']}"
    thumb = f"previews/thumb-{ep['slug']}.jpg"
    r = row(ep.get("publish", "—"), "Long", ep.get("yt_title", ep["title"]), stem, stem + ".mp4")
    if os.path.exists(os.path.join(ROOT, thumb)):
        r = r.rstrip(" |") + f" · [thumbnail]({RAW}{thumb}) |"
    rows.append((ep.get("publish", "~"), r))
rows.sort(key=lambda x: x[0])

out = ["# Earth Decoded – videos to upload", "",
       "Newest scripts are rendered automatically. For each row: download the video, open YouTube Studio → Create → Upload,",
       "paste the title, description and tags from the text file, set **Schedule** to the publish time (Mexico City),",
       "then under **Subtitles** add English (.en.srt) and Spanish (.es.srt). Long videos: also upload the thumbnail.", "",
       "| Publish (Mexico City) | Type | Title | Video | Text to paste | Subtitles EN | Subtitles ES |",
       "|---|---|---|---|---|---|---|"] + [r for _, r in rows]
open(os.path.join(ROOT, "UPLOAD.md"), "w").write("\n".join(out) + "\n")
print(f"UPLOAD.md: {len(rows)} videos")
