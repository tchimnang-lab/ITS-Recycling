import streamlit as st
import random
import pandas as pd
import requests
from enum import Enum
from typing import List, Dict
from collections import defaultdict

# Define WasteType Enum
class WasteType(Enum):
    PLASTIK = "Plastik"
    PAPIER = "Papier"
    BIOLOGISCH = "Biologisch"
    SONSTIGE = "Sonstige"
    GIFTIG = "GIFTIG"

# Define WasteItem Class
class WasteItem:
    def __init__(self, name: str, waste_types: List[WasteType], difficulty: int, image_url: str):
        self.name = name
        self.waste_types = waste_types
        self.difficulty = difficulty
        self.image_url = image_url

    def __str__(self):
        waste_types_str = ', '.join(w.value for w in self.waste_types)
        return f"{self.name} ({self.difficulty}) ({waste_types_str}) - Image: {self.image_url}"

# Define StudentModel Class
class StudentModel:
    def __init__(self):
        self.current_difficulty = 1

    def getAttribute(self, waste_items):
        items_filtered_by_difficulty = [item for item in waste_items if item.difficulty <= self.current_difficulty]
        self.aktuelles_item_index = random.randint(0, len(items_filtered_by_difficulty) - 1)
        return items_filtered_by_difficulty[self.aktuelles_item_index]

    def getAdditionalInformation(self, item: WasteItem, userItems: str):
        url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
        token = "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"
        query = f"Verdeutliche, dass {item.name} in die folgenden Müllkategorie(n) geworfen werden muss: {', '.join([w.value for w in item.waste_types])}? Der Nutzer hat sich für die falsche Müllart entschieden: {userItems}"
        return self.llm(query, token, url)

    def llm(self, query, token, url):
        parameters = {
            "max_new_tokens": 500,
            "temperature": 0.8,
            "top_k": 50,
            "top_p": 0.95,
            "return_full_text": False
        }
        prompt = f"""
Du bist ein Experte für Mülltrennung und erklärst, warum ein bestimmtes Produkt korrekt entsorgt werden sollte und es nicht in die vom Nutzer angegebene Kategorie gehört.  
Gib eine Begründung, warum es den bestimmten Müllkategorie zugeordnet wird, die zur Verdeutlichung genannt wurde.  
Verdeutliche dies mit einem Beispiel, warum die vom Nutzer gewählte Kategorie falsch ist.  
Antwort in maximal 500 Zeichen und ausschließlich auf Deutsch. 

Die Query:

{query}
"""
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        payload = {"inputs": prompt, "parameters": parameters}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].strip()
        else:
            return f"Error: {response.status_code}, unable to fetch the explanation."

    def getFeedback(self, item: WasteItem, correct: bool, user_input: list):
        if correct:
            self.current_difficulty = min(self.current_difficulty + 1, 3)
            return "Gut gemacht! Du kannst die richtige Tonne wählen!"
        else:
            self.current_difficulty = max(self.current_difficulty - 1, 1)
            waste_type_str = ', '.join(w.value for w in item.waste_types)
            user_type_str = ', '.join(w for w in user_input)
            return f"Das passt aber nicht so gut! Tipp: {item.name} ist ein Produkt, das aufgrund der Aufbereitung den folgenden Tonnen zugeordnet wird: {waste_type_str}.\n\n{self.getAdditionalInformation(item=item, userItems=user_type_str)}"

