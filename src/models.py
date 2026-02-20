"""Datenmodelle für die Haltungsform-Vorabschätzung."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AmpelColor(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


AMPEL_DISPLAY = {
    AmpelColor.GREEN: {
        "hex": "#34C759",
        "bg": "rgba(52,199,89,0.3)",
        "label": "unbedenklich / gering",
        "css_class": "ampel-green",
    },
    AmpelColor.YELLOW: {
        "hex": "#FFCC00",
        "bg": "rgba(255,204,0,0.3)",
        "label": "relevant / vertiefend",
        "css_class": "ampel-yellow",
    },
    AmpelColor.RED: {
        "hex": "#FF3B30",
        "bg": "rgba(255,59,48,0.3)",
        "label": "kritisch / erheblich",
        "css_class": "ampel-red",
    },
}

AMPEL_LABELS = {
    "Grün": AmpelColor.GREEN,
    "Gelb": AmpelColor.YELLOW,
    "Rot": AmpelColor.RED,
}

PRUEFUNG_OPTIONS = [
    "Ja",
    "Nein",
    "Voraussichtlich Nein",
    "Eher nein",
    "Eher ja",
]

AUSFUEHRUNG_OPTIONS = [
    "1 - Zwangsbelüfteter Stall",
    "2 - Zwangsbelüfteter Stall mit Auslauf",
    "3 - Außenklimastall",
    "4 - Außenklimastall mit Auslauf",
]

TIERART_OPTIONS_IST = [
    "Mastschweine",
    "Ferkelaufzucht",
    "Sauen/Eber",
    "Sauen mit Ferkel bis 10kg",
    "Jungsauen",
    "Kälber",
    "Färsen",
    "Milchkühe",
    "Bullen",
    "Hühnchen",
    "Legehennen",
    "Neu",
]

TIERART_OPTIONS_ZIEL = [
    "Mastschweine",
    "Ferkelaufzucht",
    "Sauen/Eber",
    "Sauen mit Ferkel bis 10kg",
    "Jungsauen",
    "Kälber",
    "Färsen",
    "Milchkühe",
    "Bullen",
    "Hühnchen",
    "Legehennen",
    "Keine",
]


class Assessment(BaseModel):
    aufwand: AmpelColor = AmpelColor.GREEN
    schwierigkeit: str = "green"  # AmpelColor value or "Kein Einfluss"
    begruendung_aufwand: str = ""
    begruendung_schwierigkeit: str = ""


class IstZustandRow(BaseModel):
    be_nr: str = ""
    tierart: str = "Mastschweine"
    tierplaetze: int = 0
    ausfuehrung: str = "1 - Zwangsbelüfteter Stall"
    kamine: str = "Ja"
    stand_der_technik: str = "Nein"


class PlanZustandRow(BaseModel):
    be_nr: str = ""
    tierart: str = "Mastschweine"
    tierplaetze: int = 0
    ausfuehrung: str = "1 - Zwangsbelüfteter Stall"


class Pruefungserfordernis(BaseModel):
    geruchshaeufigkeiten: str = "Ja"
    stickstoffdeposition: str = "Ja"
    ausbreitung_ist: str = "Ja"
    ausbreitung_plan: str = "Ja"
    ausbreitung_gesamt: str = "Ja"
    minderungsmassnahmen: str = "Nein"


class FarmProject(BaseModel):
    # Betriebsdaten
    strasse: str = ""
    hausnummer: str = ""
    plz: str = ""
    ort: str = ""
    projektnummer: str = ""

    # Freitexte
    genehmigung_text: str = ""
    standort_text: str = ""
    zusammenfassung_text: str = ""

    # Bewertungen
    genehmigung: Assessment = Assessment(schwierigkeit="Kein Einfluss")
    immissionsorte: Assessment = Assessment()
    nachbarbetriebe: Assessment = Assessment()
    ist_plan: Assessment = Assessment()

    # Stallanlagen
    ist_zustand: list[IstZustandRow] = []
    plan_zustand: list[PlanZustandRow] = []

    # Prüfungserfordernis
    pruefung: Pruefungserfordernis = Pruefungserfordernis()

    # Lageplan-Bild (Base64)
    lageplan_b64: Optional[str] = None

    @property
    def adresse_einzeilig(self) -> str:
        return f"{self.strasse} {self.hausnummer}, {self.plz} {self.ort}"
