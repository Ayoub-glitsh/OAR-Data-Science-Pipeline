"""
ai_module.py - Module d'Intelligence Artificielle
Option A: Détection de mots-clés de durabilité
"""
import pandas as pd
import re
import logging
from pathlib import Path
from typing import List, Dict
import numpy as np

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_companies_data():
    """Charge les données des entreprises"""
    companies_path = Path("data/outputs") / "relational_companies.csv"
    
    if not companies_path.exists():
        # Essayer le fichier nettoyé
        companies_path = Path("data/cleaned") / "companies.csv"
        if not companies_path.exists():
            raise FileNotFoundError(" Fichier des entreprises non trouvé")
    
    companies_df = pd.read_csv(companies_path)
    logging.info(f" Chargé: {len(companies_df)} entreprises")
    
    return companies_df

def detect_sustainability_keywords(company_name: str) -> Dict:
    """
    Détecte les mots-clés liés à la durabilité dans le nom de l'entreprise
    Retourne un dictionnaire avec les résultats
    """
    if pd.isna(company_name):
        return {
            'has_sustainability': False,
            'keywords_found': [],
            'sustainability_score': 0.0
        }
    
    # Liste des mots-clés de durabilité (en plusieurs langues)
    sustainability_keywords = {
        # Anglais
        'sustainable', 'green', 'eco', 'ecological', 'environment',
        'renewable', 'recycle', 'recycled', 'organic', 'natural',
        'clean', 'energy', 'carbon', 'zero waste', 'ethical',
        'fair', 'responsible', 'conscious', 'climate', 'planet',
        
        # Français
        'durable', 'vert', 'écologique', 'environnement', 'renouvelable',
        'recyclé', 'bio', 'biologique', 'naturel', 'propre',
        'énergie', 'carbone', 'zéro déchet', 'éthique', 'équitable',
        'responsable', 'climat', 'planète',
        
        # Espagnol/Portugais/Italien
        'sostenible', 'verde', 'ecologico', 'ambiental', 'renovable',
        'reciclado', 'organico', 'naturale', 'energia', 'carbono',
        'ético', 'responsable'
    }
    
    # Convertir en minuscules pour la recherche
    name_lower = str(company_name).lower()
    
    # Chercher les mots-clés
    found_keywords = []
    for keyword in sustainability_keywords:
        # Recherche de mots entiers
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, name_lower):
            found_keywords.append(keyword)
    
    # Calculer un score
    has_sustainability = len(found_keywords) > 0
    sustainability_score = min(len(found_keywords) / 5, 1.0)  # Score entre 0 et 1
    
    return {
        'has_sustainability': has_sustainability,
        'keywords_found': found_keywords,
        'sustainability_score': sustainability_score,
        'keyword_count': len(found_keywords)
    }

def generate_company_summary(company_row: pd.Series) -> str:
    """
    Génère un résumé automatique pour une entreprise
    """
    company_name = company_row.get('company_name', 'Unknown Company')
    country = company_row.get('country', 'Unknown Country')
    facility_count = company_row.get('facility_count', 0)
    
    # Détecte la durabilité
    sustainability_info = detect_sustainability_keywords(company_name)
    
    # Construit le résumé
    parts = []
    
    # Partie 1: Description de base
    if facility_count > 0:
        parts.append(f"{company_name} est une entreprise basée en {country} avec {facility_count} établissement(s).")
    else:
        parts.append(f"{company_name} est une entreprise basée en {country}.")
    
    # Partie 2: Durabilité
    if sustainability_info['has_sustainability']:
        if sustainability_info['keyword_count'] == 1:
            parts.append(f"Elle semble engagée dans la durabilité (mot-clé: {sustainability_info['keywords_found'][0]}).")
        else:
            keywords_str = ', '.join(sustainability_info['keywords_found'][:3])
            parts.append(f"Elle montre un fort engagement envers la durabilité (mots-clés: {keywords_str}).")
    else:
        parts.append("Aucune mention explicite de durabilité dans le nom de l'entreprise.")
    
    return ' '.join(parts)

