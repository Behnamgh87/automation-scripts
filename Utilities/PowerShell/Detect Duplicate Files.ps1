# Change the folder path to the location you want to scan for duplicates
# Get the current user's Downloads folder path
$downloadsPath = Join-Path $env:USERPROFILE "Downloads"

# Recursively collect all files in the Downloads folder
$files = Get-ChildItem -Path $downloadsPath -Recurse -File -ErrorAction SilentlyContinue

# Hashtable to store file hashes and matching paths
$hashes = @{}

# Compute SHA256 hash for each file
foreach ($file in $files) {
    try {
        $hash = Get-FileHash -Path $file.FullName -Algorithm SHA256
        if ($hashes.ContainsKey($hash.Hash)) {
            $hashes[$hash.Hash] += ,$file.FullName
        } else {
            $hashes[$hash.Hash] = @($file.FullName)
        }
    } catch {
        Write-Host "Skipped: $($file.FullName) - $($_.Exception.Message)"
    }
}

# Filter out unique files; only show duplicates
$duplicates = $hashes.Values | Where-Object { $_.Count -gt 1 }

# Display results
if ($duplicates.Count -eq 0) {
    Write-Host "No duplicate files found in $downloadsPath"
} else {
    Write-Host "Duplicate files found:`n"
    $duplicates | ForEach-Object {
        Write-Host "Duplicate group:"
        $_ | ForEach-Object { Write-Host "  - $_" }
        Write-Host ""
    }
}
