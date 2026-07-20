from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".sql", ".toml", ".txt", ".example"}


def _repository_text() -> str:
    chunks: list[str] = []
    for path in ROOT.rglob("*"):
        if path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name == ".env.example"):
            if ".git" not in path.parts:
                chunks.append(path.read_text(errors="ignore"))
    return "\n".join(chunks)


def test_no_company_specific_branding_remains():
    text = _repository_text().lower()
    prohibited = [
        "hilton " + "grand vacations",
        "hgv_" + "data_platform",
    ]
    for value in prohibited:
        assert value not in text, value


def test_no_obvious_secret_material_is_committed():
    text = _repository_text()
    patterns = [
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"(?i)(client_secret|api_key|access_token)\s*=\s*['\"][^'\"]{12,}['\"]",
    ]
    for pattern in patterns:
        assert re.search(pattern, text) is None, pattern
