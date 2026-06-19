# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
privately via the GitHub Security Advisory system at
<https://github.com/vihoma/weather-app/security/advisories/new>.

**Do not open a public issue.** We aim to acknowledge reports within 48 hours
and provide a timeline for resolution within 5 business days.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.8.x   | ✅ Active support  |
| 0.7.x   | ✅ Security fixes  |
| < 0.7   | ❌ End of life     |

## Hardening Measures (applied)

- **API key storage**: Uses system keyring (`keyring`) by default. CLI no
  longer accepts `--key` to prevent shell-history exposure.
- **Rich traceback**: `show_locals` is disabled in production builds to
  prevent secret leakage in stack traces. Developers may opt in via
  `WEATHER_DEBUG=1`.
- **Logging**: `SensitiveDataFilter` masks API keys, passwords, tokens, and
  secrets in all log output.
- **Cache security**: On-disk cache files are written atomically (temp file +
  atomic rename) and path containment is verified to prevent symlink attacks.
- **Input validation**: Location strings are capped at 256 characters and
  sanitised before logging to prevent log injection.
- **Configuration**: Pydantic model uses `extra="ignore"` to prevent unknown
  fields from being silently stored.
- **Exception handling**: Broad `except Exception` handlers have been
  narrowed to specific exception types throughout the codebase.
- **YAML parsing**: Uses `yaml.safe_load` exclusively — no arbitrary code
  execution risk.
- **Dependency scanning**: `pip-audit` runs in CI on every push and pull
  request.
