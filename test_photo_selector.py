# -*- coding: utf-8 -*-
"""日の出・日の入り 写真選択テスト"""
import os
import datetime
from pathlib import Path

PHOTOS_DIR = r"C:\Users\iwata\iCloudPhotos\Photos"

# ① 富士宮市の日の出・日の入り
try:
    from astral import LocationInfo
    from astral.sun import sun
    import pytz
    
    city = LocationInfo("Fujinomiya", "Japan", "Asia/Tokyo", 35.222, 138.621)
    today = datetime.date.today()
    s = sun(city.observer, date=today, tzinfo=pytz.timezone("Asia/Tokyo"))
    sunrise = s["sunrise"]
    sunset = s["sunset"]
    print(f"📅 {today}")
    print(f"🌅 日の出: {sunrise.strftime('%H:%M:%S')}")
    print(f"🌇 日の入: {sunset.strftime('%H:%M:%S')}")
    print()
except Exception as e:
    print(f"❌ astral エラー: {e}")
    exit(1)

# ② 今日の写真をスキャン + EXIF取得
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError as e:
    print(f"❌ PIL/pillow-heif エラー: {e}")
    exit(1)

date_str = today.strftime("%Y%m%d")
photos_with_time = []

for f in os.listdir(PHOTOS_DIR):
    fp = os.path.join(PHOTOS_DIR, f)
    if not os.path.isfile(fp):
        continue
    ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
    if ext not in ("jpg", "jpeg", "heic", "png"):
        continue
    
    # 今日の日付のファイルだけ
    if not f.startswith(date_str):
        try:
            mtime = datetime.date.fromtimestamp(os.path.getmtime(fp))
            if mtime != today:
                continue
        except OSError:
            continue
    
    # iCloudプレースホルダーチェック
    try:
        with open(fp, "rb") as fh:
            data = fh.read(16)
        if len(data) < 16:
            continue
    except (OSError, IOError):
        continue
    
    # EXIF撮影時刻取得
    try:
        img = Image.open(fp)
        exif = img._getexif() if hasattr(img, '_getexif') else None
        dt = None
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    dt = datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    break
        if not dt:
            # フォールバック: ファイル更新時刻
            dt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
        photos_with_time.append((f, dt))
    except Exception as e:
        print(f"  ⚠️ EXIF読み込み失敗: {f} ({e})")

print(f"📷 今日の写真: {len(photos_with_time)}件")
print()

if not photos_with_time:
    print("⚠️ 今日の写真が見つかりません")
    exit(0)

# ③ 日の出/日の入りに最も近い写真を選ぶ
sunrise_naive = sunrise.replace(tzinfo=None)
sunset_naive = sunset.replace(tzinfo=None)

photos_with_time.sort(key=lambda x: x[1])

print("【全写真の撮影時刻】")
for fname, dt in photos_with_time:
    diff_sunrise = abs((dt - sunrise_naive).total_seconds()) / 60
    diff_sunset = abs((dt - sunset_naive).total_seconds()) / 60
    print(f"  {dt.strftime('%H:%M:%S')} - {fname[:40]} (日出±{diff_sunrise:.0f}分, 日入±{diff_sunset:.0f}分)")

print()

best_morning = min(photos_with_time, key=lambda x: abs((x[1] - sunrise_naive).total_seconds()))
best_evening = min(photos_with_time, key=lambda x: abs((x[1] - sunset_naive).total_seconds()))

print(f"🌅 朝に最適: {best_morning[0]} ({best_morning[1].strftime('%H:%M:%S')})")
print(f"🌇 夕方に最適: {best_evening[0]} ({best_evening[1].strftime('%H:%M:%S')})")