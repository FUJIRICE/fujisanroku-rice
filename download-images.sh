#!/bin/bash
IMG_DIR="static/images/posts"
URL_FILE="image-urls.txt"
mkdir -p "$IMG_DIR"
if [ ! -f "$URL_FILE" ]; then
  echo "❌ $URL_FILE が見つかりません"
  exit 1
fi
TOTAL=$(wc -l < "$URL_FILE")
echo "📥 ${TOTAL}件の画像をダウンロードします..."
COUNT=0; SKIP=0; FAIL=0
while IFS= read -r url; do
  [ -z "$url" ] && continue
  FILENAME=$(basename "$url" | sed 's/\?.*//')
  FILENAME=$(echo "$FILENAME" | tr '[:upper:]' '[:lower:]')
  SAVE_PATH="${IMG_DIR}/${FILENAME}"
  if [ -f "$SAVE_PATH" ]; then SKIP=$((SKIP+1)); continue; fi
  HTTP_CODE=$(curl -s -o "$SAVE_PATH" -w "%{http_code}" --max-time 30 --retry 2 -H "User-Agent: Mozilla/5.0" "$url")
  if [ "$HTTP_CODE" = "200" ]; then COUNT=$((COUNT+1)); echo "  ✅ $FILENAME"
  else FAIL=$((FAIL+1)); rm -f "$SAVE_PATH"; echo "  ❌ HTTP $HTTP_CODE: $url"; fi
  sleep 0.3
done < "$URL_FILE"
echo "✅ 完了: ${COUNT}件ダウンロード / ${SKIP}件スキップ / ${FAIL}件失敗"
