#!pwsh.exe
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit.ps1".

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

# Redirect output to stderr.
2>&1

# Cross platform projects tend to avoid non-ASCII filenames; prevent
# them from being added to the repository. We exploit the fact that the
# printable range starts at the space character and ends with tilde.
if ($allownonascii -eq $false) {
	# Note that the use of brackets around a tr range is ok here, (it's
	# even required, for portability to Solaris 10's /usr/bin/tr), since
	# the square bracket bytes happen to fall in the designated range.
	test.exe ($env:LC_ALL = "C"; git diff-index --cached --name-only --diff-filter=A -z $against |
  tr.exe -d '[ -~]\0' | wc.exe -c) -ne 0 {
    Write-Host "
    Error: Attempt to add a non-ASCII file name.
    This can cause problems if you want to work with people on other platforms.
    To be portable it is advisable to rename the file.

    If you know what you are doing you can disable this check using
    git config hooks.allownonascii true
    "
    exit 1
  }
}

# Run Ruff linter on the files to be committed, and fail if there are any differences.
git diff --cached --name-only --diff-filter=ACM $against -- |
grep 'src/weather_app/.*\.py$' | xargs ruff check --quiet ||
(Write-Host "Error: ruff found issues in the files to be committed.
Please fix them before committing." && exit 1)

# If there are whitespace errors, print the offending file names and fail.
git diff-index --check --cached $against -- ||
(Write-Host "Error: whitespace errors found in the files to be committed.
Please fix them before committing." && exit 1)

# Run Ruff formatting check on the files to be committed, and fail if there are any differences.
git diff --cached --name-only --diff-filter=ACM $against -- |
grep 'src/weather_app/.*\.py$' | xargs ruff format --check --quiet ||
(Write-Host "Error: ruff found formatting issues in the files to be committed.
Please fix them before committing." && exit 1)
