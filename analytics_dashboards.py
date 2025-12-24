"""
analytics_dashboards.py - Génère des visualisations analytiques
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import logging
from pathlib import Path
import numpy as np

# Configure pour de meilleurs graphiques
matplotlib.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_relational_data():
    """Charge les données relationnelles"""
    output_dir = Path("data/outputs")
    
    # Vérifie les fichiers
    required_files = ['relational_companies.csv', 'relational_facilities.csv']
    for file in required_files:
        if not (output_dir / file).exists():
            raise FileNotFoundError(f" Fichier manquant: {file}")
    
    companies = pd.read_csv(output_dir / "relational_companies.csv")
    facilities = pd.read_csv(output_dir / "relational_facilities.csv")
    
    logging.info(f" Données chargées: {len(companies)} entreprises, {len(facilities)} établissements")
    
    return companies, facilities

def create_companies_by_country_chart(companies_df):
    """Crée le graphique des entreprises par pays"""
    print("\n Création du graphique 'Entreprises par pays'...")
    
    # Calcule les comptes
    country_counts = companies_df['country'].value_counts().sort_values(ascending=False)
    
    # Crée le graphique
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 1. Diagramme à barres
    colors = plt.cm.Set3(np.arange(len(country_counts)) / len(country_counts))
    bars = ax1.bar(country_counts.index, country_counts.values, color=colors, edgecolor='black')
    
    ax1.set_title('Nombre d\'Entreprises par Pays', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Pays', fontsize=12)
    ax1.set_ylabel('Nombre d\'Entreprises', fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    
    # Ajoute les valeurs sur les barres
    for bar, value in zip(bars, country_counts.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(country_counts.values)*0.01,
                f'{value:,}', ha='center', va='bottom', fontsize=10)
    
    # 2. Diagramme circulaire
    ax2.pie(country_counts.values, labels=country_counts.index, autopct='%1.1f%%',
           startangle=90, colors=colors, textprops={'fontsize': 10})
    ax2.set_title('Répartition par Pays (%)', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    # Sauvegarde
    output_path = Path("data/outputs") / "companies_by_country.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f" Graphique sauvegardé: {output_path}")
    
    # Affiche les données
    print("\n DONNÉES 'Entreprises par pays':")
    print(country_counts.to_string())
    
    return output_path

def create_facilities_per_company_chart(companies_df):
    """Crée le graphique des établissements par entreprise"""
    print("\n Création du graphique 'Établissements par entreprise'...")
    
    # Utilise la colonne facility_count créée précédemment
    if 'facility_count' not in companies_df.columns:
        print("  Colonne 'facility_count' non trouvée, calcul...")
        # Charge les liens si nécessaire
        links_path = Path("data/outputs") / "relational_links.csv"
        if links_path.exists():
            links = pd.read_csv(links_path)
            facility_counts = links.groupby('company_id').size()
            companies_df = companies_df.merge(
                facility_counts.rename('facility_count'),
                left_on='company_id',
                right_index=True,
                how='left'
            )
            companies_df['facility_count'] = companies_df['facility_count'].fillna(0).astype(int)
        else:
            print(" Impossible de créer le graphique: données manquantes")
            return None
    
    # Crée le graphique
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 1. Histogramme
    counts = companies_df['facility_count']
    
    # Détermine les bins intelligemment
    max_val = counts.max()
    if max_val <= 10:
        bins = range(0, max_val + 2)
    else:
        bins = 20
    
    n, bins, patches = ax1.hist(counts, bins=bins, color='lightcoral',
                                edgecolor='darkred', alpha=0.7)
    
    ax1.set_title('Distribution des Établissements par Entreprise',
                 fontsize=14, fontweight='bold')
    ax1.set_xlabel('Nombre d\'Établissements', fontsize=12)
    ax1.set_ylabel('Nombre d\'Entreprises', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Ajoute des statistiques
    mean_val = counts.mean()
    median_val = counts.median()
    
    ax1.axvline(mean_val, color='blue', linestyle='--', linewidth=2,
               label=f'Moyenne: {mean_val:.2f}')
    ax1.axvline(median_val, color='green', linestyle='--', linewidth=2,
               label=f'Médiane: {median_val:.0f}')
    ax1.legend()
    
    # 2. Box plot
    ax2.boxplot(counts, vert=True, patch_artist=True,
               boxprops=dict(facecolor='lightblue', color='darkblue'),
               medianprops=dict(color='red', linewidth=2))
    ax2.set_title('Distribution (Box Plot)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Nombre d\'Établissements', fontsize=12)
    ax2.set_xticklabels([''])
    
    # Ajoute des annotations
    stats_text = f"""Statistiques:
    Moyenne: {mean_val:.2f}
    Médiane: {median_val:.0f}
    Maximum: {counts.max():.0f}
    Écart-type: {counts.std():.2f}
    Total établissements: {counts.sum():,}"""
    
    ax2.text(0.95, 0.95, stats_text, transform=ax2.transAxes,
            fontsize=10, verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Sauvegarde
    output_path = Path("data/outputs") / "facilities_per_company.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f" Graphique sauvegardé: {output_path}")
    
    # Affiche les statistiques
    print("\n STATISTIQUES 'Établissements par entreprise':")
    print(f"  Total entreprises: {len(counts):,}")
    print(f"  Moyenne: {mean_val:.2f}")
    print(f"  Médiane: {median_val}")
    print(f"  Maximum: {counts.max()}")
    print(f"  Minimum: {counts.min()}")
    print(f"  Entreprises avec 1 établissement: {(counts == 1).sum():,}")
    print(f"  Entreprises avec >5 établissements: {(counts > 5).sum():,}")
    
    return output_path

def create_sector_analysis(facilities_df):
    """Analyse par secteur d'activité"""
    print("\n Analyse par secteur d'activité...")
    
    if 'sector' not in facilities_df.columns:
        print("  Colonne 'sector' non trouvée")
        return None
    
    # Nettoie les secteurs
    facilities_df['sector_clean'] = facilities_df['sector'].fillna('Unknown')
    facilities_df['sector_clean'] = facilities_df['sector_clean'].str.strip().str.title()
    
    # Compte par secteur
    sector_counts = facilities_df['sector_clean'].value_counts().head(10)
    
    if len(sector_counts) == 0:
        print(" Aucune donnée de secteur disponible")
        return None
    
    # Crée le graphique
    plt.figure(figsize=(14, 8))
    
    colors = plt.cm.tab20c(np.arange(len(sector_counts)) / len(sector_counts))
    bars = plt.barh(sector_counts.index, sector_counts.values, color=colors, edgecolor='black')
    
    plt.title('Top 10 des Secteurs d\'Activité', fontsize=16, fontweight='bold')
    plt.xlabel('Nombre d\'Établissements', fontsize=12)
    plt.ylabel('Secteur', fontsize=12)
    
    # Ajoute les valeurs
    for bar, value in zip(bars, sector_counts.values):
        plt.text(bar.get_width() + max(sector_counts.values)*0.01,
                bar.get_y() + bar.get_height()/2,
                f'{value:,}', va='center', fontsize=10)
    
    plt.tight_layout()
    
    # Sauvegarde
    output_path = Path("data/outputs") / "sector_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f" Graphique sauvegardé: {output_path}")
    
    # Affiche les données
    print("\n TOP 10 SECTEURS:")
    print(sector_counts.to_string())
    
    return output_path

