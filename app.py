"""Streamlit-Webplattform für die Haltungsform-Vorabschätzung."""

import base64

import pandas as pd
import streamlit as st

from src.models import (
    AMPEL_DISPLAY,
    AMPEL_LABELS,
    AUSFUEHRUNG_OPTIONS,
    PRUEFUNG_OPTIONS,
    TIERART_OPTIONS_IST,
    TIERART_OPTIONS_ZIEL,
    AmpelColor,
    Assessment,
    FarmProject,
    IstZustandRow,
    PlanZustandRow,
    Pruefungserfordernis,
)
from src.pdf_generator import generate_pdf
from src.tim_online import build_tim_online_url
from src.xlsx_parser import parse_xlsx

st.set_page_config(
    page_title="Vorabschätzung Haltungsform",
    page_icon="\U0001F3E0",
    layout="wide",
)

st.title("Immissionsschutztechnische Vorabschätzung")
st.caption("Änderung der Haltungsform in der Schweinemast")


# ── Session State initialisieren ──
def _init_state():
    defaults = {
        "strasse": "",
        "hausnummer": "",
        "plz": "",
        "ort": "",
        "projektnummer": "",
        "genehmigung_text": "",
        "standort_text": "",
        "zusammenfassung_text": "",
        "lageplan_bytes": None,
        # Ampel-Bewertungen (Index in AMPEL_LABELS keys)
        "gen_aufwand": "Grün",
        "gen_begr_aufwand": "",
        "imm_aufwand": "Grün",
        "imm_schwierigkeit": "Grün",
        "imm_begr_aufwand": "",
        "imm_begr_schwierigkeit": "",
        "nach_aufwand": "Grün",
        "nach_schwierigkeit": "Grün",
        "nach_begr_aufwand": "",
        "nach_begr_schwierigkeit": "",
        "ip_aufwand": "Grün",
        "ip_schwierigkeit": "Grün",
        "ip_begr_aufwand": "",
        "ip_begr_schwierigkeit": "",
        # Prüfungserfordernis
        "pruef_geruch": "Ja",
        "pruef_stickstoff": "Ja",
        "pruef_ist": "Ja",
        "pruef_plan": "Ja",
        "pruef_gesamt": "Ja",
        "pruef_minderung": "Nein",
        # Dataframes für Ist/Plan-Zustand
        "ist_df": pd.DataFrame(columns=[
            "BE-Nr.", "Tierart", "Tierplätze", "Ausführung", "Kamine", "S.d.T."
        ]),
        "plan_df": pd.DataFrame(columns=[
            "BE-Nr.", "Tierart", "Tierplätze", "Ausführung"
        ]),
        "xlsx_parsed": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_state()

# ── Tabs ──
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Betriebsdaten",
    "2. Stallanlagen",
    "3. Bewertungen",
    "4. Zusammenfassung",
    "5. PDF erstellen",
])


