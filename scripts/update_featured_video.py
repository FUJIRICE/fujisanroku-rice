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



def _iso8601_seconds(dur: str) -> int:
    """PT1H2M3S 形式を秒に直す。取れなければ0。"""
    m = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur or "")
    if not m:
        return 0
    d, h, mi, se = (int(x) if x else 0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + se


def pick_from_api():
    """RSSで見つからないときに YouTube API で遡って探す。

    RSSは最新15件しか返さない。ライブアーカイブが1日数本〜十数本
    公開されるため、通常動画が15件の枠外に押し出され、2026-08-08以降
    「動画IDが取得できませんでした」で1日3回失敗し続けていた。

    判定はタイトルの文言ではなくAPIの実データで行う:
      - liveStreamingDetails があるもの = ライブ配信/アーカイブ → 除外
      - 61秒未満 = Shorts → 除外
    """
    import pickle
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
    except Exception as e:
        log(f"APIフォールバック不可(ライブラリ無し): {type(e).__name__}")
        return None, None

    tok = platform_utils.desktop_dir() / "fuji_timelapse" / "youtube_token.pkl"
    try:
        creds = pickle.load(open(tok, "rb"))
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            pickle.dump(creds, open(tok, "wb"))
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        log(f"APIフォールバック不可(認証): {type(e).__name__}")
        return None, None

    try:
        ch = yt.channels().list(part="contentDetails", id=CHANNEL).execute()
        uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except Exception as e:
        log(f"APIフォールバック失敗(uploads取得): {type(e).__name__}")
        return None, None

    page = None
    for _ in range(6):          # 50件 × 6ページ = 最大300本まで遡る
        try:
            r = yt.playlistItems().list(part="contentDetails", playlistId=uploads,
                                        maxResults=50, pageToken=page).execute()
        except Exception as e:
            log(f"APIフォールバック失敗(playlistItems): {type(e).__name__}")
            break
        ids = [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        if not ids:
            break
        try:
            vs = yt.videos().list(part="snippet,contentDetails,liveStreamingDetails",
                                  id=",".join(ids)).execute().get("items", [])
        except Exception as e:
            log(f"APIフォールバック失敗(videos): {type(e).__name__}")
            break
        for v in vs:
            if "liveStreamingDetails" in v:
                continue        # ライブ配信・そのアーカイブ
            if _iso8601_seconds(v["contentDetails"].get("duration", "")) <= 60:
                continue        # Shorts
            return v["id"], v["snippet"]["title"]   # 最新の本編
        page = r.get("nextPageToken")
        if not page:
            break

    return None, None


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
        m_link = re.search(r'<link rel="alternate" href="([^"]+)"', blk)
        if m_vid:
            is_short = bool(m_link and "/shorts/" in m_link.group(1))
            parsed.append((m_vid.group(1), m_ttl.group(1) if m_ttl else "", is_short))
    pick = title = None
    for vid, ttl, is_short in parsed:
        # ここで選ぶのは「トップの注目枠」ではなく、
        # ライブが再生できないときに出す**代替動画**。
        # トップは hugo.toml の liveChannelID により24hライブを優先表示する。
        #
        # ライブ配信枠とShorts(縦動画)は代替動画にしない。
        # 判定はRSSのlink(/shorts/ vs /watch)の実URLを見る(タイトル文言に依存しない)。
        #
        # 以前は「タイムラプス」「4K」を含むものを優先していたが、
        # そのせいで新しい本編(例: 100日完全版)を飛ばして古い動画が
        # 選ばれてしまう。代替に出すのは最新の本編でよいので優先をやめた。
        if LIVE_PAT.search(ttl) or is_short:
            continue
        pick, title = vid, ttl
        break
    if not pick:
        # RSSの最新15件がライブアーカイブとShortsで埋まっている場合。
        log("RSS内に候補なし（ライブ/Shortsで占有）→ APIで遡って検索")
        pick, title = pick_from_api()
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
