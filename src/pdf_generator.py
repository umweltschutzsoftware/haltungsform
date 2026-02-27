"""PDF-Erzeugung mit xhtml2pdf."""

import base64
import io
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from src import static_texts as texts
from src.models import AMPEL_DISPLAY, AmpelColor, FarmProject

# Pfade
_BASE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _BASE_DIR / "templates"
_ASSETS_DIR = _BASE_DIR / "assets"


def _load_logo_b64() -> str:
    """Lädt das Firmenlogo als Base64-String."""
    logo_path = _ASSETS_DIR / "logo.png"
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _ampel_class(color_value: str) -> str:
    """Gibt die CSS-Klasse für eine Ampelfarbe zurück.

    Akzeptiert AmpelColor-Werte ('green', 'yellow', 'red')
    oder den Sonderfall 'Kein Einfluss'.
    """
    if color_value == "Kein Einfluss":
        return ""
    try:
        color = AmpelColor(color_value)
        return AMPEL_DISPLAY[color]["css_class"]
    except (ValueError, KeyError):
        return ""


def _render_pdf(project: FarmProject, template_name: str) -> bytes:
    """Interne Hilfsfunktion: Rendert ein Template und erzeugt ein PDF."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
    )
    env.globals["ampel_class"] = _ampel_class

    template = env.get_template(template_name)

    css_path = _TEMPLATES_DIR / "style.css"
    css_content = css_path.read_text(encoding="utf-8")

    logo_b64 = _load_logo_b64()
    logo_uri = f"data:image/png;base64,{logo_b64}"

    datum = date.today().strftime("%d.%m.%Y")

    html_content = template.render(
        css=css_content,
        logo_uri=logo_uri,
        project=project,
        texts=texts,
        datum=datum,
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,
        dest=pdf_buffer,
        encoding="utf-8",
    )

    if pisa_status.err:
        raise RuntimeError(f"PDF-Erzeugung fehlgeschlagen: {pisa_status.err} Fehler")

    pdf_buffer.seek(0)
    return pdf_buffer.read()


def generate_pdf(project: FarmProject) -> bytes:
    """Erzeugt den vollständigen PDF-Report für ein Projekt.

    Args:
        project: Das vollständige Projektdatenmodell.

    Returns:
        Die PDF-Datei als Bytes.
    """
    return _render_pdf(project, "report.html")


def generate_pdf_kurz(project: FarmProject) -> bytes:
    """Erzeugt den Kurzreport (max. 3 Seiten) für ein Projekt.

    Enthält: Deckblatt, Tierzahlen mit Ampelbewertung, Zusammenfassung und
    nächste Schritte.

    Args:
        project: Das vollständige Projektdatenmodell.

    Returns:
        Die PDF-Datei als Bytes.
    """
    return _render_pdf(project, "report_kurz.html")
