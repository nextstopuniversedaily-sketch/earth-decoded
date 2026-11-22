#!/usr/bin/env bash
# Commit one finished video and push it, even if other runs pushed in the meantime.
# usage: tools/publish.sh "commit message" file1 file2 ...
# The video's files are copied aside, the checkout is moved to the latest
# origin/main, the files are put back, UPLOAD.md is rebuilt, then pushed.
msg="$1"; shift
tmp=$(mktemp -d)
files=()
for p in "$@"; do
  [ -e "$p" ] || continue
  mkdir -p "$tmp/$(dirname "$p")" && cp -a "$p" "$tmp/$p" && files+=("$p")
done
[ ${#files[@]} -eq 0 ] && { echo "nothing to publish"; exit 0; }
for i in 1 2 3 4 5; do
  git rebase --abort 2>/dev/null || true
  git merge --abort 2>/dev/null || true
  git fetch -q origin main && git reset -q --hard origin/main
  cp -a "$tmp"/. .
  python tools/index.py || true
  git add "${files[@]}" UPLOAD.md
  git commit -q -m "$msg" || { echo "no changes"; exit 0; }
  if git push -q origin HEAD:main; then echo "published: $msg"; exit 0; fi
  echo "push attempt $i failed, retrying"; sleep $((i * 5))
done
echo "could not publish $msg"; exit 1
