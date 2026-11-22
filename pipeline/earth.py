"""Earth Decoded extras: animated-style maps, word-highlight captions,
English + Spanish subtitle files and copy-paste upload sheets.

Map visual spec (in a segment's "visual"):
  {"type": "map",
   "extent": [lon_min, lon_max, lat_min, lat_max],   # what the frame shows
   "highlight": ["Mexico"],                          # Natural Earth country names (gold)
   "highlight_box": [lon_min, lon_max, lat_min, lat_max],  # optional: only part of a country (e.g. Alaska)
   "marker": [lon, lat], "label": "Mexico City",     # optional pulsing pin
   "line": [[lon, lat], [lon, lat]], "line_label": "49th parallel"}  # optional border/route line
"""
import io, os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_world = None


def world():
    global _world
    if _world is None:
        import warnings
        warnings.filterwarnings("ignore")
        import geopandas as gpd
        _world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    return _world


def map_image(v, size, font_path=None):
    """Render a map to a PIL image of exactly `size` (w, h), dark 'satellite' style."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from shapely.geometry import box

    w, h = size
    dpi = 100
    lon0, lon1, lat0, lat1 = v["extent"]
    # keep the frame's aspect: widen the shorter side of the extent
    want = w / h
    k = max(0.25, np.cos(np.radians((lat0 + lat1) / 2)))   # shrink longitudes at high latitudes
    have = (lon1 - lon0) * k / (lat1 - lat0)
    if have < want:
        pad = ((lat1 - lat0) * want / k - (lon1 - lon0)) / 2
        lon0, lon1 = lon0 - pad, lon1 + pad
    else:
        pad = ((lon1 - lon0) * k / want - (lat1 - lat0)) / 2
        lat0, lat1 = lat0 - pad, lat1 + pad

    wd = world()
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#0a2b47")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor("#0a2b47")
    # ocean gradient
    grad = np.linspace(0, 1, 256)[:, None]
    ocean = np.dstack([0.02 + 0.05 * grad, 0.10 + 0.14 * grad, 0.20 + 0.20 * grad])
    ax.imshow(ocean, extent=(lon0, lon1, lat0, lat1), aspect="auto", zorder=0, origin="lower")
    for g in np.arange(-180, 181, 10):
        ax.plot([g, g], [-90, 90], color="#ffffff", alpha=0.05, lw=1, zorder=1)
    for g in np.arange(-90, 91, 10):
        ax.plot([-180, 180], [g, g], color="#ffffff", alpha=0.05, lw=1, zorder=1)
    wd.plot(ax=ax, color="#21463b", edgecolor="#6f9c86", linewidth=1.2, zorder=2, aspect=None)
    hl = v.get("highlight") or []
    if hl:
        sel = wd[wd.name.isin(hl)]
        if v.get("highlight_box"):
            b = v["highlight_box"]
            sel = sel.clip(box(b[0], b[2], b[1], b[3]))
        sel.plot(ax=ax, color="#f0b323", edgecolor="#fff3c4", linewidth=2.5, zorder=3, aspect=None)
    if v.get("line"):
        (xa, ya), (xb, yb) = v["line"]
        ax.plot([xa, xb], [ya, yb], color="#ff5a46", lw=5, ls=(0, (4, 2)), zorder=4)
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    plt.close(fig)
    img = Image.open(buf).convert("RGB").resize((w, h))

    # glow around highlighted land: blur the gold mask and add it
    arr = np.asarray(img, np.float32)
    gold = ((arr[..., 0] > 200) & (arr[..., 1] > 150) & (arr[..., 2] < 120)).astype(np.float32)
    glow = np.asarray(Image.fromarray((gold * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28)), np.float32) / 255
    arr = arr + glow[..., None] * np.array([70, 50, 5], np.float32)
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

    def to_px(lon, lat):
        return (lon - lon0) / (lon1 - lon0) * w, (lat1 - lat) / (lat1 - lat0) * h

    d = ImageDraw.Draw(img)
    if v.get("marker"):
        x, y = to_px(*v["marker"])
        for r, a in ((60, 60), (40, 110), (24, 255)):
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse((x - r, y - r, x + r, y + r), fill=(255, 70, 60, a))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img)
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(255, 255, 255))
        if v.get("label") and font_path:
            from PIL import ImageFont
            fnt = ImageFont.truetype(font_path, max(40, int(min(w, h) * 0.05)))
            tw = fnt.getlength(v["label"])
            lx = min(max(x - tw / 2, 30), w - tw - 30)
            ly = y + 50 if y < h * 0.7 else y - 140
            d.rounded_rectangle((lx - 22, ly - 12, lx + tw + 22, ly + fnt.size * 1.25), radius=22, fill=(0, 0, 0))
            d.text((lx, ly), v["label"], font=fnt, fill=(255, 255, 255))
    if v.get("line_label") and v.get("line") and font_path:
        from PIL import ImageFont
        fnt = ImageFont.truetype(font_path, max(36, int(min(w, h) * 0.045)))
        (xa, ya), (xb, yb) = v["line"]
        x, y = to_px((xa + xb) / 2, (ya + yb) / 2)
        tw = fnt.getlength(v["line_label"])
        d.rounded_rectangle((x - tw / 2 - 20, y - 90, x + tw / 2 + 20, y - 90 + fnt.size * 1.3), radius=20, fill=(255, 90, 70))
        d.text((x - tw / 2, y - 84), v["line_label"], font=fnt, fill=(255, 255, 255))
    return img


# ---------------------------------------------------------------- captions
_cap_cache = {}


def caption_layer(R, words, hi, size, max_w, color=(255, 255, 255), hi_color=(255, 200, 40), stroke=9):
    """A caption chunk with the currently spoken word in the accent colour."""
    key = (tuple(words), hi, size, max_w)
    if key in _cap_cache:
        return _cap_cache[key]
    fnt = R.font(R.FONT_BLACK, size)
    space = fnt.getlength(" ")
    lines, cur, cur_w = [], [], 0
    for i, wd in enumerate(words):
        ww = fnt.getlength(wd.upper())
        if cur and cur_w + space + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0
        cur.append(i)
        cur_w += (space if len(cur) > 1 else 0) + ww
    if cur:
        lines.append(cur)
    lh = int(size * 1.12)
    widths = [sum(fnt.getlength(words[i].upper()) for i in ln) + space * (len(ln) - 1) for ln in lines]
    lay = Image.new("RGBA", (int(max(widths)) + stroke * 2 + 20, lh * len(lines) + stroke * 2 + int(size * 0.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for li, ln in enumerate(lines):
        x = (lay.width - widths[li]) / 2
        for i in ln:
            t = words[i].upper()
            big = i == hi
            d.text((x, stroke + li * lh), t, font=fnt, fill=hi_color if big else color,
                   stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
            x += fnt.getlength(t) + space
    _cap_cache[key] = lay
    return lay


def word_index(chunk, t_in, length):
    """Which word of `chunk` is being spoken t_in seconds into a chunk of `length` seconds."""
    words = chunk.split()
    weights = np.array([len(w) + 2 for w in words], np.float32)
    edges = np.cumsum(weights) / weights.sum() * length
    return int(min(np.searchsorted(edges, t_in, side="right"), len(words) - 1))


# ---------------------------------------------------------------- subtitles
def _ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _split(text, max_words):
    words, out = text.split(), []
    for i in range(0, len(words), max_words):
        out.append(" ".join(words[i:i + max_words]))
    return out


def write_srt(path, cues):
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{_ts(a)} --> {_ts(b)}\n{txt}\n\n")


def subtitle_cues(segments, starts, speeches, lang="en", max_words=7):
    """Cues for each segment's text ('text' for English, 'es' for Spanish), spread over its speech time."""
    cues = []
    for s, t0, sp in zip(segments, starts, speeches):
        txt = s.get("text") if lang == "en" else s.get("es")
        if not txt:
            continue
        parts = _split(txt, max_words)
        weights = np.array([max(4, len(p)) for p in parts], np.float32)
        edges = np.concatenate([[0], np.cumsum(weights) / weights.sum() * sp])
        for p, a, b in zip(parts, edges[:-1], edges[1:]):
            cues.append((t0 + a, t0 + b, p))
    return cues


