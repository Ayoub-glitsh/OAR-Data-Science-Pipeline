"""
clean_companies.py - Nettoie les données des entreprises
"""
import pandas as pd
import re
import hashlib
import logging
from pathlib import Path

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_latest_raw_data():
    """Charge le dernier fichier brut"""
    raw_dir = Path("data/raw")
    
    # Cherche le dernier fichier CSV
    csv_files = list(raw_dir.glob("oar_raw_*.csv"))
    if not csv_files:
        raise FileNotFoundError("Aucun fichier brut trouve")
    
    # Prend le plus récent
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    
    logging.info(f"Chargement: {latest_file}")
    df = pd.read_csv(latest_file)
    logging.info(f"Donnees: {len(df)} lignes")
    
    return df, latest_file

def clean_company_name(name):
    """Nettoie un nom d'entreprise"""
    if pd.isna(name):
        return "Unknown"
    
    name_str = str(name)
    
    # Supprime Inc., Ltd., etc.
    suffixes = ['inc', 'ltd', 'llc', 'gmbh', 'sa', 's.a', 'limited', 'corp']
    for suffix in suffixes:
        name_str = re.sub(fr'\s+{re.escape(suffix)}\.?$', '', name_str, flags=re.IGNORECASE)
    
    # Nettoie la ponctuation
    name_str = re.sub(r'[^\w\s&-]', ' ', name_str)
    name_str = re.sub(r'\s+', ' ', name_str).strip()
    
    # Met en Title Case
    return name_str.title()

def normalize_country(country):
    """Normalise le nom d'un pays"""
    if pd.isna(country):
        return "Unknown"
    
    country_str = str(country).strip().title()
    
    # Corrections manuelles
    corrections = {
        'Maroc': 'Morocco',
        'España': 'Spain',
        'Espana': 'Spain',
        'Italie': 'Italy',
        'Italia': 'Italy',
        'Grece': 'Greece',
        'Portugal': 'Portugal',  # Déjà bon
        'France': 'France',      # Déjà bon
        'Malta': 'Malta'         # Déjà bon
    }
    
    return corrections.get(country_str, country_str)

def generate_company_id(name, country):
    """Génère un ID unique pour une entreprise"""
    text = f"{name}|{country}".lower().strip()
    return hashlib.md5(text.encode()).hexdigest()[:10]

def clean_and_extract_companies(df):
    """Nettoie et extrait les entreprises"""
    logging.info("Nettoyage des entreprises...")
    
    # Trouve la colonne avec les noms d'entreprise
    company_cols = ['company_name', 'name', 'company']
    company_col = next((col for col in company_cols if col in df.columns), None)
    
    if not company_col:
        company_col = df.columns[0]
        logging.warning(f"Colonne entreprise non trouvee, utilisation de: {company_col}")
    
    # Prépare les données
    companies_data = []
    
    for _, row in df.iterrows():
        # Nettoie le nom
        raw_name = row.get(company_col, 'Unknown')
        clean_name = clean_company_name(raw_name)
        
        # Normalise le pays
        country = normalize_country(row.get('country', 'Unknown'))
        
        # Génère l'ID
        company_id = generate_company_id(clean_name, country)
        
        companies_data.append({
            'company_id': company_id,
            'company_name': clean_name,
            'country': country,
            'original_name': raw_name if raw_name != clean_name else ''
        })
    
    # Crée le DataFrame
    companies_df = pd.DataFrame(companies_data)
    
    # Enlève les doublons (même ID = même entreprise)
    companies_df = companies_df.drop_duplicates(subset=['company_id'])
    
    logging.info(f"Entreprises nettoyees: {len(companies_df)}")
    return companies_df

def save_cleaned_companies(df):
    """Sauvegarde les entreprises nettoyées"""
    output_dir = Path("data/cleaned")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "companies.csv"
    df.to_csv(output_path, index=False)
    
    logging.info(f"Sauvegarde: {output_path}")
    
    # Affiche un échantillon
    print("\n" + "="*50)
    print("ECHANTILLON DES ENTREPRISES NETTOYEES:")
    print("="*50)
    print(df.head(10).to_string(index=False))
    print(f"\nTotal: {len(df)} entreprises uniques")
    
    return output_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*50)
    print("NETTOYAGE DES ENTREPRISES")
    print("="*50)
    
    try:
        # 1. Charger
        raw_df, source_file = load_latest_raw_data()
        
        # 2. Nettoyer
        companies_df = clean_and_extract_companies(raw_df)
        
        # 3. Sauvegarder
        save_cleaned_companies(companies_df)
        
        print("\n" + "="*50)
        print("NETTOYAGE TERMINE!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        return False

if __name__ == "__main__":
    main()