def create_summary_report(companies_df, facilities_df):
    """Crée un rapport sommaires"""
    print("\n CRÉATION DU RAPPORT SOMMAIRE...")
    
    # Calcule les statistiques
    stats = {
        'total_companies': len(companies_df),
        'total_facilities': len(facilities_df),
        'countries_covered': companies_df['country'].nunique(),
        'avg_facilities_per_company': companies_df.get('facility_count', pd.Series([0])).mean(),
        'companies_with_multiple_facilities': (companies_df.get('facility_count', pd.Series([0])) > 1).sum(),
        'top_country': companies_df['country'].value_counts().index[0] if len(companies_df) > 0 else 'N/A',
        'top_sector': facilities_df['sector'].value_counts().index[0] if 'sector' in facilities_df.columns and len(facilities_df) > 0 else 'N/A'
    }
    
    # Crée un DataFrame pour les statistiques
    stats_df = pd.DataFrame({
        'Metric': list(stats.keys()),
        'Value': list(stats.values())
    })
    
    # Sauvegarde
    output_path = Path("data/outputs") / "analytics_summary.csv"
    stats_df.to_csv(output_path, index=False)
    
    print(f" Rapport sauvegardé: {output_path}")
    
    # Affiche le rapport
    print("\n" + "="*50)
    print(" RAPPORT ANALYTIQUE SOMMAIRE")
    print("="*50)
    for key, value in stats.items():
        label = key.replace('_', ' ').title()
        if isinstance(value, float):
            print(f"{label:40} : {value:>10.2f}")
        else:
            print(f"{label:40} : {value:>10}")
    print("="*50)
    
    return output_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*60)
    print(" DÉMARRAGE DE L'ANALYSE ET DES VISUALISATIONS")
    print("="*60)
    
    try:
        # 1. Charger les données
        companies_df, facilities_df = load_relational_data()
        
        print(f"\n📁 Données chargées avec succès:")
        print(f"   - {len(companies_df):,} entreprises")
        print(f"   - {len(facilities_df):,} établissements")
        
        # 2. Créer les visualisations
        print("\n CRÉATION DES VISUALISATIONS...")
        
        # Graphique 1
        chart1 = create_companies_by_country_chart(companies_df)
        
        # Graphique 2
        chart2 = create_facilities_per_company_chart(companies_df)
        
        # Graphique 3 (optionnel)
        chart3 = create_sector_analysis(facilities_df)
        
        # 3. Créer le rapport
        report = create_summary_report(companies_df, facilities_df)
        
        # 4. Afficher la liste des fichiers créés
        print("\n" + "="*60)
        print(" FICHIERS CRÉÉS:")
        print("="*60)
        outputs_dir = Path("data/outputs")
        image_files = list(outputs_dir.glob("*.png"))
        csv_files = list(outputs_dir.glob("*.csv"))
        
        print("\n IMAGES:")
        for img in sorted(image_files):
            print(f"  • {img.name}")
        
        print("\n DONNÉES:")
        for csv in sorted(csv_files):
            print(f"  • {csv.name}")
        
        print("\n" + "="*60)
        print("ANALYSE TERMINÉE AVEC SUCCÈS!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()