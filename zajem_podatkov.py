import os # Knjiznjica za delo z datotečnim sistemom
import re 
import pandas as pd
import bs4

PODATKI_MAPA = "podatki"
CSV_DATOTEKA = "podatki/nepremicnine_ljubljana.csv"

# ==============================================================================
# POMOŽNE FUNKCIJE ZA ODBDELAVO IN ČIŠČENJE PODATKOV
# ==============================================================================
def pocisti_stevilko(besedilo, vzorec, pretvori_v_float = False): 
    """Pomožna funkcija za čiščenje in pretvorbo številskih nizov iz HTML-ja.
    Sprejme surovo besedilo in regularni izraz (vzorec). Če najde ujemanje,
    izlušči številčni del ter ga varno pretvori v int ali float.
    """
    if not besedilo:
        return None
    ujemanje = re.search(vzorec, besedilo)
    if ujemanje:
        niz_stevilke = ujemanje.group(1)
        try:
            if pretvori_v_float:
                # Za decimalna števila (float): zamenjamo slovensko vejico s piko ("55,20" -> "55.20")
                return float(niz_stevilke.replace(",", "."))
            else:
                # Za cela števila (int): odstranimo pike za tisočice ("250.000" -> "250000")
                return int(niz_stevilke.replace(".", ""))
        except ValueError:
            # Če besedila ni mogoče pretvoriti v število, varno vrnemo None
            return None

    # Če Regex ni našel nobenega ujemanja v besedilu, vrnemo None
    return None

def poisci_podatke_oglasa(oglas_juha):
    """Iz HTML objekta posamezne podstrani oglasa izlušči vse podrobne podatke."""
    
    # 1. LOKACIJA / UPRAVNA ENOTA (Z Regexom poiščemo besedilo za "Upravna enota:")
    upravna_enota = None
    ue_element = oglas_juha.find(string=re.compile(r"Upravna enota", re.IGNORECASE))
    if ue_element:
        # Preberemo celotno besedilo starševske značke in izrežemo podatek za dvopičjem
        ujemanje_ue = re.search(r"Upravna enota:\s*(.*)", ue_element.parent.get_text(strip=True))
        if ujemanje_ue:
            upravna_enota = ujemanje_ue.group(1).strip()

    # 2. CENA (Iščemo razred ali značko z ceno na podstrani oglasa)
    cena_tag = oglas_juha.find("span", class_="cena") or oglas_juha.find("div", class_="price")
    cena_besedilo = cena_tag.get_text(strip=True) if cena_tag else None
    cena = pocisti_stevilko(cena_besedilo, r"([\d.]+)\s*€")

    # 3. VELIKOST (m2)
    velikost_tag = oglas_juha.find("span", class_="velikost") or oglas_juha.find("div", class_="size")
    velikost_besedilo = velikost_tag.get_text(strip=True) if velikost_tag else None
    velikost = pocisti_stevilko(velikost_besedilo, r"([\d,]+)\s*m2", pretvori_v_float=True)

    # 4. LETO GRADNJE
    leto_tag = oglas_juha.find("span", class_="leto") or oglas_juha.find("div", class_="year")
    leto_besedilo = leto_tag.get_text(strip=True) if leto_tag else None
    leto = pocisti_stevilko(leto_besedilo, r"(\d{4})")

    # Izračun cene na m2 (če imamo oba podatka)
    cena_per_m2 = round(cena / velikost, 2) if (cena and velikost) else None

    return {
        "upravna_enota": upravna_enota,
        "cena": cena,
        "velikost_m2": velikost,
        "leto_gradnje": leto,
        "cena_per_m2": cena_per_m2
    }


def poisci_vse_oglase(html_vsebina):
    """Iz celotne HTML kode seznama poišče vse oglase in izlušči podatke."""
    juha = bs4.BeautifulSoup(html_vsebina, "html.parser")
    seznam_oglasov = []

    # Poiščemo vse bloke oglasov na seznamu
    bloki_oglasov = juha.find_all("div", class_="property-details") or juha.find_all("div", class_="o-loop")

    for oglas in bloki_oglasov:
        # 1. Najprej iz seznama poberemo ID in osnovni naslov
        id_oglasa = oglas.get("id") or oglas.get("data-id")
        
        naslov_tag = oglas.find("span", class_="title") or oglas.find("a")
        naslov = naslov_tag.get_text(strip=True) if naslov_tag else None

        # 2. Poiščemo podatke znotraj tega oglasa (ali podstrani)
        podatki_oglasa = poisci_podatke_oglasa(oglas)
        
        # 3. Združimo vse podatke v en slovar
        zdruzeni_podatki = {
            "id": id_oglasa,
            "naslov": naslov,
            **podatki_oglasa  # Doda vse kjuče iz funkcije poisci_podatke_oglasa
        }
        
        seznam_oglasov.append(zdruzeni_podatki)

    return seznam_oglasov

def shrani_v_csv(seznam_oglasov, pot_do_datoteke=CSV_DATOTEKA):
    """Sprejme seznam slovarjev z oglasi in jih shrani v CSV datoteko."""
    os.makedirs(PODATKI_MAPA, exist_ok=True)
    df = pd.DataFrame(seznam_oglasov)
    df.to_csv(pot_do_datoteke, index=False, encoding="utf-8")