def analyze_companies(companies_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyse toutes les entreprises avec l'IA
    """
    print("\n" + "="*50)
    print(" ANALYSE IA DES ENTREPRISES")
    print("="*50)
    
    results = []
    
    print(f" Analyse de {len(companies_df)} entreprises...")
    
    for idx, row in companies_df.iterrows():
        # Analyse de durabilité
        sustainability = detect_sustainability_keywords(row.get('company_name', ''))
        
        # Génération de résumé
        summary = generate_company_summary(row)
        
        # Crée le résultat
        result = {
            'company_id': row.get('company_id', f'COMP_{idx}'),
            'company_name': row.get('company_name', 'Unknown'),
            'country': row.get('country', 'Unknown'),
            'has_sustainability': sustainability['has_sustainability'],
            'sustainability_score': sustainability['sustainability_score'],
            'keywords_found': ';'.join(sustainability['keywords_found']),
            'keyword_count': sustainability['keyword_count'],
            'ai_summary': summary,
            'facility_count': row.get('facility_count', 0)
        }
        
        results.append(result)
        
        # Affiche la progression
        if (idx + 1) % 1000 == 0:
            print(f"  Traité {idx + 1}/{len(companies_df)} entreprises")
    
    # Crée le DataFrame des résultats
    results_df = pd.DataFrame(results)
    
    # Statistiques
    sustainable_companies = results_df['has_sustainability'].sum()
    sustainability_rate = (sustainable_companies / len(results_df)) * 100
    
    print(f"\n RÉSULTATS DE L'ANALYSE IA:")
    print(f"  Entreprises analysées: {len(results_df):,}")
    print(f"  Entreprises durables détectées: {sustainable_companies:,}")
    print(f"  Taux de durabilité: {sustainability_rate:.1f}%")
    print(f"  Score moyen de durabilité: {results_df['sustainability_score'].mean():.3f}")
    
    # Top des mots-clés
    all_keywords = []
    for keywords in results_df['keywords_found']:
        if pd.notna(keywords) and keywords != '':
            all_keywords.extend(keywords.split(';'))
    
    if all_keywords:
        keyword_counts = pd.Series(all_keywords).value_counts()
        print(f"\n TOP 10 MOTS-CLÉS DE DURABILITÉ:")
        for keyword, count in keyword_counts.head(10).items():
            print(f"  {keyword:20} : {count:5,}")
    
    return results_df

def save_ai_results(results_df: pd.DataFrame):
    """Sauvegarde les résultats de l'IA"""
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Fichier complet
    full_path = output_dir / "ai_analysis_full.csv"
    results_df.to_csv(full_path, index=False, encoding='utf-8')
    
    # 2. Fichier simplifié (pour visualisation)
    simple_cols = ['company_id', 'company_name', 'country', 'has_sustainability',
                   'sustainability_score', 'ai_summary']
    simple_df = results_df[simple_cols].copy()
    simple_path = output_dir / "ai_analysis_simple.csv"
    simple_df.to_csv(simple_path, index=False, encoding='utf-8')
    
    # 3. Statistiques
    stats = {
        'total_companies': len(results_df),
        'sustainable_companies': int(results_df['has_sustainability'].sum()),
        'sustainability_rate': float(results_df['has_sustainability'].mean() * 100),
        'avg_sustainability_score': float(results_df['sustainability_score'].mean()),
        'top_country_sustainability': results_df[results_df['has_sustainability']]
                                      .groupby('country').size().idxmax()
                                      if len(results_df[results_df['has_sustainability']]) > 0 else 'N/A'
    }
    
    stats_df = pd.DataFrame([stats])
    stats_path = output_dir / "ai_statistics.csv"
    stats_df.to_csv(stats_path, index=False)
    
    print(f"\n RÉSULTATS SAUVEGARDÉS:")
    print(f"  • {full_path}")
    print(f"  • {simple_path}")
    print(f"  • {stats_path}")
    
    # Affiche un échantillon
    print("\n ÉCHANTILLON DES RÉSULTATS IA:")
    print(results_df.head(5).to_string(index=False))
    
    return full_path, simple_path, stats_path

def create_sustainability_report(results_df: pd.DataFrame):
    """Crée un rapport sur la durabilité"""
    print("\n CRÉATION DU RAPPORT DE DURABILITÉ...")
    
    # Entreprises les plus durables
    top_sustainable = results_df.nlargest(10, 'sustainability_score')[
        ['company_name', 'country', 'sustainability_score', 'keywords_found']
    ]
    
    # Par pays
    sustainability_by_country = results_df.groupby('country').agg({
        'has_sustainability': 'mean',
        'sustainability_score': 'mean',
        'company_id': 'count'
    }).rename(columns={
        'has_sustainability': 'sustainability_rate',
        'company_id': 'total_companies'
    })
    
    sustainability_by_country['sustainability_rate'] *= 100
    
    # Sauvegarde les rapports
    output_dir = Path("data/outputs")
    
    top_sustainable_path = output_dir / "top_sustainable_companies.csv"
    top_sustainable.to_csv(top_sustainable_path, index=False)
    
    country_sustainability_path = output_dir / "sustainability_by_country.csv"
    sustainability_by_country.to_csv(country_sustainability_path)
    
    print(f"\n RAPPORT PAR PAYS:")
    print(sustainability_by_country.sort_values('sustainability_rate', ascending=False)
          .head(10).to_string())
    
    print(f"\n TOP 10 ENTREPRISES LES PLUS DURABLES:")
    print(top_sustainable.to_string(index=False))
    
    return top_sustainable_path, country_sustainability_path

def main():
    """Fonction principale"""
    setup_logging()
    
    print("\n" + "="*60)
    print(" DÉMARRAGE DU MODULE D'INTELLIGENCE ARTIFICIELLE")
    print("="*60)
    
    try:
        # 1. Charger les données
        companies_df = load_companies_data()
        
        # 2. Analyser avec l'IA
        ai_results = analyze_companies(companies_df)
        
        # 3. Sauvegarder les résultats
        save_ai_results(ai_results)
        
        # 4. Créer des rapports supplémentaires
        create_sustainability_report(ai_results)
        
        print("\n" + "="*60)
        print(" ANALYSE IA TERMINÉE AVEC SUCCÈS!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()