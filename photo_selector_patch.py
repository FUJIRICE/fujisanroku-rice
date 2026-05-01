# ============================================================
# 【2026-04-24 追加】日の出・日の入りベースの写真選択ロジック
# ============================================================

# 富士宮市の座標(astral用)
FUJINOMIYA_LOCATION = LocationInfo("Fujinomiya", "Japan", "Asia/Tokyo", 35.222, 138.621)


def _get_photo_datetime(fp):
    """写真の撮影時刻を取得する。
    優先順位:
      1. ファイル名 YYYYMMDD_HHMMSS.* から抽出 (Reolinkカメラ用)
      2. EXIF DateTimeOriginal (iPhone等)
      3. ファイル更新時刻 (mtime) フォールバック
    """
    name = os.path.basename(fp)

    # ① ファイル名から (Reolinkカメラ: 20260424_043001.jpg)
    parts = name.split("_")
    if len(parts) >= 2 and len(parts[0]) == 8 and len(parts[1]) >= 6:
        try:
            date_part = parts[0]
            time_part = parts[1][:6]
            return datetime.datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S")
        except ValueError:
            pass

    # ② EXIF DateTimeOriginal (iPhone)
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass

        img = Image.open(fp)
        exif = img._getexif() if hasattr(img, '_getexif') else None
        if exif:
            for tag_id, value in exif.items():
                if TAGS.get(tag_id) == 'DateTimeOriginal':
                    return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        log.debug(f"EXIF読み込み失敗: {name} ({e})")

    # ③ フォールバック: ファイル更新時刻
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    except OSError:
        return None


def _get_sun_times(target_date):
    """指定日の日の出・日の入り時刻を取得 (naive datetime, JST)"""
    try:
        s = sun(FUJINOMIYA_LOCATION.observer, date=target_date,
                tzinfo=pytz.timezone("Asia/Tokyo"))
        sunrise_naive = s["sunrise"].replace(tzinfo=None)
        sunset_naive = s["sunset"].replace(tzinfo=None)
        return sunrise_naive, sunset_naive
    except Exception as e:
        log.error(f"日の出・日の入り取得失敗: {e}")
        return None, None


def _select_best_photo(photos, target_date, time_of_day):
    """日の出/日の入りに最も近い写真を選ぶ"""
    if not photos:
        return None

    photos_with_time = []
    for fp in photos:
        dt = _get_photo_datetime(fp)
        if dt is not None:
            photos_with_time.append((fp, dt))

    if not photos_with_time:
        return random.choice(photos)

    if time_of_day not in ("morning", "evening"):
        return random.choice([p[0] for p in photos_with_time])

    sunrise_naive, sunset_naive = _get_sun_times(target_date)
    if sunrise_naive is None:
        log.warning("日の出・日の入り取得不可、時間帯フィルタにフォールバック")
        if time_of_day == "morning":
            filtered = [p for p in photos_with_time if 4 <= p[1].hour < 12]
        else:
            filtered = [p for p in photos_with_time if 15 <= p[1].hour < 21]
        if filtered:
            return random.choice([p[0] for p in filtered])
        return random.choice([p[0] for p in photos_with_time])

    if time_of_day == "morning":
        target = sunrise_naive
        label = "日の出"
    else:
        target = sunset_naive
        label = "日の入り"

    candidates = [p for p in photos_with_time
                  if abs((p[1] - target).total_seconds()) <= 2 * 3600]

    if candidates:
        best = min(candidates, key=lambda x: abs((x[1] - target).total_seconds()))
        diff_min = abs((best[1] - target).total_seconds()) / 60
        log.info(f"{label}({target.strftime('%H:%M')})に最も近い写真を選択: "
                 f"{os.path.basename(best[0])} ({best[1].strftime('%H:%M')}, "
                 f"差{diff_min:.0f}分)")
        return best[0]

    best = min(photos_with_time, key=lambda x: abs((x[1] - target).total_seconds()))
    diff_min = abs((best[1] - target).total_seconds()) / 60
    log.warning(f"{label}±2時間以内に写真なし、全写真から最近のもの選択: "
                f"{os.path.basename(best[0])} ({best[1].strftime('%H:%M')}, "
                f"差{diff_min:.0f}分)")
    return best[0]


def find_todays_photo(time_of_day=None):
    """今日撮影された読み取り可能な写真を探す(なければ直近7日まで遡る)

    time_of_day: 'morning' → 日の出に最も近い写真を選ぶ
                 'evening' → 日の入りに最も近い写真を選ぶ
                 None      → ランダム選択
    """
    if not os.path.exists(PHOTOS_DIR):
        log.warning(f"写真フォルダが見つかりません: {PHOTOS_DIR}")
        return None

    today = datetime.date.today()

    readable_photos = []
    search_date = None
    for days_back in range(8):
        d = today - datetime.timedelta(days=days_back)
        photos = _scan_photos_for_date(d)
        if photos:
            readable_photos = photos
            search_date = d
            if days_back == 0:
                log.info(f"今日の写真が {len(photos)} 枚見つかりました")
            else:
                log.info(f"今日の写真なし → {days_back}日前({d})の写真を {len(photos)} 枚見つけました")
            break

    if not readable_photos:
        log.warning("直近7日間の写真が見つかりませんでした")
        return None

    photo = _select_best_photo(readable_photos, search_date, time_of_day)
    log.info(f"写真を選択: {photo}")
    return photo