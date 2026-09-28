import re
import csv
import bs4

def prenesi_lokalno_stran(pot_do_datoteke):
    """Prebere HTML vsebino iz lokalno shranjene datoteke na disku."""
    try:
        with open(pot_do_datoteke, "r", encoding="utf-8") as datoteka:
            return datoteka.read()
    except FileNotFoundError:
        print(f"Datoteka {pot_do_datoteke} ne obstaja.")
        return None

def pocisti_stevilko(besedilo, vzorec, pretvori_v_float=False):
    """Pomožna funkcija za čiščenje številskih vrednosti iz besedila."""
    if not besedilo:
        return None
    najdba = re.search(vzorec, besedilo.replace(".", "").replace(",", "."))
    if najdba:
        try:
            val = najdba.group(1)
            return float(val) if pretvori_v_float else int(float(val))
        except ValueError:
            return None
    return None

def pocisti_lokacijo(naslov):
    """Očisti naslov oglasa, da vrne lepo območje (npr. Bežigrad, Vič, Šiška)."""
    if not naslov:
        return None
    
    lokacija = naslov.upper()
    lokacija = lokacija.replace("LJ. ", "").replace("LJUBLJANA - ", "").replace("LJUBLJANA-", "")
    
    if "," in lokacija:
        lokacija = lokacija.split(",")[0]
        
    return lokacija.strip().title()

def določi_stevilo_sob(naslov, opis):
    """Iz naslova in opisa prepozna število sob oziroma tip stanovanja."""
    skupno_besedilo = f"{naslov} {opis}".lower()
    
    if "garsonjera" in skupno_besedilo:
        return "Garsonjera"
    
    # Išemo vzorce kot npr. "2-sobno", "3 sobno", "dvosobno"
    match = re.search(r"(\d+)\s*[-]?sobno", skupno_besedilo)
    if match:
        return f"{match.group(1)}-sobno"
        
    if "dvosobno" in skupno_besedilo:
        return "2-sobno"
    if "trisobno" in skupno_besedilo:
        return "3-sobno"
    if "enosobno" in skupno_besedilo:
        return "1-sobno"
    if "štirisobno" in skupno_besedilo or "4-sobno" in skupno_besedilo:
        return "4-sobno"
        
    return "Neznano"

def poisci_podatke_oglasa(oglas):
    """Iz posameznega bloka oglasa izlušči ID, naslov, lokacijo, število sob, ceno, velikost in leto."""
    
    # 1. ID OGLASA
    data_href = oglas.get("data-href", "")
    id_ujemanje = re.search(r"_(\d+)/", data_href)
    id_oglasa = id_ujemanje.group(1) if id_ujemanje else None

    # 2. NASLOV
    naslov_tag = oglas.find("h2")
    naslov = naslov_tag.get_text(strip=True) if naslov_tag else None

    # 3. LOKACIJA
    lokacija = pocisti_lokacijo(naslov)

    # 4. OPIS (za prepoznavanje sob)
    desc_tag = oglas.find("p", {"itemprop": "description"})
    opis = desc_tag.get_text(strip=True) if desc_tag else ""

    # 5. ŠTEVILO SOB
    stevilo_sob = določi_stevilo_sob(naslov, opis)

    # 6. CENA
    meta_cena = oglas.find("meta", {"itemprop": "price"})
    if meta_cena and meta_cena.get("content"):
        try:
            cena = float(meta_cena["content"])
        except ValueError:
            cena = None
    else:
        cena_tag = oglas.find("h6")
        cena_besedilo = cena_tag.get_text(strip=True) if cena_tag else None
        cena = pocisti_stevilko(cena_besedilo, r"([\d.]+)", pretvori_v_float=True)

    # 7. VELIKOST IN LETO
    velikost = None
    leto_gradnje = None
    
    ul_tag = oglas.find("ul", {"itemprop": "disambiguatingDescription"})
    if ul_tag:
        elementi_li = ul_tag.find_all("li")
        if len(elementi_li) >= 2:
            velikost_besedilo = elementi_li[0].get_text(strip=True)
            velikost = pocisti_stevilko(velikost_besedilo, r"([\d,]+)", pretvori_v_float=True)
            
            leto_besedilo = elementi_li[1].get_text(strip=True)
            leto_gradnje = pocisti_stevilko(leto_besedilo, r"(\d{4})")

    # Izračun cene na m2
    cena_per_m2 = round(cena / velikost, 2) if (cena and velikost) else None

    return {
        "id": id_oglasa,
        "naslov": naslov,
        "lokacija": lokacija,
        "stevilo_sob": stevilo_sob,
        "cena": cena,
        "velikost_m2": velikost,
        "leto_gradnje": leto_gradnje,
        "cena_per_m2": cena_per_m2
    }

def poisci_vse_oglase(html_vsebina):
    """Poišče vse bloke oglasov v HTML vsebini in vrne seznam slovarjev."""
    juha = bs4.BeautifulSoup(html_vsebina, "html.parser")
    seznam_oglasov = []
    bloki_oglasov = juha.find_all("div", class_="property-details")

    for oglas in bloki_oglasov:
        podatki = poisci_podatke_oglasa(oglas)
        seznam_oglasov.append(podatki)

    return seznam_oglasov

def shrani_v_csv(oglasi, izhodna_datoteka="nepremicnine.csv"):
    """Shrani seznam oglasov v CSV datoteko."""
    if not oglasi:
        print("Ni podatkov za shranjevanje.")
        return

    kljuci = oglasi[0].keys()
    with open(izhodna_datoteka, "w", newline="", encoding="utf-8") as f:
        pisatelj = csv.DictWriter(f, fieldnames=kljuci)
        pisatelj.writeheader()
        for oglas in oglasi:
            pisatelj.writerow(oglas)

if __name__ == "__main__":
    vsi_oglasi = []
    stevilo_strani = 10 
    
    print("Začenjam z branjem vseh 10 lokalnih datotek...")
    
    for i in range(1, stevilo_strani + 1):
        pot_datoteke = f"podatki/stran-{i}.html"
        html_strani = prenesi_lokalno_stran(pot_datoteke)
        
        if html_strani:
            oglasi_na_strani = poisci_vse_oglase(html_strani)
            vsi_oglasi.extend(oglasi_na_strani)
            print(f" -> Prebrana {pot_datoteke}: najdenih {len(oglasi_na_strani)} oglasov.")

    print(f"\nSkupno uspešno zbranih oglasov: {len(vsi_oglasi)}")
    
    # Shranimo vse zbrane podatke v CSV
    shrani_v_csv(vsi_oglasi)
    print("Vsi podatki so uspešno shranjeni v 'nepremicnine.csv'!")

