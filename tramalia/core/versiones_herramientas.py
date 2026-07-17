"""Pin reusable versions of external tools used by the project."""

VERSION_ACTIONLINT = "1.7.12"
VERSION_ACTIONLINT_PY = "1.7.12.24"
VERSION_GITLEAKS = "8.30.1"
VERSION_SEMGREP = "1.169.0"
VERSION_SERENA = "1.6.0"
SHA_SERENA = "93b9544ea9def8e93cb6a90f8ea67befe3c8fee4"
FUENTE_SERENA = f"git+https://github.com/oraios/serena.git@{SHA_SERENA}"

__all__ = [
    "VERSION_ACTIONLINT",
    "VERSION_ACTIONLINT_PY",
    "VERSION_GITLEAKS",
    "VERSION_SEMGREP",
    "VERSION_SERENA",
    "SHA_SERENA",
    "FUENTE_SERENA",
]
