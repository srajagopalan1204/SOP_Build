<# 
  verify_slide_v1a.ps1  (PS 5.1 compatible)
  Checks which text would be captured as each slide's Title and writes a report.
  Streams that report to BOTH the PowerShell console and a log file.

  Usage:
    powershell -ExecutionPolicy Bypass -File "C:\Users\scottuser\Documents\SonetLumier\Code\verify_slide_v1a.ps1" `
      -Path "C:\Users\scottuser\Documents\SonetLumier\Input\PPS_SRO_102425_1014.pptx" `
      -Out  "C:\Users\scottuser\Documents\SonetLumier\Logs\verify_SRO_$(Get-Date -f 'MMddyy_HHmm').txt"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Path,

    [Parameter()]
    [string]$Out = "$(Join-Path -Path (Get-Location) -ChildPath ('verify_' + (Get-Date -f 'MMddyy_HHmm') + '.txt'))",

    # Treat any line matching this as boilerplate; exclude from title candidates
    [Parameter()]
    [string]$SkipRegex = '^\s*(Base\s+Created|Created\s+by|Prepared\s+by)\b'
)

# Collect report lines in memory AND echo them live to console.
$global:ReportLines = New-Object System.Collections.Generic.List[string]

function Write-Both {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Message
    )
    # Show immediately in console
    Write-Host $Message
    # Stash for final log write
    $global:ReportLines.Add($Message) | Out-Null
}

function Get-TitleText {
    param(
        $slide,
        [string]$skipPattern
    )

    # 1) Real Title placeholder if present
    try {
        if ($slide.Shapes.HasTitle) {
            $t = $slide.Shapes.Title.TextFrame.TextRange.Text
            if ($t -and $t.Trim().Length -gt 0) {
                return ($t -replace "`r|`n",' ').Trim()
            }
        }
    } catch {}

    # 2) Score text shapes (name/placeholder/size/top heuristics)
    $candidates = @()
    foreach ($sh in $slide.Shapes) {
        try {
            if ($sh.HasTextFrame -and $sh.TextFrame.HasText) {
                $txt = [string]$sh.TextFrame.TextRange.Text
                if (-not [string]::IsNullOrWhiteSpace($txt)) {
                    $txt = ($txt -replace "`r|`n",' ').Trim()

                    if ($skipPattern -and ($txt -match $skipPattern)) { continue }

                    $phType = $null;       try { $phType = $sh.PlaceholderFormat.Type } catch {}
                    $isTitleName = $false; try { $isTitleName = ($sh.Name -like 'Title*') } catch {}
                    $fontSize = 0;         try { $fontSize = [int]$sh.TextFrame.TextRange.Font.Size } catch {}
                    $top = 99999;          try { $top      = [double]$sh.Top } catch {}

                    $score = 0
                    if ($phType -in 1,3) { $score += 100 } # Title, CenterTitle
                    if ($phType -eq 2)   { $score += 80  } # Subtitle
                    if ($isTitleName)    { $score += 50  }
                    $score += [Math]::Min($fontSize,72)
                    $score += [Math]::Max(0, 400 - [Math]::Min($top,400)) # higher on slide => more points

                    $candidates += [PSCustomObject]@{
                        Score = $score
                        Text  = $txt
                    }
                }
            }
        } catch {}
    }

    if ($candidates.Count -gt 0) {
        $best = $candidates | Sort-Object -Property Score -Descending | Select-Object -First 1
        return $best.Text
    }

    return $null
}

# Open PowerPoint and walk slides
$pp   = $null
$pres = $null
try {
    $pp = New-Object -ComObject PowerPoint.Application

    # constants
    $msoTrue  = -1
    $msoFalse = 0

    $pres = $pp.Presentations.Open($Path, $msoTrue, $msoFalse, $msoFalse)

    # Header lines
    Write-Both ("VERIFY: {0}" -f (Get-Item $Path).Name)
    Write-Both ("Generated: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
    Write-Both ("SkipRegex: {0}" -f $SkipRegex)
    Write-Both ""

    $emptyOrSkipped = 0
    $i = 0
    foreach ($slide in $pres.Slides) {
        $i++
        $title = Get-TitleText -slide $slide -skipPattern $SkipRegex
        if ($null -eq $title) { $title = "" }
        if ([string]::IsNullOrWhiteSpace($title)) { $emptyOrSkipped++ }

        Write-Both (('Slide {0}: "{1}"' -f $i, $title))
    }

    Write-Both ""
    Write-Both ("Slides total: {0}" -f $i)
    Write-Both ("Empty/Skipped titles: {0}" -f $emptyOrSkipped)

    # Write final report to log file on disk
    $global:ReportLines | Set-Content -Path $Out -Encoding UTF8
    Write-Host ("Saved log -> {0}" -f $Out)
}
finally {
    if ($pres) { try { $pres.Close() | Out-Null } catch {} }
    if ($pp)   { try { $pp.Quit()  | Out-Null } catch {} }
}
