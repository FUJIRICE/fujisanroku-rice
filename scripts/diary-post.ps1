<#
.SYNOPSIS
    毎朝・毎夕、iCloud写真 + 定型文をGitHubに自動投稿します。

.DESCRIPTION
    - iCloudPhotosフォルダから「今日の朝or夕方」の写真を自動選択
    - diary/YYYY/MM.md に日付・挨拶・写真を追記
    - GitHub にプッシュ → Cloudflare Pages が自動ビルド

.PARAMETER Pat
    GitHub PAT（Personal Access Token）

.PARAMETER RepoPath
    fujisanroku-riceリポジトリのローカルパス（省略可）

.EXAMPLE
    .\diary-post.ps1 -Pat "ghp_xxxx"
    .\diary-post.ps1 -Pat "ghp_xxxx" -RepoPath "C:\repos\fujisanroku-rice"

.NOTES
    タスクスケジューラで毎朝7:00・毎夕18:00に実行してください。
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Pat,

    [string]$RepoPath = "C:\Users\iwata\Documents\GitHub\fujisanroku-rice",
    [string]$ICloudPhotos = "C:\Users\iwata\iCloudPhotos\Photos",

    # Make.com Webhook URL（設定後に入力）
    [string]$WebhookUrl = ""
)

# ─────────────────────────────────────
# 日時・朝夕の判定
# ─────────────────────────────────────
$now      = Get-Date
$hour     = $now.Hour
$dateStr  = $now.ToString("yyyy-MM-dd")
$yearStr  = $now.ToString("yyyy")
$monthStr = $now.ToString("MM")
$dayStr   = $now.ToString("dd")
$dateJP   = "$($now.Year)年$($now.Month)月$($now.Day)日"

