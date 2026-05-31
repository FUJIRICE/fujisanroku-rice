"""
毎日 FUJIRICE素材画像 からランダムに1枚選び concept-fuji.jpg を更新して git push する。
タスクスケジューラから実行: python rotate_concept_photo.py
"""

import os
import random
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import date

PHOTOS_DIR   = Path(r"C:\Users\iwata\Desktop\FUJIRICE素材画像")
REPO_DIR     = Path(r"C:\Users\iwata\Desktop\fujisanroku-rice")
TARGET_IMAGE = REPO_DIR / "static" / "images" / "concept-fuji.jpg"
LOG_FILE     = REPO_DIR / "scripts" / "rotate_concept_photo.log"
EXTENSIONS   = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
log = logging.getLogger(__name__)


def pick_photo() -> Path | None:
    photos = [p for p in PHOTOS_DIR.iterdir() if p.suffix in EXTENSIONS]
    if not photos:
        log.error(f"写真が見つかりません: {PHOTOS_DIR}")
        return None
    chosen = random.choice(photos)
    log.info(f"選択した写真: {chosen.name}")
    return chosen


def update_concept(photo: Path):
    shutil.copy2(photo, TARGET_IMAGE)
    log.info(f"コピー完了: {TARGET_IMAGE}")


def git_push(photo_name: str):
    today = date.today().isoformat()
    msg = f"Daily concept photo update ({today}): {photo_name}"
    cmds = [
        ["git", "-C", str(REPO_DIR), "add", str(TARGET_IMAGE)],
        ["git", "-C", str(REPO_DIR), "commit", "-m", msg],
        ["git", "-C", str(REPO_DIR), "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"コマンド失敗: {' '.join(cmd)}\n{result.stderr}")
            raise RuntimeError(result.stderr)
        log.info(f"OK: {' '.join(cmd)}")


if __name__ == "__main__":
    log.info("=== rotate_concept_photo 開始 ===")
    photo = pick_photo()
    if photo:
        update_concept(photo)
        git_push(photo.name)
        log.info("=== 完了 ===")
    else:
        log.warning("写真なし、スキップ")
