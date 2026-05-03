#!pwsh.exe
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit.ps1".

# Error action preference to stop the commit if any command fails.
$ErrorActionPreference = "Stop"

$against = ""
$git_status = (git rev-parse --verify HEAD 2>&1 > $null)
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

# Run Ruff linter on the files to be committed, and fail if there are any differences.
(git diff --cached --name-only --diff-filter=ACM $against -- |
grep 'src/weather_app/.*\.py$' | xargs ruff check --quiet) ||
Write-Error "Error: Ruff linter found issues in the files to be committed.
$error_suffix"

# Run Ruff formatting check on the files to be committed, and fail if there are any differences.
(git diff --cached --name-only --diff-filter=ACM $against -- |
grep 'src/weather_app/.*\.py$' | xargs ruff format --check --quiet) ||
Write-Error "Error: ruff formatter found issues in the files to be committed.
$error_suffix"

# If there are whitespace errors, print the offending file names and fail.
git diff-index --check --cached $against -- ||
Write-Error "Error: whitespace errors found in the files to be committed.
$error_suffix"

