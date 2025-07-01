# Change the folder path to the location you want to scan for duplicates
# Define path to Downloads folder
$downloadsPath = Join-Path $env:USERPROFILE "Downloads"

# Get all files recursively in Downloads
$files = Get-ChildItem -Path $downloadsPath -Recurse -File -ErrorAction SilentlyContinue

# Store file hashes and their paths
$hashes = @{}

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

# Identify duplicates
$duplicates = $hashes.Values | Where-Object { $_.Count -gt 1 }

# Delete all but one in each group
foreach ($group in $duplicates) {
    # Keep the first file, delete the rest
    $filesToDelete = $group[1..($group.Count - 1)]
    foreach ($fileToDelete in $filesToDelete) {
        try {
            Remove-Item -Path $fileToDelete -Force
            Write-Host "Deleted duplicate: $fileToDelete"
        } catch {
            Write-Host "Could not delete: $fileToDelete - $($_.Exception.Message)"
        }
    }
}

Write-Host "`n✅ Cleanup complete. All duplicate files (except one copy) have been deleted from Downloads."
