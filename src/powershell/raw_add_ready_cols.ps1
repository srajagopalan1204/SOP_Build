<#
  raw_add_ready_cols.ps1

  Purpose:
    Take an existing RAW CSV (from your working exp_slide_n_csv*) and
    add extra READY-style columns as EMPTY fields (no logic, no changes
    to existing data).

  Existing RAW columns (example):
    Source_PPT, SlideIndex, SelectionTitle, Title, Code,
    Title_short, Image_sub_url, Deci_Question, Next1_Code, Next2_Code, ...

  New columns added (all blank):
    
  Image_web    # final SOP image path (you will fill)
  Narr1_seed
  Desc_Next1
  Desc_Next2
  Desi_Ques
  Narr2_seed
  Narr3_seed
  UAP_Label
  UAP_URL
  Start_Here
  Entity
  Function
  SubEntity
  Exclude


  Usage example:

    powershell -ExecutionPolicy Bypass -File "C:\Users\scottuser\Documents\SonetLumier\Code\raw_add_ready_cols.ps1" `
      -In  "C:\Users\scottuser\Documents\SonetLumier\Slide_Map\LineEnt2_Raw_120925_1558.csv" `
      -Out "C:\Users\scottuser\Documents\SonetLumier\Slide_Map\LineEnt2_Raw_120925_1558_READYBASE.csv"

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
  $Out  = Join-Path $dir ($base + "_READYBASE.csv")
}

Write-Log "Input : $In"
Write-Log "Output: $Out"

# Import existing RAW CSV
$rows = Import-Csv -Path $In

if (-not $rows -or $rows.Count -eq 0) {
  throw "No rows found in input CSV: $In"
}

# New columns to add (all blank)
$newCols = @(
  'Image_web',      # final SOP image path (you will fill)
  'Narr1_seed',
  'Desc_Next1',
  'Desc_Next2',
  'Desi_Ques',
  'Narr2_seed',
  'Narr3_seed',
  'UAP_Label',
  'UAP_URL',
  'Start_Here',
  'Entity',
  'Function',
  'SubEntity',
  'Exclude'
)     


# Ensure each row has these properties; if missing, add as empty string
foreach ($row in $rows) {
  foreach ($col in $newCols) {
    if (-not $row.PSObject.Properties.Match($col)) {
      Add-Member -InputObject $row -MemberType NoteProperty -Name $col -Value ""
    }
  }
}

# Preserve original column order, then append the new ones at the end
$existingCols = $rows[0].PSObject.Properties.Name
$finalCols = @()
$finalCols += $existingCols
foreach ($c in $newCols) {
  if (-not ($finalCols -contains $c)) {
    $finalCols += $c
  }
}

Write-Log ("Final columns: " + ($finalCols -join ", "))

# Export with columns in the chosen order
$rows |
  Select-Object $finalCols |
  Export-Csv -Path $Out -Encoding UTF8 -NoTypeInformation

Write-Log "Wrote CSV with added empty READY-style columns."
