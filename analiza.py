import pandas as pd
import matplotlib.pyplot as plt

# 1. Naložitev podatkov iz CSV datoteke
pot_csv = "podatki/nepremicnine.csv"
df = pd.read_csv(pot_csv)

# 2. Funkcija za mapiranje in združevanje surovih lokacij v smiselne mestne četrti
def zdruzi_v_skupine(lokacija):
    if not isinstance(lokacija, str):
        return None
    
    l = lokacija.strip()
    
    if l in ["Center", "Stara Lj.", "Tabor", "Prule", "Kodeljevo"]:
        return "Center Ljubljana"
    elif l in ["Bežigrad", "Zupančičeva Jama", "BS 3", "Brinje"]:
        return "Bežigrad"
    elif l in ["Savsko Naselje", "Nove Jarše", "Zelena Jama", "Stožice"]:
        return "Savsko naselje – Jarše"
    elif l in ["Moste", "Štepanjsko Naselje"]:
        return "Moste"
    elif l in ["Šiška", "Zg. Šiška", "Sp. Šiška"]:
        return "Šiška"
    elif l in ["Koseze", "Dravlje", "Podutik"]:
        return "Koseze – Dravlje"
    elif l in ["Šentvid", "Gunclje", "Stanežiče", "Spodnje Gameljne", "Brod", "Mostec"]:
        return "Šentvid"
    elif l in ["Vič", "Rožna Dolina", "Vrhovci", "Dolgi Most"]:
        return "Vič"
    elif l in ["Trnovo"]:
        return "Trnovo"
    elif l in ["Polje", "Nove Fužine", "Fužine"]:
        return "Fužine – Polje"
    elif l in ["Zalog", "Vevče", "Zg. Kašelj"]:
        return "Zalog – Kašelj"
    elif l in ["Rudnik"]:
        return "Rudnik"
    else:
        return None

# Ustvarimo nov stolpec z urejenimi skupinami in odstranimo neveljavne vrstice
df['skupina_lokacij'] = df['lokacija'].apply(zdruzi_v_skupine)
df = df.dropna(subset=['skupina_lokacij'])

print("--- OSNOVNE INFORMACIJE O ANALIZI ---")
print(f"Skupno število uspešno obdelanih oglasov: {len(df)}")
print()

# 3. Podrobna statistična analiza (št. oglasov, povprečje, mediana, min, max)
statistike = df.groupby('skupina_lokacij')['cena_per_m2'].agg(
    št_oglasov='count',
    povprečje='mean',
    mediana='median',
    minimum='min',
    maksimum='max'
).round(2)

print("--- PODROBNA STATISTIKA CENA / m² PO ČETRTEH ---")
print(statistike.sort_values(by='povprečje', ascending=False))
print()

# 4. PRVI GRAF: Povprečna cena m² po območjih (horizontalni stolpci)
povprecje_skupin = statistike['povprečje']

plt.figure(figsize=(12, 8))
povprecje_skupin.sort_values().plot(kind='barh', color='cornflowerblue', edgecolor='black')
plt.title('Povprečna cena m² po ljubljanskih četrteh in območjih', fontsize=14, fontweight='bold')
plt.xlabel('Cena / m² (€)', fontsize=12)
plt.ylabel('Območje', fontsize=12)
plt.tight_layout()

plt.savefig('graf_natancne_skupine.png', dpi=300)
print("Graf cen je bil uspešno shranjen kot 'graf_natancne_skupine.png'!")

# Prikaz prvega grafa (ko ga zapreš, se odpre drugi graf)
plt.show()

# 5. DRUGI GRAF: Porazdelitev stanovanj po številu sob (Garsonjera na 1. mestu, brez neznanega)
stolpec_sob = 'stevilo_sob'

