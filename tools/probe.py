"""Find reusable (PD / CC0 / CC BY) Commons images for search queries.

Reads probe/queries.json (a list of search strings) and writes probe/results.md
listing, per query, file titles whose license allows reuse in a video.
"""
import json, os, re, sys
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "EarthDecodedBot/1.0 (https://github.com/nextstopuniversedaily-sketch/earth-decoded)"}


def license_ok(lic):
    l = (lic or "").lower()
    parts = re.split(r"[\s\-]", l)
    if "sa" in parts or "nd" in parts:
        return False
    return (l.startswith("public domain") or l.startswith("pd") or "cc0" in l or l.startswith("cc by")
            or l.startswith("cc-by") or l.startswith("no restrictions") or l == "attribution")


def search(q):
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=60, params={
        "action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q + " filetype:bitmap",
        "gsrlimit": 50, "prop": "imageinfo", "iiprop": "extmetadata|mime|size",
        "iiextmetadatafilter": "LicenseShortName|ImageDescription", "format": "json"})
    pages = r.json().get("query", {}).get("pages", {}).values()
    out = []
    for p in sorted(pages, key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        if ii.get("mime") in ("image/jpeg", "image/png") and ii.get("width", 0) >= 1200 and license_ok(lic):
            out.append((p["title"], lic, ii.get("width"), ii.get("height")))
    return out


def main():
    queries = json.load(open(os.path.join(ROOT, "probe", "queries.json")))
    lines = ["# Reusable Commons images\n"]
    for q in queries:
        try:
            hits = search(q)
        except Exception as e:  # noqa: BLE001
            hits, lines = [], lines + [f"\n## {q}\n- error: {e}"]
            continue
        lines.append(f"\n## {q}  ({len(hits)})")
        lines += [f"- {t} | {lic} | {w}x{h}" for t, lic, w, h in hits[:15]]
    open(os.path.join(ROOT, "probe", "results.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
