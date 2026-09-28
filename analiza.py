import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Naložimo podatke iz CSV datoteke
df = pd.read_csv("podatki/nepremicnine.csv") 

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

# Ustvarimo nov stolpec z urejenimi skupinami
df['skupina_lokacij'] = df['lokacija'].apply(zdruzi_v_skupine)

# Očistimo numerične stolpce (cena, velikost, leto)
df['cena_num'] = pd.to_numeric(df['cena'].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce')
df['velikost_num'] = pd.to_numeric(df['velikost_m2'].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce')
df['leto_num'] = pd.to_numeric(df['leto_gradnje'], errors='coerce')

# Na novo in pravilno izračunamo ceno na m², da se izognemo naramnim nulam ali napakam
df['cena_per_m2'] = df['cena_num'] / df['velikost_num']

# Odstranimo vrstice, kjer nimamo lokacije ali pa so vrednosti cen/kvadrature enake 0 ali manjšo (prepreči padec grafa na 0)
df = df.dropna(subset=['skupina_lokacij'])
df = df[(df['cena_num'] > 0) & (df['velikost_num'] > 0) & (df['cena_per_m2'] > 0)]

print(f"Število oglasov po čiščenju in odstranitvi neveljavnih cen: {len(df)}")
print()

# 3. Podrobna statistična analiza po četrtih
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


# --- GRAFI ---

# 1. GRAF: Povprečna cena m² po območjih
plt.figure(figsize=(12, 8))
statistike['povprečje'].sort_values().plot(kind='barh', color='cornflowerblue', edgecolor='black')
plt.title('Povprečna cena m² po ljubljanskih četrteh', fontsize=14, fontweight='bold')
plt.xlabel('Cena / m² (€)', fontsize=12)
plt.ylabel('Območje', fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.close()

# 2. GRAF: Število oglasov po območjih
plt.figure(figsize=(11, 6))
df['skupina_lokacij'].value_counts().sort_values().plot(kind='barh', color='mediumpurple', edgecolor='black', width=0.8)
plt.title('Število nepremičninskih oglasov po ljubljanskih območjih', fontsize=14, fontweight='bold')
plt.xlabel('Število oglasov', fontsize=12)
plt.ylabel('Območje', fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.close()

# 3. GRAF: Porazdelitev stanovanj po številu sob
def ocisti_sobe(val):
    if pd.isna(val):
        return None
    v = str(val).strip().lower()
    if "garsonjer" in v: return "Garsonjera"
    elif "1" in v and "1," not in v and "1." not in v: return "1-sobno"
    elif "2" in v and "2," not in v and "2." not in v: return "2-sobno"
    elif "3" in v and "3," not in v and "3." not in v: return "3-sobno"
    elif "4" in v: return "4-sobno"
    elif "5" in v or "več" in v: return "5+ sobno"
    return None

df['urejene_sobe'] = df['stevilo_sob'].apply(ocisti_sobe)
zeleni_vrstni_red = ["Garsonjera", "1-sobno", "2-sobno", "3-sobno", "4-sobno", "5+ sobno"]
stevci_sob = df['urejene_sobe'].value_counts().reindex([kat for kat in zeleni_vrstni_red if kat in df['urejene_sobe'].unique()])

plt.figure(figsize=(10, 6))
stevci_sob.plot(kind='bar', color='steelblue', edgecolor='black', width=0.8)
plt.title('Porazdelitev stanovanj glede na število sob', fontsize=14, fontweight='bold')
plt.xlabel('Tip stanovanja', fontsize=12)
plt.ylabel('Število stanovanj', fontsize=12)
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.close()

# 4. GRAF: Raztreseni diagram (Kvadratura vs Skupna cena)
plt.figure(figsize=(10, 6))
plt.scatter(df['velikost_num'], df['cena_num'], color='teal', alpha=0.6, edgecolor='black', s=40)
plt.title('Vpliv kvadrature na skupno ceno stanovanja', fontsize=14, fontweight='bold')
plt.xlabel('Kvadratura (m²)', fontsize=12)
plt.ylabel('Skupna cena (€)', fontsize=12)
plt.ticklabel_format(style='plain', axis='both')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.close()

# 5. GRAF: Povprečna cena na m² glede na leto gradnje
cena_po_letih = df.groupby('leto_num')['cena_per_m2'].mean().sort_index()
plt.figure(figsize=(11, 6))
cena_po_letih.plot(kind='line', marker='o', color='darkorange', linewidth=2, markersize=5)
plt.title('Povprečna cena na m² glede na leto gradnje stavbe', fontsize=14, fontweight='bold')
plt.xlabel('Leto gradnje', fontsize=12)
plt.ylabel('Povprečna cena / m² (€)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.close()

# 6. GRAF: Škatlasti diagram (Boxplot) cen na m² glede na število sob
plt.figure(figsize=(11, 6))
df_box = df.dropna(subset=['urejene_sobe', 'cena_per_m2'])
obstojuce_kategorije = [kat for kat in zeleni_vrstni_red if kat in df_box['urejene_sobe'].values]
podatki_box = [df_box[df_box['urejene_sobe'] == kat]['cena_per_m2'] for kat in obstojuce_kategorije]

plt.boxplot(podatki_box, patch_artist=True,
            boxprops=dict(facecolor='lightblue', color='black'),
            medianprops=dict(color='red', linewidth=2))

plt.xticks(range(1, len(obstojuce_kategorije) + 1), obstojuce_kategorije)
plt.title('Razpon cen na m² glede na tip stanovanja (Boxplot)', fontsize=14, fontweight='bold')
plt.xlabel('Tip stanovanja', fontsize=12)
plt.ylabel('Cena / m² (€)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.close()

# 7. GRAF: Korelacijska matrika (Heatmap) vseh numeričnih podatkov
numeric_df = df[['cena_num', 'velikost_num', 'cena_per_m2', 'leto_num']].dropna()

plt.figure(figsize=(8, 6))
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
plt.title('Korelacijska matrika nepremičninskih podatkov', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.close()

print("Vsi grafi (vključno s korelacijsko matriko) so bili uspešno ustvarjeni in shranjeni!")