if stolpec_sob in df.columns:
    # Funkcija za čiščenje – ohranimo le garsonjere in čista števila sob
    def ocisti_sobe(val):
        if pd.isna(val):
            return None
        v = str(val).strip().lower()
        
        if "garsonjer" in v:
            return "Garsonjera"
        elif "1" in v and "1," not in v and "1." not in v:
            return "1-sobno"
        elif "2" in v and "2," not in v and "2." not in v:
            return "2-sobno"
        elif "3" in v and "3," not in v and "3." not in v:
            return "3-sobno"
        elif "4" in v:
            return "4-sobno"
        elif "5" in v or "več" in v:
            return "5+ sobno"
        else:
            return None  # Vse ostalo (vključno z neznanim) zavržemo

    df['urejene_sobe'] = df[stolpec_sob].apply(ocisti_sobe)
    
    # Točen vrstni red (Garsonjera na prvem mestu)
    zeleni_vrstni_red = ["Garsonjera", "1-sobno", "2-sobno", "3-sobno", "4-sobno", "5+ sobno"]
    
    # Izračunamo frekvence in jih filtriramo glede na zgornji seznam (brez neznanega)
    stevci_sob = df['urejene_sobe'].value_counts()
    stevci_sob = stevci_sob.reindex([kat for kat in zeleni_vrstni_red if kat in stevci_sob.index])

    plt.figure(figsize=(10, 6))
    stevci_sob.plot(kind='bar', color='steelblue', edgecolor='black', width=0.8)
    
    plt.title('Porazdelitev stanovanj glede na število sob', fontsize=14, fontweight='bold')
    plt.xlabel('Tip stanovanja / Število sob', fontsize=12)
    plt.ylabel('Število stanovanj (oglasov)', fontsize=12)
    plt.xticks(rotation=0)  # Ohranimo vodoravne napise
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    plt.savefig('graf_struktura_sob.png', dpi=300)
    print("Graf strukture sob je bil uspešno shranjen kot 'graf_struktura_sob.png'!")

    plt.show()
else:
    print(f"Opozorilo: Stolpec '{stolpec_sob}' ni bil najden v datoteki.")

# 6. TRETJI GRAF: Raztreseni diagram (Cena glede na kvadraturo)
stolpec_kvadratura = 'velikost_m2'
stolpec_cena = 'cena'

if stolpec_kvadratura in df.columns and stolpec_cena in df.columns:
    plt.figure(figsize=(10, 6))
    
    # Skrbno očistimo in pretvorimo podatke v števila (odstranimo morebitne presledke ipd.)
    x = pd.to_numeric(df[stolpec_kvadratura].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce')
    y = pd.to_numeric(df[stolpec_cena].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce')
    
    plt.scatter(x, y, color='teal', alpha=0.6, edgecolor='black', s=40)
    
    plt.title('Vpliv kvadrature na skupno ceno stanovanja', fontsize=14, fontweight='bold')
    plt.xlabel('Kvadratura (m²)', fontsize=12)
    plt.ylabel('Skupna cena (€)', fontsize=12)
    
    # Izklopimo znanstveno zapisovanje / čudno skaliranje osi, da so vidne cele vrednosti
    plt.ticklabel_format(style='plain', axis='both')
    
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    plt.savefig('graf_cena_kvadratura.png', dpi=300)
    print("Tretji graf (cena glede na kvadraturo) je bil uspešno shranjen kot 'graf_cena_kvadratura.png'!")

    plt.show()
else:
    print("Opozorilo: Stolpca za kvadraturo ali ceno nista bila najdena.")

# 7. ČETRTI GRAF: Škatlasti diagram (Boxplot) cen na m² po posameznih četrteh
plt.figure(figsize=(12, 7))

podatki_za_boxplot = [group['cena_per_m2'].dropna() for name, group in df.groupby('skupina_lokacij')]
ime_skupin = [name for name, group in df.groupby('skupina_lokacij')]

# Narišemo boxplot BREZ argumenta labels
bp = plt.boxplot(podatki_za_boxplot, patch_artist=True, 
                 boxprops=dict(facecolor='lightblue', color='black'),
                 medianprops=dict(color='red', linewidth=1.5))

# Imena četrti nastavimo tukaj posebej, kar deluje v vseh verzijah Matplotliba
plt.xticks(ticks=range(1, len(ime_skupin) + 1), labels=ime_skupin, rotation=45, ha='right')

plt.title('Porazdelitev in razpon cen na m² po ljubljanskih območjih', fontsize=14, fontweight='bold')
plt.xlabel('Območje', fontsize=12)
plt.ylabel('Cena / m² (€)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

plt.savefig('graf_box_cene.png', dpi=300)
print("Četrti graf (škatlasti diagram cen) je bil uspešno shranjen kot 'graf_box_cene.png'!")

plt.show()