if ($hour -lt 12) {
    $session      = "朝"
    $greeting     = "おはようございます"
    $message      = "今日も富士山麓で一日が始まりました。"
    $photoStart   = $now.Date.AddHours(4)   # 04:00〜
    $photoEnd     = $now.Date.AddHours(12)  # 12:00まで
} else {
    $session      = "夜"
    $greeting     = "こんばんは"
    $message      = "今日も一日お疲れ様でした。富士山麓の夕暮れです。"
    $photoStart   = $now.Date.AddHours(14)  # 14:00〜
    $photoEnd     = $now.Date.AddHours(20)  # 20:00まで
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host " 🌾 FUJI RICE 日記自動投稿" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host " 日付  : $dateJP $session" -ForegroundColor Gray
Write-Host " 挨拶  : $greeting" -ForegroundColor Gray
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────
# リポジトリの確認
# ─────────────────────────────────────
if (-not (Test-Path $RepoPath)) {
    # リポジトリが見つからない場合、クローンを試みる
    Write-Host "⚠️  リポジトリが見つかりません: $RepoPath" -ForegroundColor Yellow
    Write-Host "   GitHubからクローンします..." -ForegroundColor Gray
    $parentPath = Split-Path $RepoPath -Parent
    if (-not (Test-Path $parentPath)) { New-Item -ItemType Directory -Path $parentPath -Force | Out-Null }

    $env:GIT_ASKPASS = "echo"
    $cloneUrl = "https://$Pat@github.com/FUJIRICE/fujisanroku-rice.git"
    git clone $cloneUrl $RepoPath 2>&1 | Out-Null

    if (-not (Test-Path $RepoPath)) {
        Write-Host "❌ クローン失敗。RepoPathを確認してください" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ クローン完了" -ForegroundColor Green
}

# ─────────────────────────────────────
# iCloudから写真を選択
# ─────────────────────────────────────
$selectedPhoto = $null

Write-Host "【写真選択】" -ForegroundColor White
Write-Host "   検索範囲: $($photoStart.ToString('HH:mm'))〜$($photoEnd.ToString('HH:mm'))" -ForegroundColor Gray
Write-Host "   フォルダ: $ICloudPhotos" -ForegroundColor Gray

if (Test-Path $ICloudPhotos) {
    # 今日の朝/夕方の時間帯の写真を検索
    $photos = Get-ChildItem -Path $ICloudPhotos -Recurse -Include "*.jpg","*.jpeg","*.heic","*.png","*.JPG","*.JPEG","*.HEIC","*.PNG" |
        Where-Object {
            $_.LastWriteTime -ge $photoStart -and
            $_.LastWriteTime -le $photoEnd
        } |
        Sort-Object LastWriteTime -Descending

    if ($photos.Count -gt 0) {
        $selectedPhoto = $photos[0]
        Write-Host "   ✅ 写真発蚋: $($selectedPhoto.Name) ($($selectedPhoto.LastWriteTime.ToString('HH:mm')))" -ForegroundColor Green
    } else {
        # 今日の写真がなければ過去7日以内の同時間帯
        Write-Host "   ⚠️  今日の$session写真なし。過去7日から検索..." -ForegroundColor Yellow
        $photos = Get-ChildItem -Path $ICloudPhotos -Recurse -Include "*.jpg","*.jpeg","*.heic","*.png","*.JPG","*.JPEG","*.HEIC","*.PNG" |
            Where-Object {
                $_.LastWriteTime -ge $now.AddDays(-7) -and
                ($_.LastWriteTime.Hour -ge $photoStart.Hour -and $_.LastWriteTime.Hour -lt $photoEnd.Hour)
            } |
            Sort-Object LastWriteTime -Descending

        if ($photos.Count -gt 0) {
            $selectedPhoto = $photos[0]
            Write-Host "   ✅ 過去写真使用: $($selectedPhoto.Name)" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  写真なし。テキストのみで投稿します。" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ⚠️  iCloudフォルダ未検出。テキストのみで投稿します。" -ForegroundColor Yellow
}

# ─────────────────────────────────────
# 写真をリポジトリにコピー
# ─────────────────────────────────────
$photoMdRef = ""

if ($selectedPhoto) {
    $photoDestDir = Join-Path $RepoPath "diary\photos\$yearStr"
    if (-not (Test-Path $photoDestDir)) { New-Item -ItemType Directory -Path $photoDestDir -Force | Out-Null }

    $ext = $selectedPhoto.Extension.ToLower()
    # HEICはJPGとして扱う（Cloudflare Pagesでの表示のため）
    if ($ext -eq ".heic") { $ext = ".jpg" }
    $photoFileName = "$dateStr-$session$ext"
    $photoDest = Join-Path $photoDestDir $photoFileName

    Copy-Item -Path $selectedPhoto.FullName -Destination $photoDest -Force
    Write-Host "   📷 写真コピー完了: diary/photos/$yearStr/$photoFileName" -ForegroundColor Green

    $photoMdRef = "`n![${dateJP}の${session}](../photos/$yearStr/$photoFileName)`n"
}

# ─────────────────────────────────────
# 日記ファイルに追記
# ─────────────────────────────────────
$diaryDir  = Join-Path $RepoPath "diary\$yearStr"
if (-not (Test-Path $diaryDir)) { New-Item -ItemType Directory -Path $diaryDir -Force | Out-Null }

$diaryFile = Join-Path $diaryDir "$monthStr.md"

$entry = @"

## $dateJP $session

$greeting。$message
$photoMdRef
"@

Write-Host ""
Write-Host "【日記追記】" -ForegroundColor White
Add-Content -Path $diaryFile -Value $entry -Encoding UTF8
Write-Host "   ✅ 追記完了: diary/$yearStr/$monthStr.md" -ForegroundColor Green

# ─────────────────────────────────────
# Git コミット & プッシュ
# ─────────────────────────────────────
Write-Host ""
Write-Host "【GitHub プッシュ】" -ForegroundColor White

Push-Location $RepoPath

# 認証設定（PAT使用）
$remoteUrl = "https://$Pat@github.com/FUJIRICE/fujisanroku-rice.git"
git remote set-url origin $remoteUrl 2>&1 | Out-Null

git config user.name  "FUJI RICE Bot" 2>&1 | Out-Null
git config user.email "iwataku926@gmail.com" 2>&1 | Out-Null

git pull --rebase origin main 2>&1 | Out-Null
git add diary/ 2>&1 | Out-Null

$commitMsg = "$dateStr ${session}の日記"
$diff = git diff --staged --name-only 2>&1
if ($diff) {
    git commit -m $commitMsg 2>&1 | Out-Null
    git push origin main 2>&1 | Out-Null
    Write-Host "   ✅ プッシュ完了: $commitMsg" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  変更なし（スキップ）" -ForegroundColor Gray
}

Pop-Location

# ─────────────────────────────────────
# Make.com Webhook 送信（SNS自動投稿）
# ─────────────────────────────────────
if ($WebhookUrl -ne "" -and $diff) {
    Write-Host ""
    Write-Host "【Make.com Webhook 送信】" -ForegroundColor White

    # 写真のGitHub Raw URL（あれば）
    $photoRawUrl = ""
    if ($selectedPhoto) {
        $encodedSession = [System.Uri]::EscapeDataString($session)
        $photoRawUrl = "https://raw.githubusercontent.com/FUJIRICE/fujisanroku-rice/main/diary/photos/$yearStr/$dateStr-$encodedSession$ext"
    }

    # 投稿本文（Instagram/Faceboog用）
    $caption = @"
$greeting。$message

📅 $dateJP

#富士山麓 #富士米 #fujirice #お米 #山梨 #農家 #rice #japan
"@

    $body = @{
        date        = $dateStr
        session     = $session
        greeting    = $greeting
        message     = $message
        caption     = $caption
        photo_url   = $photoRawUrl
        has_photo   = ($photoRawUrl -ne "")
    } | ConvertTo-Json -Compress

    try {
        $response = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 15
        Write-Host "   ✅ Webhook送信完了 → Instagram/Facebook投稿へ" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Webhook送信失敗: $_" -ForegroundColor Yellow
        Write-Host "   （日記はGitHubに保存済みです）" -ForegroundColor Gray
    }
} elseif ($WebhookUrl -eq "") {
    Write-Host ""
    Write-Host "   ℹ️  WebhookUrl未設定 → SNS自動投稿スキップ" -ForegroundColor Gray
    Write-Host "   💡 Make.comのWebhook URLを取得後、-WebhookUrl パラメータで設定してください" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host " 🎉 完了！Cloudflareが自動更新します" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
