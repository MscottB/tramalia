"""Normaliza los enlaces de idioma generados por MkDocs a URL absolutas."""

import re
from urllib.parse import urljoin

from mkdocs.plugins import event_priority

PATRON_ETIQUETA_LINK = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
PATRON_REL_ALTERNATIVO = re.compile(
    r"\brel\s*=\s*(?:\"alternate\"|'alternate'|alternate)(?=\s|>)",
    re.IGNORECASE,
)
PATRON_IDIOMA = re.compile(
    r"\bhreflang\s*=\s*(?:\"(?P<doble>[^\"]+)\"|'(?P<simple>[^']+)'|"
    r"(?P<sin_comillas>[^\s>]+))",
    re.IGNORECASE,
)
PATRON_HREF = re.compile(
    r"\bhref\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.IGNORECASE,
)


@event_priority(-200)
def on_post_page(salida, **argumentos):
    """Evita que el filtro de Material relativice los metadatos hreflang."""
    pagina = argumentos["page"]
    configuracion = argumentos["config"]
    url_sitio = configuracion.site_url
    if not url_sitio:
        return salida
    archivos_alternativos = getattr(pagina.file, "alternates", {})
    enlaces = {
        idioma: urljoin(url_sitio, archivo.url)
        for idioma, archivo in archivos_alternativos.items()
    }

    def reemplazar(coincidencia):
        etiqueta = coincidencia.group(0)
        if not PATRON_REL_ALTERNATIVO.search(etiqueta):
            return etiqueta
        coincidencia_idioma = PATRON_IDIOMA.search(etiqueta)
        if coincidencia_idioma is None:
            return etiqueta
        idioma = next(
            valor for valor in coincidencia_idioma.groupdict().values() if valor
        )
        enlace = enlaces.get(idioma)
        if enlace is None:
            return etiqueta
        return PATRON_HREF.sub(
            f'href="{enlace}"',
            etiqueta,
            count=1,
        )

    return PATRON_ETIQUETA_LINK.sub(reemplazar, salida)
