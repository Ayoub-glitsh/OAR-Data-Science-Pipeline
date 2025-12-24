"""
relational_builder.py - Construit la base de données relationnelle
"""
import pandas as pd
import logging
from pathlib import Path

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_cleaned_data():
    """Charge les données nettoyées"""
    cleaned_dir = Path("data/cleaned")
    
    # Vérifie que les fichiers existent
    required_files = ['companies.csv', 'facilities.csv', 'company_facilities.csv']
    missing_files = []
    
    for file in required_files:
        if not (cleaned_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Fichiers manquants: {missing_files}")
    
    # Charge les données
    companies = pd.read_csv(cleaned_dir / "companies.csv")
    facilities = pd.read_csv(cleaned_dir / "facilities.csv")
    links = pd.read_csv(cleaned_dir / "company_facilities.csv")
    
    logging.info(f"Entreprises: {len(companies)}")
    logging.info(f"Etablissements: {len(facilities)}")
    logging.info(f"Liens: {len(links)}")
    
    return companies, facilities, links

def validate_integrity(companies, facilities, links):
    """Valide l'intégrité des données"""
    print("\n" + "="*50)
    print("VALIDATION DE L'INTEGRITE")
    print("="*50)
    
    errors = []
    warnings = []
    
    # 1. Vérifie les IDs uniques
    if companies['company_id'].duplicated().any():
        dup_count = companies['company_id'].duplicated().sum()
        errors.append(f"[ERREUR] {dup_count} IDs d'entreprise en double")
    else:
        print("IDs d'entreprise: tous uniques")
    
    if facilities['facility_id'].duplicated().any():
        dup_count = facilities['facility_id'].duplicated().sum()
        errors.append(f"[ERREUR] {dup_count} IDs d'etablissement en double")
    else:
        print("IDs d'etablissement: tous uniques")
    
    # 2. Vérifie les relations
    # Établissements sans entreprise
    orphaned_facilities = facilities[~facilities['facility_id'].isin(links['facility_id'])]
    if len(orphaned_facilities) > 0:
        warnings.append(f"[AVERTISSEMENT] {len(orphaned_facilities)} etablissements sans lien d'entreprise")
    else:
        print("Tous les etablissements ont un lien")
    
    # Entreprises sans établissements
    orphaned_companies = companies[~companies['company_id'].isin(links['company_id'])]
    if len(orphaned_companies) > 0:
        warnings.append(f"[AVERTISSEMENT] {len(orphaned_companies)} entreprises sans etablissements")
    else:
        print("Toutes les entreprises ont au moins un etablissement")
    
    # 3. Vérifie les liens invalides
    invalid_companies = links[~links['company_id'].isin(companies['company_id'])]
    invalid_facilities = links[~links['facility_id'].isin(facilities['facility_id'])]
    
    if len(invalid_companies) > 0:
        errors.append(f"[ERREUR] {len(invalid_companies)} liens avec entreprises inexistantes")
    
    if len(invalid_facilities) > 0:
        errors.append(f"[ERREUR] {len(invalid_facilities)} liens avec etablissements inexistants")
    
    # Affiche les résultats
    if errors:
        print("\nERREURS TROUVEES:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\nAVERTISSEMENTS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\nTOUTES LES VALIDATIONS SONT PASSEES!")
    
    return len(errors) == 0

def build_relational_database(companies, facilities, links):
    """Construit la base de données relationnelle finale"""
    print("\n" + "="*50)
    print("CONSTRUCTION DE LA BASE DE DONNEES")
    print("="*50)
    
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Table Companies (améliorée)
    companies_final = companies.copy()
    
    # Ajoute des métadonnées
    companies_final['record_source'] = 'OAR Pipeline v1.0'
    companies_final['created_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # Calcule le nombre d'établissements
    facility_counts = links.groupby('company_id').size()
    companies_final = companies_final.merge(
        facility_counts.rename('facility_count'),
        left_on='company_id',
        right_index=True,
        how='left'
    )
    
    # Remplit les valeurs manquantes
    companies_final['facility_count'] = companies_final['facility_count'].fillna(0).astype(int)
    
    # 2. Table Facilities (améliorée)
    facilities_final = facilities.copy()
    facilities_final['record_source'] = 'OAR Pipeline v1.0'
    facilities_final['created_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # 3. Table Links (vérifiée)
    links_final = links.copy()
    links_final['relationship_type'] = 'ownership'
    links_final['created_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # Sauvegarde
    companies_path = output_dir / "relational_companies.csv"
    facilities_path = output_dir / "relational_facilities.csv"
    links_path = output_dir / "relational_links.csv"
    
    companies_final.to_csv(companies_path, index=False)
    facilities_final.to_csv(facilities_path, index=False)
    links_final.to_csv(links_path, index=False)
    
    print(f"Sauvegarde Companies: {companies_path}")
    print(f"Sauvegarde Facilities: {facilities_path}")
    print(f"Sauvegarde Links: {links_path}")
    
    # Affiche les statistiques
    print("\nSTATISTIQUES FINALES:")
    print(f"Entreprises: {len(companies_final):,}")
    print(f"Etablissements: {len(facilities_final):,}")
    print(f"Liens: {len(links_final):,}")
    
    avg_facilities = companies_final['facility_count'].mean()
    max_facilities = companies_final['facility_count'].max()
    
    print(f"Etablissements/entreprise (moyenne): {avg_facilities:.2f}")
    print(f"Etablissements/entreprise (maximum): {max_facilities}")
    
    # Distribution par pays
    print("\nDISTRIBUTION PAR PAYS:")
    country_dist = companies_final['country'].value_counts()
    for country, count in country_dist.head(10).items():
        print(f"  {country:15} : {count:6,} entreprises")
    
    return companies_path, facilities_path, links_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*60)
    print("CONSTRUCTION DE LA BASE DE DONNEES RELATIONNELLE")
    print("="*60)
    
    try:
        # 1. Charger
        companies, facilities, links = load_cleaned_data()
        
        # 2. Valider
        is_valid = validate_integrity(companies, facilities, links)
        
        if not is_valid:
            print("\nProblemes detectes, mais on continue...")
        
        # 3. Construire
        build_relational_database(companies, facilities, links)
        
        print("\n" + "="*60)
        print("BASE DE DONNEES RELATIONNELLE CREE AVEC SUCCES!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()