# Define DidacticModel Class
class DidacticModel:
    def __init__(self, uebungen):
        self.sessions = [
            {"title": "Grundlagen des Recyclings", "content": "Recycling ist der Prozess der Umwandlung von Abfallstoffen in neue Materialien und Gegenstände. Es trägt dazu bei, den Verbrauch frischer Rohstoffe zu reduzieren, den Energieverbrauch zu senken und die Umweltverschmutzung zu verringern."},
            {"title": "Recycling Kategorien", "content": "Es gibt verschiedene Recyclingkategorien: Gelber Sack (Kunststoff- und Metallverpackungen), Restmüll (nicht wiederverwertbarer Abfall), Papiertonne (Papier und Pappe), Sondermüll (gefährlicher Abfall) und Biomüll (organischer Abfall)."},
            {"title": "Spezielle Kategorien", "content": "Zu den Sonderkategorien zählen Artikel wie Batterien, Elektronik und Gefahrenstoffe, die besondere Handhabungs- und Entsorgungsmethoden erfordern."}
        ]
        self.uebungen = uebungen
        
        if 'current_session' not in st.session_state:
            st.session_state.current_session = 0
        if 'current_exercise' not in st.session_state:
            st.session_state.current_exercise = 0
        if 'score' not in st.session_state:
            st.session_state.score = 0

    def show_session(self, session_index: int):
        session = self.sessions[session_index]
        st.write(f"## {session['title']}")
        st.write(session['content'])

    def show_exercise(self, exercise_index: int):
        exercise = self.uebungen[exercise_index]
        st.write(f"### {exercise['question']}")
        selected_option = st.radio("Choose an option:", exercise['options'])
        if st.button("Submit Answer"):
            if selected_option == exercise['answer']:
                st.success("Correct!")
                st.session_state.score += 1
            else:
                st.error("Incorrect.")
            st.session_state.current_exercise += 1
            st.rerun()

    def entrypoint(self):
        st.sidebar.title("Progress")
        st.sidebar.write(f"Session: {st.session_state.current_session}/{len(self.sessions)}")
        st.sidebar.write(f"Uebung: {st.session_state.current_exercise}/{len(self.uebungen)}")
        st.sidebar.write(f"Ergebnis: {st.session_state.score}")

        if st.session_state.current_session < len(self.sessions):
            self.show_session(st.session_state.current_session)
            if st.button("Naechste Seite"):
                st.session_state.current_session = st.session_state.current_session + 1 if st.session_state.current_session < 3 else st.session_state.current_session
                st.rerun()
        elif st.session_state.current_exercise < len(self.uebungen):
            self.show_exercise(st.session_state.current_exercise)
        else:
            st.write("### Herzlichen Glückwunsch! Du hast alle Sitzungen und Übungen abgeschlossen. Teste jetzt dein Wissen.")
            st.write(f"Dein Endergebnis ist: {st.session_state.score}/{len(self.uebungen)}")

# Define DomainModel Class
class DomainModel:
    def __init__(self, waste_items: List[WasteItem]):
        self.waste_items = waste_items

    def categorize_waste(self) -> Dict[str, List[str]]:
        waste_categories = defaultdict(list)
        category_mapping = {
            WasteType.PLASTIK: "Plastikmüll",
            WasteType.PAPIER: "Papiermüll",
            WasteType.BIOLOGISCH: "Biomüll",
            WasteType.SONSTIGE: "Restmüll",
            WasteType.GIFTIG: "Sondermüll"
        }
        for item in self.waste_items:
            for waste_type in item.waste_types:
                waste_categories[category_mapping[waste_type]].append(item.name)
        return dict(waste_categories)

# Define RecyclingSpiel Class
class RecyclingSpiel:
    def __init__(self, waste_items: List[WasteItem]):
        self.waste_items = waste_items
        self.spiel_zuruecksetzen()

    def spiel_zuruecksetzen(self):
        self.punktestand = 0
        self.gesamte_fragen = 0
        self.verlauf = []

    def antwort_bewerten(self, ausgewaehlte_kategorien, aktuellesItem):
        item_daten = self.waste_items[self.waste_items.index(aktuellesItem)]
        korrekte_kategorien = [wt.value for wt in item_daten.waste_types]
        ist_korrekt = set(ausgewaehlte_kategorien) == set(korrekte_kategorien)
        ergebnis = {
            "item": item_daten.name,
            "ausgewaehlt": ausgewaehlte_kategorien,
            "korrekt": korrekte_kategorien,
            "ist_korrekt": ist_korrekt,
            "schwierigkeit": item_daten.difficulty
        }
        self.verlauf.append(ergebnis)
        if ist_korrekt:
            self.punktestand += 1
        self.gesamte_fragen += 1
        return ergebnis

    def verlauf_anzeigen(self):
        return self.verlauf

