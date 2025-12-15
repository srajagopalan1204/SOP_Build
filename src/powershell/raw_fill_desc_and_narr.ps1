<#
  raw_fill_desc_and_narr.ps1

  Purpose:
    Helper script to fill:
      - Desc_Next1  from Title_short of Next1_Code
      - Desc_Next2  from Title_short of Next2_Code
      - Desi_Ques   for D* rows from Title_short + "?"
      - Narr1_seed  from this row's Title_short

    Assumes the input CSV already has these columns (from raw_add_ready_cols.ps1):
      Code, Title_short, Next1_Code, Next2_Code,
      Desc_Next1, Desc_Next2, Desi_Ques, Narr1_seed

  Behavior:
    - Only fills fields that are currently empty (so you can manually override later).
    - Does NOT change any other columns.

  Example:

    powershell -ExecutionPolicy Bypass -File "C:\Users\scottuser\Documents\SonetLumier\Code\raw_fill_desc_and_narr.ps1" `
      -In  "C:\Users\scottuser\Documents\SonetLumier\Slide_Map\LineEnt2_Raw_120925_1558_READYBASE.csv" `
      -Out "C:\Users\scottuser\Documents\SonetLumier\Slide_Map\LineEnt2_Raw_120925_1558_READYBASE_ENH.csv"

#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$In,

  [Parameter(Mandatory = $false)]
  [string]$Out
)

function Write-Log {
  param([string]$msg)
  $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
  Write-Host $line
}

if (-not (Test-Path -LiteralPath $In)) {
  throw "Input CSV not found: $In"
}

# Derive default Out path if not provided
if (-not $Out -or [string]::IsNullOrWhiteSpace($Out)) {
  $dir  = Split-Path -Parent -Path $In
  $base = [System.IO.Path]::GetFileNameWithoutExtension($In)
  $Out  = Join-Path $dir ($base + "_ENH.csv")
}

Write-Log "Input : $In"
Write-Log "Output: $Out"

# Import input CSV
$rows = Import-Csv -Path $In
if (-not $rows -or $rows.Count -eq 0) {
  throw "No rows found in input CSV: $In"
}

# Check necessary columns exist
$neededCols = @(
  'Code',
  'Title_short',
  'Next1_Code',
  'Next2_Code',
  'Desc_Next1',
  'Desc_Next2',
  'Desi_Ques',
  'Narr1_seed'
)

$existingCols = $rows[0].PSObject.Properties.Name
foreach ($c in $neededCols) {
  if (-not ($existingCols -contains $c)) {
    throw "Required column '$c' not found in CSV. Run raw_add_ready_cols.ps1 first or check the file."
  }
}

# Build a lookup: Code -> Title_short
$codeToTitle = @{}
foreach ($row in $rows) {
  $code = $row.Code
  if (-not [string]::IsNullOrWhiteSpace($code)) {
    # If duplicate codes exist, last one wins (but normally codes are unique)
    $codeToTitle[$code] = $row.Title_short
  }
}

# Preserve column order
$colOrder = $rows[0].PSObject.Properties.Name

# Fill helper fields
foreach ($row in $rows) {

  $code       = $row.Code
  $titleShort = $row.Title_short

  # 1) Narr1_seed from this row's Title_short (if empty)
  if ([string]::IsNullOrWhiteSpace($row.Narr1_seed) -and
      -not [string]::IsNullOrWhiteSpace($titleShort)) {

    $row.Narr1_seed = $titleShort
  }

  # 2) Desi_Ques for decision rows (Code starts with D)
  if (-not [string]::IsNullOrWhiteSpace($code) -and $code -match '^D\d+') {
    if ([string]::IsNullOrWhiteSpace($row.Desi_Ques) -and
        -not [string]::IsNullOrWhiteSpace($titleShort)) {

      $q = $titleShort.Trim()
      if ($q -notmatch '\?$') {
        $q += "?"
      }
      $row.Desi_Ques = $q
    }
  }

  # 3) Desc_Next1 from Title_short of Next1_Code target (if exists)
  $n1 = $row.Next1_Code
  if ([string]::IsNullOrWhiteSpace($row.Desc_Next1) -and
      -not [string]::IsNullOrWhiteSpace($n1) -and
      $codeToTitle.ContainsKey($n1)) {

    $row.Desc_Next1 = $codeToTitle[$n1]
  }

  # 4) Desc_Next2 from Title_short of Next2_Code target (if exists)
  $n2 = $row.Next2_Code
  if ([string]::IsNullOrWhiteSpace($row.Desc_Next2) -and
      -not [string]::IsNullOrWhiteSpace($n2) -and
      $codeToTitle.ContainsKey($n2)) {

    $row.Desc_Next2 = $codeToTitle[$n2]
  }
}

# Export with original column order preserved
$rows |
  Select-Object $colOrder |
  Export-Csv -Path $Out -Encoding UTF8 -NoTypeInformation

Write-Log "Wrote enhanced CSV with Desc_Next1/2, Desi_Ques, Narr1_seed filled where blank."