# ════════════════════════════════════════
# TAB 1: Betriebsdaten
# ════════════════════════════════════════
with tab1:
    st.header("Betriebsdaten")

    # XLSX-Upload
    uploaded_file = st.file_uploader(
        "XLSX-Datei von profarm hochladen",
        type=["xlsx"],
        key="xlsx_upload",
    )

    if uploaded_file is not None and not st.session_state.xlsx_parsed:
        with st.spinner("XLSX wird gelesen..."):
            try:
                data = parse_xlsx(uploaded_file.getvalue())
                # Widget-Keys direkt setzen, damit st.text_input die Werte übernimmt
                st.session_state.inp_strasse = data["strasse"]
                st.session_state.inp_hausnummer = data["hausnummer"]
                st.session_state.inp_plz = data["plz"]
                st.session_state.inp_ort = data["ort"]
                st.session_state.inp_projektnummer = data["projektnummer"]

                # Auch die allgemeinen Keys setzen (für andere Tabs)
                st.session_state.strasse = data["strasse"]
                st.session_state.hausnummer = data["hausnummer"]
                st.session_state.plz = data["plz"]
                st.session_state.ort = data["ort"]
                st.session_state.projektnummer = data["projektnummer"]

                # Ist-Zustand DataFrame
                if data["ist_zustand"]:
                    ist_rows = []
                    for r in data["ist_zustand"]:
                        ist_rows.append({
                            "BE-Nr.": r.be_nr,
                            "Tierart": r.tierart,
                            "Tierplätze": r.tierplaetze,
                            "Ausführung": r.ausfuehrung,
                            "Kamine": r.kamine,
                            "S.d.T.": r.stand_der_technik,
                        })
                    st.session_state.ist_df = pd.DataFrame(ist_rows)

                # Plan-Zustand DataFrame
                if data["plan_zustand"]:
                    plan_rows = []
                    for r in data["plan_zustand"]:
                        plan_rows.append({
                            "BE-Nr.": r.be_nr,
                            "Tierart": r.tierart,
                            "Tierplätze": r.tierplaetze,
                            "Ausführung": r.ausfuehrung,
                        })
                    st.session_state.plan_df = pd.DataFrame(plan_rows)

                st.session_state.xlsx_parsed = True
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Einlesen der XLSX-Datei: {e}")

    # Formularfelder – Widget-Key ist die primäre Datenquelle
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.strasse = st.text_input("Straße", value=st.session_state.strasse, key="inp_strasse")
        st.session_state.plz = st.text_input("PLZ", value=st.session_state.plz, key="inp_plz")
        st.session_state.projektnummer = st.text_input("Projektnummer", value=st.session_state.projektnummer, key="inp_projektnummer")
    with col2:
        st.session_state.hausnummer = st.text_input("Hausnummer", value=st.session_state.hausnummer, key="inp_hausnummer")
        st.session_state.ort = st.text_input("Ort", value=st.session_state.ort, key="inp_ort")

    # Lageplan-Upload
    st.subheader("Lageplan")
    lageplan_file = st.file_uploader(
        "Lageplan-Bild hochladen (PNG/JPG)",
        type=["png", "jpg", "jpeg"],
        key="lageplan_upload",
    )
    if lageplan_file is not None:
        st.session_state.lageplan_bytes = lageplan_file.getvalue()
        st.image(st.session_state.lageplan_bytes, caption="Lageplan", use_container_width=True)


# ════════════════════════════════════════
# TAB 2: Stallanlagen
# ════════════════════════════════════════
with tab2:
    st.header("Stallanlagen")

    # Ist-Zustand
    st.subheader("Ist-Zustand der Tierhaltung")

    ist_config = {
        "BE-Nr.": st.column_config.TextColumn("BE-Nr."),
        "Tierart": st.column_config.SelectboxColumn("Tierart", options=TIERART_OPTIONS_IST),
        "Tierplätze": st.column_config.NumberColumn("Tierplätze", min_value=0, step=1),
        "Ausführung": st.column_config.SelectboxColumn("Ausführung", options=AUSFUEHRUNG_OPTIONS),
        "Kamine": st.column_config.SelectboxColumn("Kamine", options=["Ja", "Nein"]),
        "S.d.T.": st.column_config.SelectboxColumn("S.d.T.", options=["Ja", "Nein"]),
    }

    edited_ist = st.data_editor(
        st.session_state.ist_df,
        column_config=ist_config,
        num_rows="dynamic",
        use_container_width=True,
        key="ist_editor",
    )
    st.session_state.ist_df = edited_ist

    st.divider()

    # Plan-Zustand
    st.subheader("Plan-Zustand der Tierhaltung")

    plan_config = {
        "BE-Nr.": st.column_config.TextColumn("BE-Nr."),
        "Tierart": st.column_config.SelectboxColumn("Tierart", options=TIERART_OPTIONS_ZIEL),
        "Tierplätze": st.column_config.NumberColumn("Tierplätze", min_value=0, step=1),
        "Ausführung": st.column_config.SelectboxColumn("Ausführung", options=AUSFUEHRUNG_OPTIONS),
    }

    edited_plan = st.data_editor(
        st.session_state.plan_df,
        column_config=plan_config,
        num_rows="dynamic",
        use_container_width=True,
        key="plan_editor",
    )
    st.session_state.plan_df = edited_plan


