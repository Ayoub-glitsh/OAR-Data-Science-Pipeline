"""
clean_facilities.py - Nettoie et extrait les établissements
"""
import pandas as pd
import hashlib
import logging
from pathlib import Path

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_data():
    """Charge toutes les données nécessaires"""
    # Données brutes
    raw_dir = Path("data/raw")
    raw_files = list(raw_dir.glob("oar_raw_*.csv"))
    if not raw_files:
        raise FileNotFoundError("Aucun fichier brut trouve")
    
    latest_raw = max(raw_files, key=lambda x: x.stat().st_mtime)
    raw_df = pd.read_csv(latest_raw)
    logging.info(f"Donnees brutes: {latest_raw} ({len(raw_df)} lignes)")
    
    # Entreprises nettoyées
    companies_path = Path("data/cleaned/companies.csv")
    if not companies_path.exists():
        raise FileNotFoundError("Fichier companies.csv non trouve")
    
    companies_df = pd.read_csv(companies_path)
    logging.info(f"Entreprises: {companies_path} ({len(companies_df)} entreprises)")
    
    return raw_df, companies_df

def clean_facility_name(name):
    """Nettoie un nom d'établissement"""
    if pd.isna(name):
        return "Unknown Facility"
    
    name_str = str(name)
    
    # Nettoie les espaces multiples
    name_str = ' '.join(name_str.split())
    
    # Supprime les caractères spéciaux indésirables
    name_str = ''.join(char for char in name_str if ord(char) < 128 or char in 'àâäéèêëîïôöùûüç')
    
    # Met en Title Case
    return name_str.strip().title()

def generate_facility_id(name, lat, lon):
    """Génère un ID unique pour un établissement"""
    # Utilise nom + coordonnées pour un ID stable
    combined = f"{name}|{lat:.6f}|{lon:.6f}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]

def extract_facilities(raw_df, companies_df):
    """Extrait les établissements des données brutes"""
    logging.info("Extraction des établissements...")
    
    facilities_data = []
    links_data = []
    
    # Crée un mapping pour trouver les entreprises
    # On utilise le nom original pour faire le lien
    company_map = {}
    for _, company in companies_df.iterrows():
        original_name = company.get('original_name', '')
        if pd.notna(original_name) and original_name.strip():
            company_map[original_name.strip().lower()] = company['company_id']
    
    # Traite chaque ligne
    for idx, row in raw_df.iterrows():
        # Nom de l'établissement
        facility_name = clean_facility_name(
            row.get('facility_name', row.get('name', f'Facility_{idx}'))
        )
        
        # Coordonnées
        lat = float(row.get('lat', 0))
        lon = float(row.get('lon', 0))
        
        # ID
        facility_id = generate_facility_id(facility_name, lat, lon)
        
        # Trouve l'entreprise
        company_id = "UNKNOWN"
        
        # Essaye plusieurs colonnes possibles
        possible_cols = ['company_name', 'name', 'company', 'organization']
        for col in possible_cols:
            if col in row and pd.notna(row[col]):
                raw_company_name = str(row[col]).strip().lower()
                if raw_company_name in company_map:
                    company_id = company_map[raw_company_name]
                    break
        
        # Si pas trouvé, on cherche par similarité
        if company_id == "UNKNOWN" and 'company_name' in companies_df.columns:
            # Prend la première entreprise comme fallback
            company_id = companies_df.iloc[0]['company_id']
        
        # Ajoute l'établissement
        facilities_data.append({
            'facility_id': facility_id,
            'facility_name': facility_name,
            'latitude': lat,
            'longitude': lon,
            'country': row.get('country', 'Unknown'),
            'address': str(row.get('address', '')).strip(),
            'sector': row.get('sector', 'Unknown')
        })
        
        # Ajoute le lien
        links_data.append({
            'company_id': company_id,
            'facility_id': facility_id
        })
        
        # Progression
        if (idx + 1) % 1000 == 0:
            logging.info(f"  Traite {idx + 1}/{len(raw_df)} établissements")
    
    # Crée les DataFrames
    facilities_df = pd.DataFrame(facilities_data)
    links_df = pd.DataFrame(links_data)
    
    # Enlève les doublons
    facilities_df = facilities_df.drop_duplicates(subset=['facility_id'])
    links_df = links_df.drop_duplicates()
    
    logging.info(f"Etablissements: {len(facilities_df)}")
    logging.info(f"Liens: {len(links_df)}")
    
    return facilities_df, links_df

def save_results(facilities_df, links_df):
    """Sauvegarde les résultats"""
    output_dir = Path("data/cleaned")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Établissements
    facilities_path = output_dir / "facilities.csv"
    facilities_df.to_csv(facilities_path, index=False)
    
    # Liens
    links_path = output_dir / "company_facilities.csv"
    links_df.to_csv(links_path, index=False)
    
    logging.info(f"Etablissements: {facilities_path}")
    logging.info(f"Liens: {links_path}")
    
    # Affiche un résumé
    print("\n" + "="*50)
    print("RESUME DES ETABLISSEMENTS")
    print("="*50)
    print(f"Nombre d'établissements: {len(facilities_df):,}")
    print(f"Nombre de liens: {len(links_df):,}")
    print(f"Pays couverts: {facilities_df['country'].nunique()}")
    print(f"Secteurs: {facilities_df['sector'].nunique()}")
    
    print("\nECHANTILLON (5 premiers):")
    print(facilities_df.head().to_string(index=False))
    
    return facilities_path, links_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*50)
    print("EXTRACTION DES ETABLISSEMENTS")
    print("="*50)
    
    try:
        # 1. Charger
        raw_df, companies_df = load_data()
        
        # 2. Extraire
        facilities_df, links_df = extract_facilities(raw_df, companies_df)
        
        # 3. Sauvegarder
        save_results(facilities_df, links_df)
        
        print("\n" + "="*50)
        print("EXTRACTION TERMINEE!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()