# Define GameEnvironment Class
class GameEnvironment:
    def __init__(self, domain_model: DomainModel, didactic_model: DidacticModel, student_model: StudentModel):
        self.domain_model = domain_model
        self.didactic_model = didactic_model
        self.student_model = student_model

        # Initialize session state
        if "is_intro_completed" not in st.session_state:
            st.session_state.is_intro_completed = False
        if "recycling_spiel" not in st.session_state:
            st.session_state.recycling_spiel = RecyclingSpiel(domain_model.waste_items)
        if "student_model" not in st.session_state:
            st.session_state.student_model = self.student_model
        if "domain_model" not in st.session_state:
            st.session_state.domain_model = self.domain_model
        if "aktuelles_item" not in st.session_state:
            st.session_state.aktuelles_item = student_model.getAttribute(domain_model.waste_items)

        self.program_switcher()

    def program_switcher(self):
        # self.hauptprogramm()
        if st.session_state.is_intro_completed:
            self.hauptprogramm()
        else:
            self.introprogramm()

    def introprogramm(self):
        st.title("📘 Einführung in das Recycling")
        self.didactic_model.entrypoint()

        if st.session_state.current_session >= len(self.didactic_model.sessions) and st.session_state.current_exercise >= len(self.didactic_model.uebungen):
            if st.button("Zum Spiel wechseln"):
                st.session_state.is_intro_completed = True
                st.rerun()

    def hauptprogramm(self):
        st.set_page_config(page_title="Recycling Trainer", page_icon="♻️", layout="wide")

        spiel = st.session_state.recycling_spiel
        studentModel = st.session_state.student_model
        aktuelles_item = st.session_state.aktuelles_item
        domainModel = st.session_state.domain_model

        with st.sidebar:
            st.title("♻️ Recycling Pro")
            st.write("Meistere die Mülltrennung!")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Punktestand", f"{spiel.punktestand}/{spiel.gesamte_fragen}")
            with col2:
                genauigkeit = f"{spiel.punktestand/spiel.gesamte_fragen*100:.1f}%" if spiel.gesamte_fragen > 0 else "0%"
                st.metric("Genauigkeit", genauigkeit)

            if st.button("Spiel zurücksetzen"):
                spiel.spiel_zuruecksetzen()
                st.session_state.aktuelles_item = self.student_model.getAttribute(domainModel.waste_items)
                st.rerun()

        st.header("Mülltrennung lernen")

        col1, col2, col3 = st.columns([3, 5, 4])
        with col1:
            st.image(aktuelles_item.image_url, caption=aktuelles_item.name, use_container_width=True)
            st.write(f"**Schwierigkeit:** {'★' * aktuelles_item.difficulty}")

        with col2:
            st.write(f"### Sortiere: {st.session_state.aktuelles_item.name}")
            ausgewaehlte_kategorien = st.multiselect("Wähle Entsorgungskategorien:", [wt.value for wt in WasteType])

            if st.button("Entsorgung prüfen"):
                if not ausgewaehlte_kategorien:
                    st.warning("Bitte wähle mindestens eine Kategorie!")
                else:
                    ergebnis = spiel.antwort_bewerten(ausgewaehlte_kategorien, st.session_state.aktuelles_item)
                    if ergebnis['ist_korrekt']:
                        st.success(studentModel.getFeedback(st.session_state.aktuelles_item, True, ausgewaehlte_kategorien))
                        st.session_state.aktuelles_item = studentModel.getAttribute(domainModel.waste_items)
                    else:
                        st.error("Das ist leider falsch!")
                        with st.spinner("Weitere Infos werden geladen..."):
                            st.info(studentModel.getFeedback(st.session_state.aktuelles_item, False, ausgewaehlte_kategorien))
                        st.session_state.aktuelles_item = studentModel.getAttribute(domainModel.waste_items)
                    if st.button("Nächstes Bild"):
                        st.rerun()

        with col3:
            st.header("Verlauf der gewählten Items")
            verlauf = spiel.verlauf_anzeigen()
            if verlauf:
                verlauf_df = pd.DataFrame(verlauf)
                st.dataframe(verlauf_df)
            else:
                st.write("Noch keine Items gewählt.")

