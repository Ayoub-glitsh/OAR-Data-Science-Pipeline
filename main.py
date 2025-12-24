"""
main.py - Orchestrateur principal du pipeline
"""
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime
import time

def setup_logging():
    """Configure le logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_phase(script_name, phase_name, timeout=600):
    """Exécute une phase du pipeline"""
    logging.info(f"PHASE: {phase_name}")
    logging.info(f"Execution de: {script_name}")
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            logging.info(f"[OK] {phase_name} termine avec succes")
            logging.info(f"Durée: {duration:.1f} secondes")
            
            # Affiche la sortie si intéressante
            if result.stdout and len(result.stdout) > 100:
                logging.info(f"Sortie (extrait): {result.stdout[:500]}...")
            
            return True
        else:
            logging.error(f"[ERREUR] {phase_name} a echoue")
            logging.error(f"Code de sortie: {result.returncode}")
            logging.error(f"Erreur: {result.stderr[:1000]}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"[TIMEOUT] {phase_name} timeout apres {timeout} secondes")
        return False
    except Exception as e:
        logging.error(f"[EXCEPTION] {phase_name} exception: {e}")
        return False

def check_prerequisites():
    """Vérifie les prérequis"""
    logging.info("Verification des prerequis...")
    
    # Vérifie Python
    try:
        import pandas
        import requests
        import matplotlib
        logging.info("Toutes les dependances Python sont installees")
    except ImportError as e:
        logging.error(f"Dependance manquante: {e}")
        logging.info("Execute: pip install -r requirements.txt")
        return False
    
    # Vérifie les dossiers
    required_dirs = ["data/raw", "data/cleaned", "data/outputs", "logs"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            logging.warning(f"Dossier manquant: {dir_path}")
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logging.info(f"Dossier cree: {dir_path}")
    
    return True

def display_banner():
    """Affiche une bannière de démarrage"""
    banner = """
    ======================================================
    
       OAR DATA SCIENCE PIPELINE - COMMONSHARE TEST
    
       Version: 1.0
       Auteur: Ayoub Aguezar
       Date: {timestamp}
    
    ======================================================
    """
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(banner.format(timestamp=timestamp))

def main():
    """Fonction principale"""
    display_banner()
    setup_logging()
    
    logging.info("=" * 70)
    logging.info("DEMARRAGE DU PIPELINE DE DONNEES OAR")
    logging.info("=" * 70)
    
    # Vérifie les prérequis
    if not check_prerequisites():
        logging.error("Prerequis non satisfaits. Arret.")
        return False
    
    # Définit l'ordre des phases
    phases = [
        ("scrape_oar.py", "1. Extraction des données OAR"),
        ("clean_companies.py", "2. Nettoyage des entreprises"),
        ("clean_facilities.py", "3. Traitement des établissements"),
        ("relational_builder.py", "4. Construction relationnelle"),
        ("analytics_dashboards.py", "5. Analyse et visualisation"),
        ("ai_module.py", "6. Module d'Intelligence Artificielle"),
        ("export_final.py", "7. Export final")
    ]
    
    # Exécute chaque phase
    results = {}
    
    for script, phase_name in phases:
        success = run_phase(script, phase_name)
        results[phase_name] = success
        
        if not success:
            logging.warning(f"La phase {phase_name} a echoue")
            choice = input(f"\n[ERREUR] {phase_name} a echoue. Continuer malgre tout? (o/n): ")
            if choice.lower() != 'o':
                logging.error("Pipeline arrete par l'utilisateur")
                break
    
    # Résumé final
    logging.info("\n" + "=" * 70)
    logging.info("RESUME DU PIPELINE")
    logging.info("=" * 70)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for phase, success in results.items():
        status = "[OK]" if success else "[ECHEC]"
        logging.info(f"{status} {phase}")
    
    logging.info("\n" + "=" * 70)
    logging.info(f"COMPLETION: {successful}/{total} phases reussies")
    
    if successful == total:
        logging.info("FELICITATIONS! Le pipeline s'est execute avec succes!")
        logging.info("Les resultats sont dans: final_export/ et data/outputs/")
    else:
        logging.warning(f"{total - successful} phases ont echoue")
    
    logging.info("=" * 70)
    
    return successful == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nPipeline interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\nERREUR INATTENDUE: {e}")
        sys.exit(1)