def write_upload_sheet(path, ep, video_file, chapters=None, credits=None):
    """Plain-text sheet with everything to paste into YouTube Studio."""
    desc = ep.get("description", "")
    if chapters:
        desc += "\n\nChapters:\n" + "\n".join(chapters)
    if credits:
        desc += "\n\nImage credits:\n" + "\n".join(credits)
    out = [
        f"VIDEO FILE: {video_file}",
        f"PUBLISH: {ep.get('publish', 'see UPLOAD.md')}",
        "",
        "TITLE (English):", ep.get("yt_title", ep.get("title", "")),
        "",
        "DESCRIPTION (English):", desc,
        "",
        "TAGS (paste into the Tags box):", ", ".join(ep.get("tags", [])),
        "",
        "SETTINGS: Audience = No, it's not made for kids | Category = Education | Altered content = No",
        "SUBTITLES: Subtitles > Add language > English: upload the .en.srt file; Spanish: upload the .es.srt file",
        "",
        "TITLE (Spanish translation):", ep.get("yt_title_es", ""),
        "",
        "DESCRIPTION (Spanish translation):", ep.get("description_es", ""),
    ]
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


# ---------------------------------------------------------------- thumbnails
def vivid(img, w, h, top_dark=0.55, top_frac=0.42, bottom_dark=0.0):
    """Punchy full-colour look with a dark top band so big text pops."""
    from PIL import ImageChops, ImageEnhance, ImageOps
    im = img.convert("RGB")
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Color(im).enhance(1.45)
    im = ImageEnhance.Contrast(im).enhance(1.15)
    im = im.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=2))
    glow = im.filter(ImageFilter.GaussianBlur(18))
    im = Image.blend(im, ImageChops.screen(im, glow), 0.3)
    a = np.asarray(im, np.float32) / 255.0
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - 0.55 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
    top = 1 - top_dark * np.clip(1 - yy / (h * top_frac), 0, 1)
    bot = 1 - bottom_dark * np.clip((yy / h - 0.78) / 0.22, 0, 1)
    a = a * np.clip(v, 0.3, 1)[..., None] * top[..., None] * bot[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def cover(img, w, h, focus=(0.5, 0.5), zoom=1.0):
    iw, ih = img.size
    s = max(w / iw, h / ih) * zoom
    im = img.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
    x = int(min(max(focus[0] * im.width - w / 2, 0), im.width - w))
    y = int(min(max(focus[1] * im.height - h / 2, 0), im.height - h))
    return im.crop((x, y, x + w, y + h))


def decorate(canvas, R, spec, w, h, accent=(255, 200, 40)):
    """Optional extras on any thumbnail: red ring + arrow, red badge, big red down/up arrow."""
    d = ImageDraw.Draw(canvas)
    red = (255, 45, 45)
    if spec.get("circle"):
        cx, cy, r = spec["circle"]
        cx, cy, r = cx * w, cy * h, r * min(w, h)
        for k in range(3):
            d.ellipse((cx - r - k * 4, cy - r - k * 4, cx + r + k * 4, cy + r + k * 4), outline=red, width=10)
    if spec.get("arrow_down") or spec.get("arrow_up"):
        up = bool(spec.get("arrow_up"))
        ax, ay = spec.get("arrow_at", (0.82, 0.55))
        ax, ay, s = ax * w, ay * h, min(w, h) * 0.16
        shaft = (ax - s * 0.22, ay - s * 1.1, ax + s * 0.22, ay + s * 0.2) if not up else (ax - s * 0.22, ay - s * 0.2, ax + s * 0.22, ay + s * 1.1)
        head = [(ax - s * 0.6, ay + s * 0.1), (ax + s * 0.6, ay + s * 0.1), (ax, ay + s * 0.9)] if not up else \
               [(ax - s * 0.6, ay - s * 0.1), (ax + s * 0.6, ay - s * 0.1), (ax, ay - s * 0.9)]
        for off, col in ((10, (0, 0, 0)), (0, red)):
            d.rectangle((shaft[0] - off, shaft[1] - off, shaft[2] + off, shaft[3] + off), fill=col)
            d.polygon([(x + (off if x > ax else -off if x < ax else 0), y + (off if not up else -off)) for x, y in head], fill=col)
    if spec.get("badge"):
        fnt = R.font(R.FONT_BLACK, int(min(w, h) * 0.075))
        tw = fnt.getlength(spec["badge"])
        bx, by = spec.get("badge_at", (0.5, 0.74))
        bx, by = bx * w - tw / 2, by * h
        d.rounded_rectangle((bx - 30, by - 14, bx + tw + 30, by + fnt.size * 1.2), radius=24, fill=red, outline=(255, 255, 255), width=5)
        d.text((bx, by - 4), spec["badge"], font=fnt, fill=(255, 255, 255))
    return canvas


def short_thumb(R, img, spec, ep, w=1080, h=1920, accent=(255, 200, 40)):
    """Vertical Shorts thumbnail / opening frame: vivid photo or map, giant two-colour hook."""
    if spec.get("map"):
        base = np.asarray(map_image(spec["map"], (w, h), R.FONT_BOLD), np.float32)
        yy = np.arange(h)[:, None]
        top = 1 - 0.6 * np.clip(1 - yy / (h * 0.45), 0, 1)
        canvas = Image.fromarray((base * top[..., None]).clip(0, 255).astype(np.uint8)).convert("RGBA")
    else:
        if img is None:
            img = R.starfield(3, w, h)
        canvas = vivid(cover(img, w, h, tuple(spec.get("focus", (0.5, 0.5))), spec.get("zoom", 1.0)), w, h,
                       top_dark=0.62, top_frac=0.48, bottom_dark=0.45).convert("RGBA")
    decorate(canvas, R, spec, w, h, accent)
    d = ImageDraw.Draw(canvas)
    # kicker pill
    kick = ep.get("kicker", R.BRAND)
    kf = R.font(R.FONT_BOLD, 50)
    kw = kf.getlength(kick)
    d.rounded_rectangle(((w - kw) / 2 - 34, 250, (w + kw) / 2 + 34, 250 + 82), radius=41, fill=accent)
    d.text(((w - kw) / 2, 262), kick, font=kf, fill=(20, 14, 0))
    # giant hook: white line(s) then accent line(s)
    y = 380
    for txt, col in ((spec.get("white", ""), (255, 255, 255)), (spec.get("accent", ""), accent)):
        if not txt:
            continue
        size = 200
        while R.font(R.FONT_BLACK, size).getlength(txt) > w * 0.9 and size > 90:
            size -= 6
        fnt = R.font(R.FONT_BLACK, size)
        tw = fnt.getlength(txt)
        d.text(((w - tw) / 2, y), txt, font=fnt, fill=col, stroke_width=14, stroke_fill=(0, 0, 0))
        y += int(size * 1.05)
    bf = R.font(R.FONT_BOLD, 34)
    bw_ = bf.getlength(R.BRAND)
    d.text(((w - bw_) / 2, 120), R.BRAND, font=bf, fill=accent, stroke_width=3, stroke_fill=(0, 0, 0))
    return canvas.convert("RGB")