# Define Waste Items
waste_items = [
    WasteItem("Joghurtbecher", [WasteType.PLASTIK], 1, "https://www.verbraucherzentrale.nrw/sites/default/files/styles/gallery_slider_article_tablet/public/2018-12/joghurtbecher.jpg?h=0fa75c9b&itok=JSdWafj8"),
    WasteItem("Joghurtbecher mit Papier", [WasteType.PLASTIK, WasteType.PAPIER], 3, "https://www.der-reporter.de/i/fileadmin/user_upload/import/artikel/29/3729/193729_193729_Korrekte_Entsorgung_von_Verpackungen_Credit_Initiative-_Muelltrennung-wirkt.jpg?w=1024&_=1661848155"),
    WasteItem("Milchkarton", [WasteType.PLASTIK], 2, "https://images.noz-mhn.de/img/20141956/crop/cbase_4_3-w1200/2035156272/916945232/b7359aa0178a3589b8a5d101f96ad41f.jpg"),
    WasteItem("Aluminiumdose", [WasteType.PLASTIK], 3, "https://www.kibag-entsorgungstechnik.ch/files/entsorgungstechnik/bilder/rubrikbilder/kibag-entsorgung-alu-dose-recycling.jpg"),
    WasteItem("Papiertüte", [WasteType.PAPIER], 1, "https://img.freepik.com/fotos-premium/eine-zerknitterte-papiertuete-auf-weissem-hintergrund-gegenstand-von-muell_594847-3695.jpg"),
    WasteItem("Plastiktüte", [WasteType.PLASTIK], 1, "https://www.nabu.de/imperia/md/nabu/images/oekologisch-leben/ernaehrung-einkauf/fittosize_680_453_abe2ccaa2ac843407a9ca4d9d0344434_plastiktuete_nabu_s._hennigs__16_.jpeg"),
    WasteItem("Hybridverpackung (Papier/Plastik)", [WasteType.PAPIER, WasteType.PLASTIK], 3, "https://d569htemax5yg.cloudfront.net/catalog/product/P/2/P2G8307.jpg"),
    WasteItem("Apfelgriebs", [WasteType.BIOLOGISCH], 2, "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Apfelgriebsch.JPG/1200px-Apfelgriebsch.JPG"),
    WasteItem("E-Zigarette", [WasteType.GIFTIG], 2, "https://cdn03.plentymarkets.com/kku2l5dldin4/item/images/5860/full/5860-Elfbar-600-Einweg-E-Zigarette-Mad-Blue.jpg"),
    WasteItem("Caprisonne", [WasteType.PLASTIK, WasteType.SONSTIGE], 3, "https://i0.web.de/image/572/40095572,pd=1,f=sdata11/trinkpaeckchen-capri-sun-papierstrohhalm.jpg"),
    WasteItem("beschichteter Papierstrohalm", [WasteType.SONSTIGE], 1, "https://partyvikings.de/media/catalog/product/cache/a8a7725c9f67a2f4a037f0ab6a30a27c/p/a/paperstraws.jpeg")
]

# Define Intro Exercises
intro_exercises = [
    {"question": "Zu welcher Kategorie gehört eine Plastikflasche?", "options": ["Gelber Sack", "Restmüll", "Papiertonne", "Sondermüll", "Biomüll"], "answer": "Gelber Sack"},
    {"question": "Zu welcher Kategorie gehört ein öliger Pizzakarton?", "options": ["Gelber Sack", "Restmüll", "Papiertonne", "Sondermüll", "Biomüll"], "answer": "Restmüll"},
    {"question": "Zu welcher Kategorie gehört eine Zeitschrift?", "options": ["Gelber Sack", "Restmüll", "Papiertonne", "Sondermüll", "Biomüll"], "answer": "Papiertonne"}
]

# Initialize GameEnvironment
ge = GameEnvironment(
    domain_model=DomainModel(waste_items=waste_items),
    didactic_model=DidacticModel(uebungen=intro_exercises),
    student_model=StudentModel()
)
