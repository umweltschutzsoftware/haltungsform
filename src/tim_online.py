"""Tim-Online NRW URL-Generator.

Erzeugt eine vorkonfigurierte Tim-Online URL für einen Projektstandort.
Geocodiert die Adresse über Nominatim (OpenStreetMap) und transformiert
die Koordinaten von WGS84 (EPSG:4326) nach ETRS89/UTM Zone 32N (EPSG:25832).
"""

from urllib.parse import quote

from geopy.geocoders import Nominatim
from pyproj import Transformer

# Transformer wird einmalig erstellt (Thread-safe, wiederverwendbar)
_transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=False)


def build_tim_online_url(
    strasse: str,
    hausnummer: str,
    plz: str,
    ort: str,
    scale: int = 2047,
) -> str | None:
    """Erzeugt eine Tim-Online NRW URL für die gegebene Adresse.

    Args:
        strasse: Straßenname
        hausnummer: Hausnummer
        plz: Postleitzahl
        ort: Ortsname
        scale: Kartenmaßstab (Standard: 2047)

    Returns:
        Die Tim-Online URL oder None falls Geocoding fehlschlägt.
    """
    if not strasse or not ort:
        return None

    geolocator = Nominatim(user_agent="haltungsform-vorabschaetzung")

    try:
        location = geolocator.geocode(
            query={
                "street": f"{hausnummer} {strasse}".strip(),
                "postalcode": plz,
                "city": ort,
                "country": "Germany",
            },
            exactly_one=True,
            timeout=10,
        )
    except Exception:
        return None

    if location is None:
        return None

    # WGS84 (lat, lon) -> ETRS89/UTM32N (easting, northing)
    easting, northing = _transformer.transform(location.latitude, location.longitude)
    easting = int(round(easting))
    northing = int(round(northing))

    # Adresstext für Tim-Online
    address_text = f"{strasse} {hausnummer}\n{plz} {ort}"
    encoded_text = quote(address_text, safe="")

    return (
        f"https://www.tim-online.nrw.de/tim-online2/"
        f"?bg=basemapDE"
        f"&text={encoded_text}"
        f"&scale={scale}"
        f"&center={easting},{northing}"
        f"&icon=true"
    )
