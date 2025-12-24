"""
export_final.py - Export final des données et rapports
"""
import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime
import shutil

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def create_final_dataset():
    """Crée le jeu de données final"""
    print("\n" + "="*50)
    print(" CRÉATION DU JEU DE DONNÉES FINAL")
    print("="*50)
    
    output_dir = Path("data/outputs")
    
    # Vérifie les fichiers nécessaires
    required_files = [
        'relational_companies.csv',
        'relational_facilities.csv',
        'relational_links.csv',
        'ai_analysis_simple.csv'
    ]
    
    missing_files = []
    for file in required_files:
        if not (output_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"  Fichiers manquants: {missing_files}")
        print("  Essayer de les régénérer...")
        return False
    
    # Charge les données
    companies = pd.read_csv(output_dir / "relational_companies.csv")
    facilities = pd.read_csv(output_dir / "relational_facilities.csv")
    links = pd.read_csv(output_dir / "relational_links.csv")
    ai_results = pd.read_csv(output_dir / "ai_analysis_simple.csv")
    
    print(f" Données chargées:")
    print(f"  • Entreprises: {len(companies):,}")
    print(f"  • Établissements: {len(facilities):,}")
    print(f"  • Liens: {len(links):,}")
    print(f"  • Analyses IA: {len(ai_results):,}")
    
    # Crée un dossier pour l'export final
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    final_dir = Path("final_export") / f"oar_pipeline_{timestamp}"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n Dossier d'export: {final_dir}")
    
    # 1. Export CSV complet
    print("\n Export CSV...")
    
    companies.to_csv(final_dir / "companies_final.csv", index=False)
    facilities.to_csv(final_dir / "facilities_final.csv", index=False)
    links.to_csv(final_dir / "relationships_final.csv", index=False)
    ai_results.to_csv(final_dir / "ai_analysis_final.csv", index=False)
    
    # 2. Export JSON (pour les applications web)
    print(" Export JSON...")
    
    final_json = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "pipeline_version": "1.0",
            "data_source": "Open Apparel Registry",
            "countries_covered": sorted(companies['country'].unique().tolist())
        },
        "summary": {
            "total_companies": int(len(companies)),
            "total_facilities": int(len(facilities)),
            "total_relationships": int(len(links)),
            "sustainable_companies": int(ai_results['has_sustainability'].sum()),
            "sustainability_rate": float((ai_results['has_sustainability'].sum() / len(ai_results)) * 100)
        },
        "companies": companies.head(1000).to_dict(orient='records'),  # Limité pour la taille
        "sample_facilities": facilities.head(500).to_dict(orient='records')
    }
    
    with open(final_dir / "data_summary.json", 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=2, ensure_ascii=False)
    
    # 3. Export Excel (pour les utilisateurs business)
    print(" Export Excel...")
    
    with pd.ExcelWriter(final_dir / "oar_dataset.xlsx", engine='openpyxl') as writer:
        companies.head(10000).to_excel(writer, sheet_name='Companies', index=False)
        facilities.head(10000).to_excel(writer, sheet_name='Facilities', index=False)
        ai_results.head(10000).to_excel(writer, sheet_name='AI Analysis', index=False)
        
        # Ajoute un résumé
        summary_df = pd.DataFrame([
            ["Date d'export", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Nombre d'entreprises", len(companies)],
            ["Nombre d'établissements", len(facilities)],
            ["Entreprises durables", ai_results['has_sustainability'].sum()],
            ["Taux de durabilité", f"{(ai_results['has_sustainability'].sum() / len(ai_results) * 100):.1f}%"],
            ["Pays couverts", len(companies['country'].unique())]
        ], columns=['Metric', 'Value'])
        
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # 4. Copie les visualisations
    print(" Copie des visualisations...")
    
    viz_dir = final_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    image_files = list(output_dir.glob("*.png"))
    for img in image_files:
        shutil.copy2(img, viz_dir / img.name)
    
    # 5. Crée un README pour l'export
    print(" Création du README...")
    
    readme_content = f"""# OAR Data Pipeline - Export Final

##  Date d'export
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

##  Données incluses

### Fichiers CSV:
1. `companies_final.csv` - {len(companies):,} entreprises
2. `facilities_final.csv` - {len(facilities):,} établissements
3. `relationships_final.csv` - {len(links):,} relations
4. `ai_analysis_final.csv` - Analyse de durabilité IA

### Fichiers structurés:
1. `data_summary.json` - Résumé JSON avec métadonnées
2. `oar_dataset.xlsx` - Dataset complet Excel

### Visualisations:
{len(image_files)} graphiques dans le dossier `visualizations/`

##  Statistiques clés

- **Entreprises totales**: {len(companies):,}
- **Établissements totaux**: {len(facilities):,}
- **Entreprises durables**: {ai_results['has_sustainability'].sum():,}
- **Taux de durabilité**: {(ai_results['has_sustainability'].sum() / len(ai_results) * 100):.1f}%
- **Pays couverts**: {len(companies['country'].unique())}

##  Pipeline Information

- **Version**: 1.0
- **Source**: Open Apparel Registry
- **Pays cibles**: Morocco, Spain, Portugal, Italy, France, Greece, Malta

##  Structure des données

### Table Companies:
- company_id: Identifiant unique
- company_name: Nom nettoyé
- country: Pays normalisé
- facility_count: Nombre d'établissements
- record_source: Source des données

### Table Facilities:
- facility_id: Identifiant unique
- facility_name: Nom de l'établissement
- latitude/longitude: Coordonnées GPS
- country/sector/address: Informations supplémentaires

### AI Analysis:
- has_sustainability: Détection de durabilité
- sustainability_score: Score IA (0-1)
- ai_summary: Résumé automatique

## 📞 Contact

Pipeline créé pour le test technique CommonShare.
Toutes les données proviennent de l'Open Apparel Registry.
"""
    
    with open(final_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n Export final créé dans: {final_dir}")
    
    # Affiche le contenu
    print("\n CONTENU DE L'EXPORT:")
    for item in final_dir.rglob("*"):
        if item.is_file():
            size = item.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024/1024:.1f} MB"
            print(f"  • {item.relative_to(final_dir)} ({size_str})")
    
    return final_dir

def generate_pipeline_report():
    """Génère un rapport du pipeline"""
    print("\n" + "="*50)
    print("📋 RAPPORT DU PIPELINE")
    print("="*50)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "pipeline_name": "OAR Data Science Pipeline",
        "status": "completed",
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "outputs": {}
    }
    
    # Compte les fichiers dans chaque dossier
    for folder in ["data/raw", "data/cleaned", "data/outputs"]:
        folder_path = Path(folder)
        if folder_path.exists():
            files = list(folder_path.glob("*"))
            report["outputs"][folder] = {
                "file_count": len(files),
                "files": [f.name for f in files[:10]]  # Premier 10 seulement
            }
    
    # Calcule les statistiques finales
    try:
        companies_path = Path("data/outputs") / "relational_companies.csv"
        if companies_path.exists():
            companies = pd.read_csv(companies_path)
            report["statistics"] = {
                "total_companies": int(len(companies)),
                "countries": int(companies['country'].nunique()),
                "avg_facilities_per_company": float(companies.get('facility_count', 1).mean())
            }
    except:
        pass
    
    # Sauvegarde le rapport
    report_path = Path("logs") / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f" Rapport sauvegardé: {report_path}")
    
    # Affiche un résumé
    print("\ RÉSUMÉ DU PIPELINE:")
    if "statistics" in report:
        stats = report["statistics"]
        print(f"  • Entreprises: {stats.get('total_companies', 0):,}")
        print(f"  • Pays: {stats.get('countries', 0)}")
        print(f"  • Établissements/entreprise: {stats.get('avg_facilities_per_company', 0):.2f}")
    
    print(f"  • Fichiers bruts: {report['outputs'].get('data/raw', {}).get('file_count', 0)}")
    print(f"  • Fichiers nettoyés: {report['outputs'].get('data/cleaned', {}).get('file_count', 0)}")
    print(f"  • Fichiers de sortie: {report['outputs'].get('data/outputs', {}).get('file_count', 0)}")
    
    return report_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*60)
    print(" EXPORT FINAL DU PIPELINE")
    print("="*60)
    
    try:
        # 1. Créer le dataset final
        export_dir = create_final_dataset()
        
        if not export_dir:
            print(" Échec de la création du dataset final")
            return False
        
        # 2. Générer le rapport
        report_path = generate_pipeline_report()
        
        print("\n" + "="*60)
        print(" EXPORT TERMINÉ AVEC SUCCÈS!")
        print("="*60)
        print(f"\n Toutes les données sont disponibles dans:")
        print(f"   • {export_dir}")
        print(f"   • {report_path}")
        print("\n Le pipeline est complet et prêt à être soumis!")
        
        return True
        
    except Exception as e:
        print(f"\n ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()