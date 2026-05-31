# FUJI RICE サイト: トップの埋め込みタイムラプスを常に最新に更新する
# YouTubeチャンネルRSSから最新の「本編タイムラプス」動画IDを取得し、
# hugo.toml の youtubeFeatureID を更新 → 変化があれば git push（Cloudflare再ビルド）
#
# 自動化パイプライン(タイムラプス生成・SNS投稿)には一切触れない。サイト更新のみ。

$repo     = "C:\Users\iwata\Desktop\fujisanroku-rice"
$hugotoml = Join-Path $repo "hugo.toml"
$channel  = "UCvvaEEAZoCEwlv11ubKSWxg"
$rssUrl   = "https://www.youtube.com/feeds/videos.xml?channel_id=$channel"
$logFile  = Join-Path $repo "scripts\update_featured_video.log"
$env:GIT_TERMINAL_PROMPT = "0"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line -Encoding utf8
    Write-Output $line
}

# --- RSS取得 ---
try {
    $xml = (Invoke-WebRequest -Uri $rssUrl -UseBasicParsing -TimeoutSec 30).Content
} catch {
    Log "RSS取得失敗: $_"
    exit 1
}

# --- 本編タイムラプス(タイムラプス/4K/timelapse)の最新を選ぶ ---
$entries = [regex]::Matches($xml, '<entry>.*?</entry>', 'Singleline')
$pick = $null; $pickTitle = $null
foreach ($m in $entries) {
    $blk = $m.Value
    $vid = [regex]::Match($blk, '<yt:videoId>([^<]+)</yt:videoId>').Groups[1].Value
    $title = [regex]::Match($blk, '<title>([^<]+)</title>').Groups[1].Value
    if ($vid -and ($title -match 'タイムラプス|4K|timelapse')) {
        $pick = $vid; $pickTitle = $title; break
    }
}
if (-not $pick -and $entries.Count -gt 0) {
    $blk = $entries[0].Value
    $pick = [regex]::Match($blk, '<yt:videoId>([^<]+)</yt:videoId>').Groups[1].Value
    $pickTitle = [regex]::Match($blk, '<title>([^<]+)</title>').Groups[1].Value
}
if (-not $pick) { Log "動画IDが取得できませんでした"; exit 1 }
Log "最新タイムラプス: $pick  ($pickTitle)"

# --- hugo.toml 更新 ---
$toml = [System.IO.File]::ReadAllText($hugotoml)
if ($toml -notmatch 'youtubeFeatureID = "[^"]*"') { Log "youtubeFeatureID が見つかりません"; exit 1 }
$current = [regex]::Match($toml, 'youtubeFeatureID = "([^"]*)"').Groups[1].Value
if ($current -eq $pick) { Log "変更なし(既に最新: $pick)。終了。"; exit 0 }
$new = [regex]::Replace($toml, 'youtubeFeatureID = "[^"]*"', "youtubeFeatureID = `"$pick`"")
[System.IO.File]::WriteAllText($hugotoml, $new, (New-Object System.Text.UTF8Encoding $false))
Log "hugo.toml 更新: $current → $pick"

# --- git commit + pull --rebase + push (hugo.toml のみ) ---
Set-Location $repo
& git add hugo.toml
& git commit -m "Update featured timelapse to latest: $pick" | Out-Null
& git pull --rebase origin main | Out-Null
& git push origin main | Out-Null
Log "git push done -> Cloudflare rebuild"
exit 0
