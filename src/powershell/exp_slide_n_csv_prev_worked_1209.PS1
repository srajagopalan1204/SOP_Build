<#
  exp_slide_n_csv.ps1  (Windows PowerShell 5.1 compatible)

  Exports slide PNGs and writes OutMap CSV with columns:
    Source_PPT, SlideIndex, SelectionTitle, Title, Code, Title_short,
    Image_sub_url, Deci_Question, Next1_Code, Next2_Code

  SelectionTitle = text from the chosen title shape on the slide (line breaks -> " | ")
  Title          = cleaned single-line title text
  Code           = code like S1, D3, Y2, N4, M1 (parsed from Title)
  Title_short    = main label, with:
                     - leading "S1. " / "M1. " removed
                     - anything after the first dash removed
                     - unicode dashes/quotes normalized

  Usage:
    powershell -ExecutionPolicy Bypass -File .\exp_slide_n_csv.ps1 `
      -Path      "C:\Users\scottuser\Documents\SonetLumier\Input\PPS_SRO_102425_1014.pptx" `
      -OutDir    "C:\Users\scottuser\Documents\SonetLumier\images\SRO" `
      -OutMapDir "C:\Users\scottuser\Documents\SonetLumier\Slide_Map" `
      -Sop       "SRO" `
      -Width     1600
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Path,
  [Parameter(Mandatory = $true)][string]$OutDir,
  [Parameter(Mandatory = $true)][string]$OutMapDir,
  [string]$Sop,
  [string]$LogPath,
  [int]$Width = 1600,

  # Regex to trim known SOP suffix from Title before parsing
  [string]$TrimSuffixRegex = '(\s*[-–—]\s*Service\s+Request\s+Order\s*\(SRO\))$',

  # Leading letters that define a valid code (S1, D2, Y3, N4, M1, etc.)
  [ValidatePattern('^[A-Za-z]+$')]
  [string]$AcceptedCodePrefixes = 'SDYNM'
)

function New-Timestamp { Get-Date -Format 'MMddyy_HHmm' }

function Write-Log {
  param([string]$msg)
  $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
  Write-Host $line
  if ($script:LogPath) {
    Add-Content -Path $script:LogPath -Value $line -Encoding UTF8
  }
}

function Ensure-Dir {
  param([string]$d)
  if (-not (Test-Path -LiteralPath $d)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
  }
}

# Choose the title-like shape, return both raw and cleaned text
function Get-TitleCandidate {
  param($slide, [string]$skipPattern)

  function _mk {
    param($shape, [string]$txt, [int]$score, [string]$reason)
    # TextRaw keeps multi-line intent but flattens newlines to " | " for CSV friendliness
    $raw   = ($txt -replace "`r`n",' | ' -replace "`r",' | ' -replace "`n",' | ').Trim()
    # TextClean is a single-line, squashed version
    $clean = ($txt -replace "`r|`n",' ' -replace '\s+',' ').Trim()
    [pscustomobject]@{
      Shape      = $shape
      Score      = $score
      Reason     = $reason
      TextRaw    = $raw
      TextClean  = $clean
    }
  }

  # 1) Strong preference: a true Title placeholder
  try {
    if ($slide.Shapes.HasTitle) {
      $t = [string]$slide.Shapes.Title.TextFrame.TextRange.Text
      if (-not [string]::IsNullOrWhiteSpace($t)) {
        return (_mk -shape $slide.Shapes.Title -txt $t -score 999 -reason 'placeholder')
      }
    }
  } catch {}

  # 2) Otherwise, score all text shapes
  $cands = @()
  foreach ($sh in $slide.Shapes) {
    try {
      if ($sh.HasTextFrame -and $sh.TextFrame.HasText) {
        $txt = [string]$sh.TextFrame.TextRange.Text
        if ([string]::IsNullOrWhiteSpace($txt)) { continue }

        # skip boilerplate footer/credit blobs
        if ($skipPattern -and ($txt -match $skipPattern)) { continue }

        $phType      = $null;       try { $phType      = $sh.PlaceholderFormat.Type } catch {}
        $isTitleName = $false;      try { $isTitleName = ($sh.Name -like 'Title*') } catch {}
        $fontSize    = 0;           try { $fontSize    = [int]$sh.TextFrame.TextRange.Font.Size } catch {}
        $top         = 99999;       try { $top         = [double]$sh.Top } catch {}

        # Score:
        # +100 for Title / CenterTitle placeholder
        # +80  for Subtitle placeholder
        # +50  if shape name starts with "Title"
        # +font size (bigger = more title-y)
        # +position bonus for being toward the top
        $score = 0
        if ($phType -in 1,3) { $score += 100 }   # title / center title
        if ($phType -eq 2)   { $score += 80  }   # subtitle
        if ($isTitleName)    { $score += 50  }
        $score += [Math]::Min($fontSize,72)
        $score += [Math]::Max(0, 400 - [Math]::Min($top,400))

        $cands += (_mk -shape $sh -txt $txt -score $score -reason ($(if ($isTitleName) {'name|heur'} else {'heur'})))
      }
    } catch {}
  }

  if ($cands.Count -gt 0) {
    return ($cands | Sort-Object Score -Descending | Select-Object -First 1)
  }

  # last resort: empty object
  [pscustomobject]@{
    Shape      = $null
    Score      = 0
    Reason     = 'none'
    TextRaw    = ''
    TextClean  = ''
  }
}

# Parse Code and a base short title from a cleaned Title string
# Example: "S11. Receive Non-stock Inventory - Service Request Order (SRO)"
#  -> Code=S11, Short="Receive Non-stock Inventory - Service Request Order (SRO)"
function Parse-CodeAndShort {
  param([string]$titleClean, [string]$prefixBag)

  $code  = ""
  $short = $titleClean

  # Build a class like [SDYNM] based on AcceptedCodePrefixes
  $bag = ([regex]::Escape($prefixBag)) -replace '\\',''
  $pattern = '^\s*([{0}]\d+)\.\s*(.+?)\s*$' -f $bag

  $m = [regex]::Match($titleClean, $pattern)
  if ($m.Success) {
    $code  = $m.Groups[1].Value
    $short = $m.Groups[2].Value
  }

  return @{ Code = $code; Short = $short }
}

# ---------- Setup and prep ----------
if (-not (Test-Path -LiteralPath $Path)) {
  throw "File not found: $Path"
}

Ensure-Dir $OutDir
Ensure-Dir $OutMapDir

if ([string]::IsNullOrWhiteSpace($Sop)) {
  try {
    $Sop = Split-Path -Leaf -Path $OutDir
    if ([string]::IsNullOrWhiteSpace($Sop)) { $Sop = 'SOP' }
  } catch {
    $Sop = 'SOP'
  }
}

$ts = New-Timestamp
if ([string]::IsNullOrWhiteSpace($LogPath)) {
  $LogPath = Join-Path $OutMapDir ("Export_Log_{0}.txt" -f $ts)
}
$script:LogPath = $LogPath

Write-Log "Starting export for: $Path"
Write-Log "OutDir=$OutDir  OutMapDir=$OutMapDir  SOP=$Sop  Prefixes=$AcceptedCodePrefixes"

$csvPath = Join-Path $OutMapDir ("{0}_Raw_{1}.csv" -f $Sop, $ts)

# PowerPoint COM constants (avoid enum casting issues)
$msoTrue  = -1
$msoFalse = 0

# ---------- Open PowerPoint, walk slides, export ----------
$pp   = $null
$pres = $null

try {
  $pp = New-Object -ComObject PowerPoint.Application
  $pp.Visible = $msoTrue

  # Open(ReadOnly=$msoTrue, Untitled=$msoFalse, WithWindow=$msoTrue)
  $pres = $pp.Presentations.Open($Path, $msoTrue, $msoFalse, $msoTrue)

  $rows = New-Object System.Collections.Generic.List[hashtable]
  $skipRegex = '^\s*(Base\s+Created|Created\s+by|Prepared\s+by)\b'

  $i = 0
  foreach ($slide in $pres.Slides) {
    $i++

    #
    # 1. Pick the best "title" shape and grab its text
    #
    $cand = Get-TitleCandidate -slide $slide -skipPattern $skipRegex

    # SelectionTitle keeps the human-facing multiline text (flattened to " | ")
    $selectionTitle = $cand.TextRaw

    # Start Title from TextClean (single line, normalized spaces)
    $titleClean = $cand.TextClean

    #
    # 2. Normalize Title text hard to remove unicode dashes/quotes/non-breaking space,
    #    trim known SOP suffix, etc.
    #

    # Replace NBSP / thin / narrow / hair / zero-width spaces with a normal space.
    # \u00A0 = nbsp, \u2007 figure space, \u202F narrow nb space,
    # \u2009 thin space, \u200A hair space, \u200B zero-width space.
    $titleClean = $titleClean -replace '[\u00A0\u2007\u202F\u2009\u200A\u200B]', ' '

    # Normalize all dash-like chars (hyphen, en dash, em dash, minus, etc.) to ASCII "-"
    # \u2010 hyphen, \u2011 non-breaking hyphen, \u2012 figure dash,
    # \u2013 en dash, \u2014 em dash, \u2212 minus sign.
    $titleClean = $titleClean -replace '[-\u2010\u2011\u2012\u2013\u2014\u2212]', '-'

    # Trim known suffix like " - Service Request Order (SRO)" if present
    if (-not [string]::IsNullOrWhiteSpace($TrimSuffixRegex)) {
      $titleClean = $titleClean -replace $TrimSuffixRegex, ''
    }

    # Normalize fancy quotes to "
    # \u201C left dbl quote, \u201D right dbl quote
    $titleClean = $titleClean -replace '[\u201C\u201D]', '"'

    # Collapse repeating whitespace and trim ends
    $titleClean = $titleClean -replace '\s+', ' '
    $titleClean = $titleClean.Trim()

    #
    # 3. Parse code and first-pass short text
    #
    $parsed = Parse-CodeAndShort -titleClean $titleClean -prefixBag $AcceptedCodePrefixes
    $code  = $parsed.Code
    $short = $parsed.Short

    #
    # 4. Build Title_short:
    #    - Normalize unicode weirdness in $short too
    #    - Chop at first dash
    #    - Drop leading "S1. " pattern if still there
    #
    $short = $short -replace '[\u00A0\u2007\u202F\u2009\u200A\u200B]', ' '
    $short = $short -replace '[-\u2010\u2011\u2012\u2013\u2014\u2212]', '-'

    # Split on first "-" and keep the left-hand side only
    $short = ($short -split '\s*-\s*', 2)[0]

    # Safety: if some title didn't parse code and still starts with "X1. ",
    # remove that leading "<letter><digits>."
    $short = $short -replace '^\s*[A-Za-z]\d+\.\s*', ''

    # Clean up leftover whitespace / quotes
    $short = $short -replace '[\u201C\u201D]', '"'
    $short = $short -replace '\s+', ' '
    $short = $short.Trim()

    #
    # 5. Image naming and export
    #
    if ([string]::IsNullOrWhiteSpace($code)) {
      $imgName = ("SLIDE_{0}.png" -f $i)
    } else {
      $imgName = ("{0}.png" -f $code)
    }

    $imgPath = Join-Path $OutDir $imgName
    $subUrl  = "/images/{0}/{1}" -f $Sop, $imgName

    try {
      if ($Width -gt 0) {
        $slide.Export($imgPath, "PNG", $Width, 0)
      } else {
        $slide.Export($imgPath, "PNG")
      }
      Write-Log ("Exported slide {0} -> {1}" -f $i, $imgName)
    } catch {
      Write-Log ("WARNING: Failed to export slide {0} -> {1}. {2}" -f $i, $imgName, $_.Exception.Message)
    }

    #
    # 6. Add row (Deci_Question left blank for now)
    #
    $rows.Add(@{
      Source_PPT     = (Get-Item $Path).Name
      SlideIndex     = $i
      SelectionTitle = $selectionTitle   # multiline as " | "
      Title          = $titleClean       # cleaned title (single line)
      Code           = $code             # e.g. S1, D3, M1
      Title_short    = $short            # stripped short label
      Image_sub_url  = $subUrl           # /images/SRO/S1.png
      Deci_Question  = ""
      Next1_Code     = ""
      Next2_Code     = ""
    })
  }

  #
  # 7. Post-process Next1_Code & Next2_Code
  #
  for ($idx = 0; $idx -lt $rows.Count; $idx++) {

    # Next1_Code: next row's Code
    if ($idx + 1 -lt $rows.Count) {
      $rows[$idx]['Next1_Code'] = $rows[$idx + 1]['Code']
    } else {
      $rows[$idx]['Next1_Code'] = ""
    }

    # Next2_Code: if this row is D<num>, find N<num> forward
    $thisCode = $rows[$idx]['Code']
    if ($thisCode -match '^(D)(\d+)$') {
      $num = $Matches[2]
      $next2 = ""
      for ($fwd = $idx + 1; $fwd -lt $rows.Count; $fwd++) {
        $c = $rows[$fwd]['Code']
        if ($c -match ("^(N)" + $num + "$")) {
          $next2 = $c
          break
        }
      }
      $rows[$idx]['Next2_Code'] = $next2
    } else {
      $rows[$idx]['Next2_Code'] = ""
    }
  }

  #
  # 8. Write CSV in fixed column order
  #
  $columns = @(
    'Source_PPT',
    'SlideIndex',
    'SelectionTitle',
    'Title',
    'Code',
    'Title_short',
    'Image_sub_url',
    'Deci_Question',
    'Next1_Code',
    'Next2_Code'
  )

  $objects = foreach ($r in $rows) {
    $o = [ordered]@{}
    foreach ($col in $columns) {
      $o[$col] = $r[$col]
    }
    New-Object psobject -Property $o
  }

  $objects | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
  Write-Log ("Wrote CSV: {0}" -f $csvPath)

} catch {
  Write-Log ("ERROR: $($_.Exception.Message)")
  throw
}
finally {
  if ($pres) {
    try { $pres.Close() | Out-Null } catch {}
  }
  if ($pp) {
    try { $pp.Quit() | Out-Null } catch {}
  }
  Write-Log "Done."
}
