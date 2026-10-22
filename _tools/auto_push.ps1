# Tự động commit + đẩy D:\AI lên GitHub (repo private archivina-ai)
# Gọi từ: hook SessionEnd của Claude Code và Task Scheduler lúc 18:00 hằng ngày.
# Cách dùng: powershell -NoProfile -ExecutionPolicy Bypass -File D:\AI\_tools\auto_push.ps1 [-Source <nguồn>]
# Không xoá file nào trên máy; chỉ ghi log vào D:\AI\_tmp\auto_push.log

param([string]$Source = "thủ công")

$ErrorActionPreference = "Continue"
$repo    = "D:\AI"
$git     = "C:\Program Files\Git\cmd\git.exe"
$logFile = Join-Path $repo "_tmp\auto_push.log"
$msgFile = Join-Path $repo "_tmp\auto_push_msg.txt"
$lockDir = Join-Path $repo "_tmp\auto_push.lock"
$maxMB   = 50   # file lớn hơn mức này thì không đẩy (GitHub chặn > 100 MB)

function Write-Log([string]$text) {
    $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Source, $text
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

# Khoá đơn giản để hook và tác vụ 18:00 không chạy chồng nhau
try { New-Item -ItemType Directory -Path $lockDir -ErrorAction Stop | Out-Null }
catch {
    $age = (Get-Date) - (Get-Item $lockDir).CreationTime
    if ($age.TotalMinutes -lt 15) { Write-Log "Đang có lần chạy khác, bỏ qua."; exit 0 }
    # Khoá treo quá 15 phút (lần trước bị ngắt) thì dùng lại
}

try {
    Set-Location $repo
    & $git add -A

    # Bỏ khỏi commit các file quá lớn (vẫn giữ nguyên trên máy)
    $staged = & $git -c core.quotepath=false diff --cached --name-only --diff-filter=AM
    foreach ($f in $staged) {
        $p = Join-Path $repo $f
        if ((Test-Path $p) -and ((Get-Item $p).Length / 1MB -gt $maxMB)) {
            & $git reset -q -- "$f"
            Write-Log "Bỏ qua file lớn hơn $maxMB MB: $f"
        }
    }

    & $git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Write-Log "Không có thay đổi."; exit 0 }

    $count = (& $git diff --cached --name-only | Measure-Object).Count
    $msg = "Tự động lưu {0} ({1}, {2} file)" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $Source, $count
    [IO.File]::WriteAllText($msgFile, $msg, (New-Object Text.UTF8Encoding $false))
    & $git commit -q -F $msgFile
    if ($LASTEXITCODE -ne 0) { Write-Log "Lỗi commit."; exit 1 }

    & $git push -q origin HEAD 2>&1 | ForEach-Object { Write-Log "git: $_" }
    if ($LASTEXITCODE -ne 0) { Write-Log "Lỗi push (commit vẫn nằm trên máy, lần sau sẽ đẩy tiếp)."; exit 1 }
    Write-Log "Đã đẩy $count file."
}
finally {
    Remove-Item $lockDir -Force -ErrorAction SilentlyContinue
}