# ════════════════════════════════════════
# TAB 3: Bewertungen
# ════════════════════════════════════════
with tab3:
    st.header("Bewertungen")

    # Tim-Online Link
    if st.session_state.strasse and st.session_state.ort:
        with st.spinner("Standort wird ermittelt..."):
            tim_url = build_tim_online_url(
                strasse=st.session_state.strasse,
                hausnummer=st.session_state.hausnummer,
                plz=st.session_state.plz,
                ort=st.session_state.ort,
            )
        if tim_url:
            st.link_button(
                "Standort in Tim-Online anzeigen",
                tim_url,
                type="primary",
            )
        else:
            st.warning("Standort konnte nicht geocodiert werden. Bitte Adresse prüfen.")
    else:
        st.info("Bitte zuerst Adresse in Tab 1 eingeben, um den Tim-Online-Link zu generieren.")

    st.divider()

    ampel_options = list(AMPEL_LABELS.keys())

    def _ampel_colored_label(label: str) -> str:
        """Hilfsfunktion für farbige Anzeige."""
        color_map = {"Grün": "\U0001F7E2", "Gelb": "\U0001F7E1", "Rot": "\U0001F534"}
        return f"{color_map.get(label, '')} {label}"

    # ── 1. Genehmigungsrecht ──
    st.subheader("1. Genehmigungsrechtliche Einordnung")
    st.session_state.genehmigung_text = st.text_area(
        "Beschreibung des Vorhabens (Genehmigungsrecht)",
        value=st.session_state.genehmigung_text,
        height=100,
        key="gen_text",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.gen_aufwand = st.selectbox(
            "Aufwand", ampel_options,
            index=ampel_options.index(st.session_state.gen_aufwand),
            key="gen_aufwand_sel",
        )
        if st.session_state.gen_aufwand != "Grün":
            st.session_state.gen_begr_aufwand = st.text_input(
                "Begründung Aufwand",
                value=st.session_state.gen_begr_aufwand,
                key="gen_begr_a",
            )
    with col2:
        st.text("Schwierigkeit: Kein Einfluss")
        st.caption("Bei der genehmigungsrechtlichen Einordnung hat die Schwierigkeit keinen Einfluss.")

    st.divider()

    # ── 2. Immissionsorte ──
    st.subheader("2. Immissionsorte")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.imm_aufwand = st.selectbox(
            "Aufwand", ampel_options,
            index=ampel_options.index(st.session_state.imm_aufwand),
            key="imm_aufwand_sel",
        )
        if st.session_state.imm_aufwand != "Grün":
            st.session_state.imm_begr_aufwand = st.text_input(
                "Begründung Aufwand",
                value=st.session_state.imm_begr_aufwand,
                key="imm_begr_a",
            )
    with col2:
        st.session_state.imm_schwierigkeit = st.selectbox(
            "Schwierigkeit", ampel_options,
            index=ampel_options.index(st.session_state.imm_schwierigkeit),
            key="imm_schwierigkeit_sel",
        )
        if st.session_state.imm_schwierigkeit != "Grün":
            st.session_state.imm_begr_schwierigkeit = st.text_input(
                "Begründung Schwierigkeit",
                value=st.session_state.imm_begr_schwierigkeit,
                key="imm_begr_s",
            )

    st.divider()

    # ── 3. Nachbarbetriebe ──
    st.subheader("3. Nachbarbetriebe")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.nach_aufwand = st.selectbox(
            "Aufwand", ampel_options,
            index=ampel_options.index(st.session_state.nach_aufwand),
            key="nach_aufwand_sel",
        )
        if st.session_state.nach_aufwand != "Grün":
            st.session_state.nach_begr_aufwand = st.text_input(
                "Begründung Aufwand",
                value=st.session_state.nach_begr_aufwand,
                key="nach_begr_a",
            )
    with col2:
        st.session_state.nach_schwierigkeit = st.selectbox(
            "Schwierigkeit", ampel_options,
            index=ampel_options.index(st.session_state.nach_schwierigkeit),
            key="nach_schwierigkeit_sel",
        )
        if st.session_state.nach_schwierigkeit != "Grün":
            st.session_state.nach_begr_schwierigkeit = st.text_input(
                "Begründung Schwierigkeit",
                value=st.session_state.nach_begr_schwierigkeit,
                key="nach_begr_s",
            )

    st.divider()

    # ── 4. Ist- und Plan-Zustand ──
    st.subheader("4. Ist- und Plan-Zustand")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.ip_aufwand = st.selectbox(
            "Aufwand", ampel_options,
            index=ampel_options.index(st.session_state.ip_aufwand),
            key="ip_aufwand_sel",
        )
        if st.session_state.ip_aufwand != "Grün":
            st.session_state.ip_begr_aufwand = st.text_input(
                "Begründung Aufwand",
                value=st.session_state.ip_begr_aufwand,
                key="ip_begr_a",
            )
    with col2:
        st.session_state.ip_schwierigkeit = st.selectbox(
            "Schwierigkeit", ampel_options,
            index=ampel_options.index(st.session_state.ip_schwierigkeit),
            key="ip_schwierigkeit_sel",
        )
        if st.session_state.ip_schwierigkeit != "Grün":
            st.session_state.ip_begr_schwierigkeit = st.text_input(
                "Begründung Schwierigkeit",
                value=st.session_state.ip_begr_schwierigkeit,
                key="ip_begr_s",
            )


# ════════════════════════════════════════
# TAB 4: Zusammenfassung
# ════════════════════════════════════════
with tab4:
    st.header("Zusammenfassung & Prüfungserfordernis")

    st.session_state.zusammenfassung_text = st.text_area(
        "Zusammenfassungstext",
        value=st.session_state.zusammenfassung_text,
        height=150,
        key="zusammenfassung_input",
    )

    st.subheader("Ampel-Übersicht")

    def _ampel_html(label: str) -> str:
        """Erzeugt HTML für farbige Ampelzelle."""
        color = AMPEL_LABELS[label]
        bg = AMPEL_DISPLAY[color]["bg"]
        return f'<td style="background-color: {bg}; text-align: center; padding: 8px;">&nbsp;</td>'

    def _schwierigkeit_html(label: str, is_kein_einfluss: bool = False) -> str:
        if is_kein_einfluss:
            return '<td style="text-align: center; padding: 8px;">Kein Einfluss</td>'
        return _ampel_html(label)

    overview_html = f"""
    <table style="width:100%; border-collapse:collapse; font-family:sans-serif; font-size:14px;">
        <tr style="background:#f0f0f0;">
            <th style="border:1px solid #ccc; padding:8px; text-align:left;">Thema</th>
            <th style="border:1px solid #ccc; padding:8px; text-align:center;">Aufwand</th>
            <th style="border:1px solid #ccc; padding:8px; text-align:center;">Schwierigkeit</th>
        </tr>
        <tr>
            <td style="border:1px solid #ccc; padding:8px;">Genehmigungsrecht</td>
            {_ampel_html(st.session_state.gen_aufwand)}
            {_schwierigkeit_html("", is_kein_einfluss=True)}
        </tr>
        <tr>
            <td style="border:1px solid #ccc; padding:8px;">Immissionsorte</td>
            {_ampel_html(st.session_state.imm_aufwand)}
            {_schwierigkeit_html(st.session_state.imm_schwierigkeit)}
        </tr>
        <tr>
            <td style="border:1px solid #ccc; padding:8px;">Nachbarbetriebe</td>
            {_ampel_html(st.session_state.nach_aufwand)}
            {_schwierigkeit_html(st.session_state.nach_schwierigkeit)}
        </tr>
        <tr>
            <td style="border:1px solid #ccc; padding:8px;">Ist- und Plan-Zustand</td>
            {_ampel_html(st.session_state.ip_aufwand)}
            {_schwierigkeit_html(st.session_state.ip_schwierigkeit)}
        </tr>
    </table>
    """
    st.markdown(overview_html, unsafe_allow_html=True)

    st.divider()

    # Prüfungserfordernis
    st.subheader("Prüfungserfordernis")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.pruef_geruch = st.selectbox(
            "Ermittlung der Geruchshäufigkeiten", PRUEFUNG_OPTIONS,
            index=PRUEFUNG_OPTIONS.index(st.session_state.pruef_geruch),
            key="pruef_geruch_sel",
        )
        st.session_state.pruef_ist = st.selectbox(
            "Ausbreitungsberechnung Ist-Zustand", PRUEFUNG_OPTIONS,
            index=PRUEFUNG_OPTIONS.index(st.session_state.pruef_ist),
            key="pruef_ist_sel",
        )
        st.session_state.pruef_gesamt = st.selectbox(
            "Ausbreitungsberechnung Gesamtbelastung", PRUEFUNG_OPTIONS,
            index=PRUEFUNG_OPTIONS.index(st.session_state.pruef_gesamt),
            key="pruef_gesamt_sel",
        )
    with col2:
        st.session_state.pruef_stickstoff = st.selectbox(
            "Ermittlung der Stickstoffdeposition", PRUEFUNG_OPTIONS,
            index=PRUEFUNG_OPTIONS.index(st.session_state.pruef_stickstoff),
            key="pruef_stickstoff_sel",
        )
        st.session_state.pruef_plan = st.selectbox(
            "Ausbreitungsberechnung Plan-Zustand", PRUEFUNG_OPTIONS,
            index=PRUEFUNG_OPTIONS.index(st.session_state.pruef_plan),
            key="pruef_plan_sel",
        )
        st.session_state.pruef_minderung = st.selectbox(
            "Konditionierung von Minderungsmaßnahmen", PRUEFUNG_OPTIONS,
            index=PRUEFUNG_OPTIONS.index(st.session_state.pruef_minderung),
            key="pruef_minderung_sel",
        )


# ════════════════════════════════════════
# TAB 5: PDF erstellen
# ════════════════════════════════════════
with tab5:
    st.header("PDF erstellen")

    st.subheader("Vorschau der Eingaben")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Projektnummer:** {st.session_state.projektnummer}")
        st.markdown(f"**Adresse:** {st.session_state.strasse} {st.session_state.hausnummer}")
        st.markdown(f"**Ort:** {st.session_state.plz} {st.session_state.ort}")
    with col2:
        ist_count = len(st.session_state.ist_df)
        plan_count = len(st.session_state.plan_df)
        st.markdown(f"**Ist-Zustand:** {ist_count} Betriebseinheit(en)")
        st.markdown(f"**Plan-Zustand:** {plan_count} Betriebseinheit(en)")

    st.divider()

    if st.button("PDF erstellen", type="primary", use_container_width=True):
        with st.spinner("PDF wird erzeugt..."):
            try:
                # Daten zusammenbauen
                ist_rows = []
                for _, row in st.session_state.ist_df.iterrows():
                    ist_rows.append(IstZustandRow(
                        be_nr=str(row.get("BE-Nr.", "")),
                        tierart=str(row.get("Tierart", "Mastschweine")),
                        tierplaetze=int(row.get("Tierplätze", 0)) if pd.notna(row.get("Tierplätze")) else 0,
                        ausfuehrung=str(row.get("Ausführung", "1 - Zwangsbelüfteter Stall")),
                        kamine=str(row.get("Kamine", "Nein")),
                        stand_der_technik=str(row.get("S.d.T.", "Nein")),
                    ))

                plan_rows = []
                for _, row in st.session_state.plan_df.iterrows():
                    plan_rows.append(PlanZustandRow(
                        be_nr=str(row.get("BE-Nr.", "")),
                        tierart=str(row.get("Tierart", "Mastschweine")),
                        tierplaetze=int(row.get("Tierplätze", 0)) if pd.notna(row.get("Tierplätze")) else 0,
                        ausfuehrung=str(row.get("Ausführung", "1 - Zwangsbelüfteter Stall")),
                    ))

                # Lageplan
                lageplan_b64 = None
                if st.session_state.lageplan_bytes:
                    lageplan_b64 = base64.b64encode(st.session_state.lageplan_bytes).decode()

                project = FarmProject(
                    strasse=st.session_state.strasse,
                    hausnummer=st.session_state.hausnummer,
                    plz=st.session_state.plz,
                    ort=st.session_state.ort,
                    projektnummer=st.session_state.projektnummer,
                    genehmigung_text=st.session_state.genehmigung_text,
                    standort_text=st.session_state.standort_text,
                    zusammenfassung_text=st.session_state.zusammenfassung_text,
                    genehmigung=Assessment(
                        aufwand=AMPEL_LABELS[st.session_state.gen_aufwand],
                        schwierigkeit="Kein Einfluss",
                        begruendung_aufwand=st.session_state.gen_begr_aufwand,
                    ),
                    immissionsorte=Assessment(
                        aufwand=AMPEL_LABELS[st.session_state.imm_aufwand],
                        schwierigkeit=AMPEL_LABELS[st.session_state.imm_schwierigkeit].value,
                        begruendung_aufwand=st.session_state.imm_begr_aufwand,
                        begruendung_schwierigkeit=st.session_state.imm_begr_schwierigkeit,
                    ),
                    nachbarbetriebe=Assessment(
                        aufwand=AMPEL_LABELS[st.session_state.nach_aufwand],
                        schwierigkeit=AMPEL_LABELS[st.session_state.nach_schwierigkeit].value,
                        begruendung_aufwand=st.session_state.nach_begr_aufwand,
                        begruendung_schwierigkeit=st.session_state.nach_begr_schwierigkeit,
                    ),
                    ist_plan=Assessment(
                        aufwand=AMPEL_LABELS[st.session_state.ip_aufwand],
                        schwierigkeit=AMPEL_LABELS[st.session_state.ip_schwierigkeit].value,
                        begruendung_aufwand=st.session_state.ip_begr_aufwand,
                        begruendung_schwierigkeit=st.session_state.ip_begr_schwierigkeit,
                    ),
                    ist_zustand=ist_rows,
                    plan_zustand=plan_rows,
                    pruefung=Pruefungserfordernis(
                        geruchshaeufigkeiten=st.session_state.pruef_geruch,
                        stickstoffdeposition=st.session_state.pruef_stickstoff,
                        ausbreitung_ist=st.session_state.pruef_ist,
                        ausbreitung_plan=st.session_state.pruef_plan,
                        ausbreitung_gesamt=st.session_state.pruef_gesamt,
                        minderungsmassnahmen=st.session_state.pruef_minderung,
                    ),
                    lageplan_b64=lageplan_b64,
                )

                pdf_bytes = generate_pdf(project)

                # Dateiname
                pnr = st.session_state.projektnummer or "ENTWURF"
                filename = f"Vorabschätzung-{pnr}.pdf"

                st.download_button(
                    label=f"PDF herunterladen ({filename})",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
                st.success("PDF erfolgreich erstellt!")

            except Exception as e:
                st.error(f"Fehler bei der PDF-Erzeugung: {e}")
                st.exception(e)
