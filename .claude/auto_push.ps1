param()
$raw = [Console]::In.ReadToEnd()
$proj = 'C:\Users\ayd3n\Desktop\ACCOUNTING_AGENT'
Push-Location $proj
try {
    git add . 2>$null
    git diff --cached --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        try {
            $fname = ($raw | ConvertFrom-Json).tool_input.file_path
            $label = if ($fname) { Split-Path $fname -Leaf } else { 'files' }
        } catch {
            $label = 'files'
        }
        git commit -m "auto: update $label" 2>&1 | Out-Null
        git push origin main 2>&1 | Out-Null
    }
} finally {
    Pop-Location
}
exit 0
