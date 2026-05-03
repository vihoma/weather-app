#! C:/Program\ Files/PowerShell/7/pwsh.exe
#
# An hook script to verify what is about to be committed. Called by "git commit"
# with no arguments.  The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit.ps1".

Function Invoke-Utility {
  $exe, $argsForExe = $Args
  $ErrorActionPreference = 'Continue' # to prevent 2> redirections from triggering a terminating error.
  try { & $exe $argsForExe } catch { Throw } # catch triggered ONLY if $exe not found, not for errors reported by $exe itself
  if ($LASTEXITCODE) { Throw "$exe indicated failure (exit code $LASTEXITCODE; full command: $Args)." }
}

# Error action preference to stop the commit if any command fails.
$ErrorActionPreference = "Stop"

$against = ""
$git_status = (git rev-parse --verify HEAD 2>&1) -ne $null
if ($git_status -eq $true) {
  $against = "HEAD"
} else {
	# Initial commit: diff against an empty tree object
	$against = (git hash-object -t tree $null)
}

# If you want to allow non-ASCII filenames set this variable to true.
$allownonascii = (git config --type=bool hooks.allownonascii)

# Rest of the script is taken from the original pre-commit hook, with some
# modifications to work in PowerShell and to run Ruff linter and formatter
# checks on the Python files in the src/weather_app directory.

# Cross platform projects tend to avoid non-ASCII filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if ($allownonascii -eq $false) {
	# Note that the use of brackets around a tr range is ok here, (it's
	# even required, for portability to Solaris 10's /usr/bin/tr), since
	# the square bracket bytes happen to fall in the designated range.
  # Use the C locale to avoid issues with character ranges and non-ASCII
  # characters.
  $oldLC_ALL = $env:LC_ALL
  $env:LC_ALL = "C"
	test.exe [(git diff-index --cached --name-only --diff-filter=A -z $against |
  tr.exe -d '[ -~]\0' | wc.exe -c) -ne 0] &&{
    # Restore the original LC_ALL value before printing the error message and
    # stopping the commit.
    $env:LC_ALL = $oldLC_ALL
    Write-Error "
    Error: Attempt to add a non-ASCII file name.
    This can cause problems if you want to work with people on other platforms.
    To be portable it is advisable to rename the file.

    If you know what you are doing you can disable this check using
    git config hooks.allownonascii true
    "
  }
}

# Error suffix to use in the error messages.
$error_suffix = "Please fix the issues before committing."

# Run Ruff linter on the source tree, and fail if there are any differences.
try {
  Write-Host "Checking and fixing linting issues in the source tree (Ruff)..."
  ruff check --fix --quiet src/
} catch {
  Write-Error "Error: Ruff linter encountered issues fixing the source tree:
  $($_.Exception.Message)
  $error_suffix"
}

# Run Ruff formatting check on source tree, and fail if there are any differences.
try {
  Write-Host "Checking and fixing formatting issues in the source tree (Ruff)..."
  ruff format --quiet src/
} catch {
  Write-Error "Error: ruff formatter encountered issues formatting the source tree:
  $($_.Exception.Message)
  $error_suffix"
}

# Run Pyrefly on the source tree, and fail if there are any errors.
try {
  Write-Host "Checking and fixing type annotation issues in the source tree (Pyrefly)..."
  pyrefly check --output-format omit-errors --summary=none src/
} catch {
  Write-Error "Error: Pyrefly encountered issues fixing the source tree:
  $($_.Exception.Message)
  $error_suffix"
}

# If we got here, it means all checks passed and the files in the source tree
# have been fixed. We need to re-stage the files in case Ruff made any changes
# to them.
if ((git diff --cached --name-only src/ | Measure-Object).Count -gt 0) {
  Write-Host "Re-staging the files in the source tree after fixing issues..."
  Invoke-Utility git add src/
}
