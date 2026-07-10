"""Genera un ZIP navegable offline de la documentación (docs/ → tramalia-docs-offline.zip).

Separado del build normal a propósito: el plugin `offline` de mkdocs-material
reescribe las URLs a *.html sin barra final (para que funcionen con file://),
lo que ROMPERÍA los enlaces `/tramalia/<pagina>/` del sitio ya publicado si se
mezclara con el `mkdocs.yml` que usa `mkdocs gh-deploy`. Por eso este script
inyecta el plugin solo en un mkdocs.yml temporal, en memoria, y construye a un
directorio aparte — el sitio en vivo nunca se toca.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "mkdocs.yml"
OUT_ZIP = ROOT / "tramalia-docs-offline.zip"


def main() -> int:
    text = CONFIG.read_text(encoding="utf-8")
    marker = "plugins:\n  - search\n"
    if marker not in text:
        print("no se encontró el bloque 'plugins: - search' esperado en mkdocs.yml", file=sys.stderr)
        return 1
    patched = text.replace(marker, marker + "  - offline\n", 1)

    # el config temporal vive en la RAÍZ del repo (no en un tempdir del SO):
    # mkdocs resuelve docs_dir/paths relativos al archivo de config, no al cwd.
    tmp_config = ROOT / ".mkdocs.offline.tmp.yml"
    tmp_config.write_text(patched, encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            site_dir = Path(tmp) / "site-offline"
            cp = subprocess.run(
                [sys.executable, "-m", "mkdocs", "build", "--strict",
                 "-f", str(tmp_config), "-d", str(site_dir)],
                cwd=ROOT,
            )
            if cp.returncode != 0:
                return cp.returncode

            if OUT_ZIP.exists():
                OUT_ZIP.unlink()
            with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in site_dir.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(site_dir))
    finally:
        tmp_config.unlink(missing_ok=True)

    size_mb = OUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"listo: {OUT_ZIP} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
