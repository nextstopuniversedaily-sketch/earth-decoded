"""Write UPLOAD.md: one section per rendered video with download links and copy-ready text."""
import datetime, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get("GITHUB_REPOSITORY", "nextstopuniversedaily-sketch/earth-decoded")
RAW = f"https://github.com/{REPO}/raw/main/"


def nice(publish):
    try:
        d = datetime.datetime.strptime(publish, "%Y-%m-%d %H:%M")
        return d.strftime("%a %b %d, %I:%M %p").replace(" 0", " ")
    except Exception:  # noqa: BLE001
        return publish


def block(text):
    return "```text\n" + (text or "").strip() + "\n```"


def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))


def section(n, ep, kind, base, mp4, thumb, chapters=None):
    title = ep.get("yt_title", ep.get("title", ""))
    out = [f"## {n}. {nice(ep.get('publish', ''))} · {kind}", f"**{title}**", ""]
    if not exists(mp4):
        return out + ["_Still rendering — check back in a few minutes._", ""]
    out.append(f"- ⬇️ **Video:** [download]({RAW}{mp4})")
    if exists(thumb):
        if kind == "Short":
            out.append(f"- 🖼️ **Thumbnail:** already built into the first frame of the video — nothing to do. "
                       f"([image]({RAW}{thumb}) if Studio offers \"Upload thumbnail\")")
        else:
            out.append(f"- 🖼️ **Thumbnail:** [download]({RAW}{thumb}) → in Studio: Details → Thumbnail → Upload file")
    out.append(f"- 💬 **Subtitles:** [English .srt]({RAW}{base}.en.srt) · [Spanish .srt]({RAW}{base}.es.srt)")
    desc = ep.get("description", "")
    if chapters:
        desc += "\n\nChapters:\n" + "\n".join(chapters)
    out += ["", "**Title** (copy):", block(title), "**Description** (copy):", block(desc),
            "**Tags** (copy):", block(", ".join(ep.get("tags", []))),
            "<details><summary>Spanish title & description (optional: Studio → Languages → Add translation)</summary>", "",
            block(ep.get("yt_title_es", "")), block(ep.get("description_es", "")), "</details>", ""]
    return out


items = []
for f in glob.glob(os.path.join(ROOT, "shorts", "*.json")):
    ep = json.load(open(f))
    stem = f"s{ep['number']:03d}"
    items.append((ep.get("publish", "~"), ep, "Short", f"videos/{stem}", f"videos/{stem}.mp4", f"previews/sthumb-{stem}.jpg", None))
for f in glob.glob(os.path.join(ROOT, "longform", "*.json")):
    ep = json.load(open(f))
    slug = ep["slug"]
    chap_file = os.path.join(ROOT, "videos", "long", slug + ".chapters.txt")
    chapters = [l for l in open(chap_file).read().splitlines() if l.strip()] if os.path.exists(chap_file) else None
    items.append((ep.get("publish", "~"), ep, "Long video", f"videos/long/{slug}", f"videos/long/{slug}.mp4",
                  f"previews/thumb-{slug}.jpg", chapters))
items.sort(key=lambda x: x[0])

out = ["# Earth Decoded – videos to upload", "",
       "**For each video below:**",
       "1. Click **Video: download**.",
       "2. YouTube Studio → **Create → Upload videos** → pick the file.",
       "3. Copy the **Title**, **Description** and **Tags** below into the same boxes (each grey box has a copy button on the right).",
       "4. **Thumbnail:** Shorts — nothing to do, it's the first frame. Long videos — click *Upload file* under Thumbnail and pick the downloaded thumbnail.",
       "5. Audience: **No, it's not made for kids**. Show more → Category: **Education**.",
       "6. Subtitles (optional but recommended): Subtitles → Add language → English → Upload file → *With timing* → the English .srt; repeat for Spanish.",
       "7. Visibility → **Schedule** → the date and time shown in the heading (Mexico City time).", ""]
for i, it in enumerate(items, 1):
    out += section(i, it[1], it[2], it[3], it[4], it[5], it[6])
open(os.path.join(ROOT, "UPLOAD.md"), "w").write("\n".join(out) + "\n")
print(f"UPLOAD.md: {len(items)} videos")
