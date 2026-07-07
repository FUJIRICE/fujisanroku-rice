# -*- coding: utf-8 -*-
"""
update_featured_video.py — サイトトップの埋め込みタイムラプスを最新に更新
(Windows版 fujisanroku-rice/scripts/update_featured_video.ps1 のPython移植・クロスプラットフォーム)

YouTubeチャンネルRSSから最新の「本編タイムラプス」動画IDを取得し、
hugo.toml の youtubeFeatureID を更新 → 変化があれば git push(Cloudflare再ビルド)。
自動化パイプライン(タイムラプス生成・SNS投稿)には一切触れない。サイト更新のみ。

使い方: python update_featured_video.py [--dry-run]
"""
import re
import sys
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / "Desktop" / "_fuji_common"))
import platform_utils

REPO = platform_utils.desktop_dir() / "fujisanroku-rice"
HUGOTOML = REPO / "hugo.toml"
CHANNEL = "UCvvaEEAZoCEwlv11ubKSWxg"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL}"
LOG_FILE = REPO / "scripts" / "update_featured_video.log"
DRY_RUN = "--dry-run" in sys.argv


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main():
    try:
        with urllib.request.urlopen(RSS_URL, timeout=30) as r:
            xml = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"RSS取得失敗: {e}")
        return 1

    entries = re.findall(r"<entry>.*?</entry>", xml, re.S)
    LIVE_PAT = re.compile(r"ライブ|生中継|Live Camera|LIVE", re.I)
    parsed = []
    for blk in entries:
        m_vid = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", blk)
        m_ttl = re.search(r"<title>([^<]+)</title>", blk)
        if m_vid:
            parsed.append((m_vid.group(1), m_ttl.group(1) if m_ttl else ""))
    pick = title = None
    for vid, ttl in parsed:
        # ライブ配信枠(12時間ごとにIDが変わる)はおすすめ動画にしない
        if LIVE_PAT.search(ttl):
            continue
        if re.search(r"タイムラプス|4K|timelapse", ttl):
            pick, title = vid, ttl
            break
    if not pick:
        for vid, ttl in parsed:
            if not LIVE_PAT.search(ttl):
                pick, title = vid, ttl
                break
    if not pick:
        log("動画IDが取得できませんでした")
        return 1
    log(f"最新タイムラプス: {pick}  ({title})")

    toml = HUGOTOML.read_text(encoding="utf-8")
    m = re.search(r'youtubeFeatureID = "([^"]*)"', toml)
    if not m:
        log("youtubeFeatureID が見つかりません")
        return 1
    current = m.group(1)
    if current == pick:
        log(f"変更なし(既に最新: {pick})。終了。")
        return 0
    if DRY_RUN:
        log(f"[dry-run] hugo.toml 更新予定: {current} → {pick}")
        return 0
    new = re.sub(r'youtubeFeatureID = "[^"]*"',
                 f'youtubeFeatureID = "{pick}"', toml)
    HUGOTOML.write_text(new, encoding="utf-8")
    log(f"hugo.toml 更新: {current} → {pick}")

    env_git = dict(GIT_TERMINAL_PROMPT="0")
    import os
    env = {**os.environ, **env_git}

    def git(*args, check_name=None):
        r = subprocess.run(["git", *args], cwd=REPO,
                           capture_output=True, text=True, env=env)
        if check_name and r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            log(f"git {check_name} 失敗(exit={r.returncode}): {err[:300]}")
        return r

    git("add", "hugo.toml")
    git("commit", "-m", f"Update featured timelapse to latest: {pick}")
    if git("pull", "--rebase", "origin", "main", check_name="pull --rebase").returncode != 0:
        git("rebase", "--abort")
        return 1
    if git("push", "origin", "main", check_name="push").returncode != 0:
        return 1
    log("git push done -> Cloudflare rebuild")
    return 0


if __name__ == "__main__":
    sys.exit(main())
