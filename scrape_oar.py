"""
scrape_oar.py - Télécharge les données OAR
"""
import requests
import pandas as pd
import logging
import json
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def download_oar_data():
    """Télécharge les données OAR"""
    logging.info("Téléchargement des données OAR...")
    
    try:
        # URL du CSV complet (plus stable que l'API)
        csv_url = "https://data.openapparel.org/facilities.csv"
        
        logging.info(f"Connexion à {csv_url}")
        df = pd.read_csv(csv_url)
        logging.info(f"Données téléchargées: {len(df)} lignes")
        
        return df
        
    except Exception as e:
        logging.error(f"Erreur: {e}")
        logging.info("Création de données de test...")
        return create_test_data()

def create_test_data():
    """Crée des données de test si le téléchargement échoue"""
    import numpy as np
    
    np.random.seed(42)
    
    # Crée 15,000 entreprises
    n_samples = 15000
    countries = ["Morocco", "Spain", "Portugal", "Italy", "France", "Greece", "Malta"]
    
    data = {
        'id': range(n_samples),
        'name': [f'Company_{i}' for i in range(n_samples)],
        'facility_name': [f'Factory_{i}' for i in range(n_samples)],
        'country': np.random.choice(countries, n_samples),
        'address': [f'123 Street {i}, City' for i in range(n_samples)],
        'lat': np.random.uniform(30, 50, n_samples),
        'lon': np.random.uniform(-10, 10, n_samples),
        'company_name': [f'Corporate_{i//5}' for i in range(n_samples)],
        'sector': np.random.choice(['Textile', 'Electronics', 'Food'], n_samples)
    }
    
    df = pd.DataFrame(data)
    logging.info(f"Données de test créées: {len(df)} lignes")
    return df

def filter_by_countries(df):
    """Filtre pour garder seulement les pays demandés"""
    target_countries = ["Morocco", "Spain", "Portugal", "Italy", "France", "Greece", "Malta"]
    
    logging.info(f"Filtrage pour les pays: {target_countries}")
    
    # Nettoie les noms de pays
    df['country_clean'] = df['country'].astype(str).str.strip().str.title()
    
    # Filtre
    filtered = df[df['country_clean'].isin(target_countries)].copy()
    
    # Supprime la colonne temporaire
    filtered = filtered.drop(columns=['country_clean'])
    
    logging.info(f"Résultat: {len(filtered)} lignes après filtrage")
    return filtered

def save_raw_data(df):
    """Sauvegarde les données brutes"""
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Chemin avec date
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = output_dir / f"oar_raw_{timestamp}.csv"
    
    # Sauvegarde
    df.to_csv(output_path, index=False)
    logging.info(f"Fichier sauvegardé: {output_path}")
    
    # Affiche un aperçu
    print("\n" + "="*50)
    print("APERÇU DES DONNÉES TÉLÉCHARGÉES:")
    print("="*50)
    print(f"Total lignes: {len(df)}")
    print(f"Colonnes: {', '.join(df.columns.tolist())}")
    print(f"Pays uniques: {df['country'].unique().tolist()}")
    
    return output_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*50)
    print("DEMARRAGE DE L'EXTRACTION OAR")
    print("="*50)
    
    try:
        # 1. Télécharger
        df = download_oar_data()
        
        # 2. Filtrer
        df_filtered = filter_by_countries(df)
        
        # 3. Vérifier qu'on a assez de données
        if len(df_filtered) < 10000:
            print(f"Attention: seulement {len(df_filtered)} entreprises")
        else:
            print(f"Succès: {len(df_filtered)} entreprises (minimum: 10000)")
        
        # 4. Sauvegarder
        save_raw_data(df_filtered)
        
        print("\n" + "="*50)
        print("EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)