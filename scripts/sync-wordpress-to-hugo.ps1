$RepoPath = "C:\Users\iwata\Documents\GitHub\fujisanroku-rice"
$PostsDir = Join-Path $RepoPath "content\posts"
$LogFile  = Join-Path $RepoPath "scripts\sync-wordpress.log"
$RssUrl   = "https://iwataya9.wordpress.com/feed/"
$Pat      = [Environment]::GetEnvironmentVariable('FUJIRICE_GITHUB_PAT', 'User')

$AMP  = [char]38
$LT   = [char]60
$GT   = [char]62
$QT   = [char]34
$APOS = [char]39

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Level] $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

Write-Log "=== sync start ==="

$ScriptsDir = Split-Path $LogFile
if (-not (Test-Path $ScriptsDir)) {
    New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null
}

try {
    $feed = Invoke-WebRequest -Uri $RssUrl -UseBasicParsing -TimeoutSec 30
    $xml = [xml]$feed.Content
    $items = $xml.rss.channel.item
    Write-Log "RSS取得: $($items.Count)件"
} catch {
    Write-Log "RSS取得失敗: $_" "ERROR"
    exit 1
}

$newCount = 0
$skipCount = 0

$imgPat = '<img[^' + $GT + ']+src=' + $QT + '([^' + $QT + ']+)' + $QT
$tagPat = '<[^' + $GT + ']+' + $GT
$brPat  = '<br\s*/?' + $GT
$pPat   = '</p' + $GT

foreach ($item in $items) {
    try {
        $title = $item.title
        $link = $item.link
        $pubDate = [DateTime]::Parse($item.pubDate)
        $content = $item.encoded.'#cdata-section'
        if (-not $content) { $content = $item.description.'#cdata-section' }
        if (-not $content) { $content = $item.description }

        $date = $pubDate.ToLocalTime()
        $dateStr = $date.ToString("yyyy-MM-dd")
        $isoDate = $date.ToString("yyyy-MM-ddTHH:mm:ss+09:00")

        $slug = ""
        if ($link -match "/\d{4}/\d{2}/\d{2}/(.+?)/?$") {
            $slug = $matches[1].TrimEnd('/')
        } else {
            $slug = $title -replace '[\s\\/:*?<>|]', '-'
            $slug = $slug -replace $QT, '-'
        }

        $timeStr = $date.ToString("HHmm")
        $slugSuffix = if ($slug.Length -gt 30) { $slug.Substring(0, 30) } else { $slug }
        $shortSlug = "$dateStr-$timeStr-$slugSuffix"
        $filename = "$shortSlug.md"
        $filepath = Join-Path $PostsDir $filename

        if (Test-Path $filepath) {
            $skipCount++
            continue
        }

     $image = ""
        $mediaThumb = $item.thumbnail
        if ($mediaThumb -and $mediaThumb.url) {
            $image = $mediaThumb.url
        } elseif ($mediaThumb) {
            $image = [string]$mediaThumb
        }
        if (-not $image -and $content -match $imgPat) {
            $image = $matches[1]
        }

        $body = $content
        $body = $body -replace $brPat, "`n"
        $body = $body -replace $pPat, "`n`n"
        $body = $body -replace $tagPat, ''

        $entNbsp = $AMP + 'nbsp;'
        $entAmp  = $AMP + 'amp;'
        $entLt   = $AMP + 'lt;'
        $entGt   = $AMP + 'gt;'
        $entQuot = $AMP + 'quot;'
        $entAp   = $AMP + '#8217;'
        $entLdq  = $AMP + '#8220;'
        $entRdq  = $AMP + '#8221;'

        $body = $body -replace $entNbsp, ' '
        $body = $body -replace $entAmp,  $AMP
        $body = $body -replace $entLt,   $LT
        $body = $body -replace $entGt,   $GT
        $body = $body -replace $entQuot, $QT
        $body = $body -replace $entAp,   $APOS
        $body = $body -replace $entLdq,  $QT
        $body = $body -replace $entRdq,  $QT
        $body = $body -replace "(\r?\n){3,}", "`n`n"
        $body = $body.Trim()

        $titleEsc = $title -replace $QT, ('\' + $QT)

        $md  = "---`n"
        $md += "title: " + $QT + $titleEsc + $QT + "`n"
        $md += "date: $isoDate`n"
        $md += "image: " + $QT + $image + $QT + "`n"
        $md += "slug: " + $QT + $shortSlug + $QT + "`n"
        $md += "draft: false`n"
        $md += "tags:`n"
        $md += '  - "rice"' + "`n"
        $md += '  - "farm"' + "`n"
        $md += "---`n"
        $md += $body + "`n"

        [System.IO.File]::WriteAllText($filepath, $md, [System.Text.UTF8Encoding]::new($false))
        Write-Log "新規作成: $filename"
        $newCount++
    } catch {
        Write-Log "エラー: $_" "ERROR"
    }
}

Write-Log "結果: 新規=$newCount, スキップ=$skipCount"

if ($newCount -gt 0) {
    Push-Location $RepoPath
    try {
        $remoteUrl = "https://$Pat@github.com/FUJIRICE/fujisanroku-rice.git"
        git remote set-url origin $remoteUrl 2>&1 | Out-Null
        git config user.name "FUJI RICE Sync Bot" 2>&1 | Out-Null
        git config user.email "iwataku926@gmail.com" 2>&1 | Out-Null
        git pull --rebase origin main 2>&1 | Out-Null
        git add "content/posts/" 2>&1 | Out-Null
        git commit -m "sync: WordPress記事を$newCount件追加" 2>&1 | Out-Null
        git push origin main 2>&1 | Out-Null
        Write-Log "git push done"
    } finally {
        Pop-Location
    }
}

Write-Log "=== sync end ==="