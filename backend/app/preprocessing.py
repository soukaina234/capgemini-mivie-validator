"""
Data preprocessing and cleaning functions
Handles CSV loading, encoding issues, and data standardization
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import re


def clean_encoding(text: str) -> str:
    """Fix encoding issues in text"""
    if pd.isna(text):
        return None
    
    replacements = {
        'Ã©': 'é', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã´': 'ô',
        'Ã ': 'à', 'Ã§': 'ç', 'Ã»': 'û', 'Ã®': 'î',
        'Ã¯': 'ï', 'Ã¼': 'ü', 'Cat�gorie': 'Catégorie',
        '�': 'é'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def parse_percentage(value: Any) -> float:
    """Convert percentage string to float (0-100 scale)"""
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Remove % sign and convert
    value_str = str(value).strip().replace('%', '').replace(',', '.')
    
    try:
        return float(value_str)
    except:
        return None


def parse_price(value: Any) -> float:
    """Convert price to float, handle TBD/NC"""
    if pd.isna(value):
        return 0.0
    
    value_str = str(value).strip().upper()
    
    # Handle special cases
    if value_str in ['TBD', 'TO BE DEFINED', 'NC', 'N/A', '']:
        return 0.0
    
    # Remove currency symbols and spaces
    value_str = value_str.replace('€', '').replace(',', '').strip()
    
    try:
        return float(value_str)
    except:
        return 0.0


def parse_duration(value: Any) -> float:
    """Convert duration to float, handle NC/TBD"""
    if pd.isna(value):
        return 0.0
    
    value_str = str(value).strip().upper()
    
    if value_str in ['NC', 'TBD', 'TO BE DEFINED', 'N/A', '']:
        return 0.0
    
    try:
        return float(value_str)
    except:
        return 0.0


def standardize_boolean(value: Any) -> bool:
    """Convert various boolean representations to True/False"""
    if pd.isna(value):
        return False
    
    value_str = str(value).strip().upper()
    
    # True values
    if value_str in ['X', 'OUI', 'YES', 'TRUE', '1', 'Y']:
        return True
    
    # False values
    return False


def standardize_mivie(value: Any) -> str:
    """Standardize Mi-Vie column to 'Oui'/'Non'/None"""
    if pd.isna(value):
        return None
    
    value_str = str(value).strip().upper()
    
    if value_str in ['OUI', 'YES', 'Y']:
        return 'Oui'
    elif value_str in ['NON', 'NO', 'N']:
        return 'Non'
    else:
        return None


def extract_niveau(niveau_text: str) -> str:
    """Extract niveau number (1, 2, or 3) from description"""
    if pd.isna(niveau_text):
        return None
    
    # Look for "Niveau 1", "Niveau 2", "Niveau 3"
    match = re.search(r'Niveau\s*(\d)', str(niveau_text), re.IGNORECASE)
    if match:
        return f"Niveau {match.group(1)}"
    
    return None


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main preprocessing function
    Cleans and standardizes the entire dataframe
    """
    print("🔄 Starting data preprocessing...")
    
    # Make a copy to avoid modifying original
    df = df.copy()

    df.columns = df.columns.str.strip() 
    # Column name mapping (original -> standardized)
    column_mapping = {
        'Nom de test': 'nom_de_test',
        'Catégorie de test': 'categorie_de_test',
        'Direction métier (Nomination Capgemin/MG2)': 'direction_metier',
        'Répartition (STM/ SSTM / SYNTHESE )': 'repartition',
        "Test d'homologation": 'test_homologation',
        'Pays de commercialisation': 'pays_commercialisation',
        'Prestation à valider': 'prestation',
        'Sous prestation': 'sous_prestation',
        'Catégorie du Véhicule': 'categorie_vehicule',
        'Stratégie de Validation': 'strategie_validation',
        "Pourcentage de la nécessité de la réalisation de l'essai": 'pourcentage_necessite',
        "Prix de l'essai en (€)": 'prix_euro',
        'Jalon': 'jalon',
        "Durée de l'essai (Jour)": 'duree_jours',
        "Lieu de réalisation de l'essai": 'lieu_realisation',
        "Description de l'essai": 'description_essai',
        "Test à faire dans le cadre d'une Mi-vie": 'test_mivie',
        'Zone de modification': 'zone_modification',
        'Niveau de modification': 'niveau_modification',
        'Type de moyen': 'type_moyen',
        'Moyen Dédié /Partagé': 'moyen_dedie_partage'
    }
    
    # Rename columns
    df.rename(columns=column_mapping, inplace=True)
    
    # Fix encoding for text columns
    text_columns = [
        'nom_de_test', 'categorie_de_test', 'direction_metier',
        'prestation', 'sous_prestation', 'description_essai',
        'zone_modification', 'niveau_modification'
    ]
    
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_encoding)
    
    # Parse percentage
    if 'pourcentage_necessite' in df.columns:
        df['pourcentage_necessite'] = df['pourcentage_necessite'].apply(parse_percentage)
    
    # Parse price
    if 'prix_euro' in df.columns:
        df['prix_euro'] = df['prix_euro'].apply(parse_price)
    
    # Parse duration
    if 'duree_jours' in df.columns:
        df['duree_jours'] = df['duree_jours'].apply(parse_duration)
    
    # Standardize homologation
    if 'test_homologation' in df.columns:
        df['test_homologation'] = df['test_homologation'].apply(standardize_boolean)
    
    # Standardize Mi-Vie
    if 'test_mivie' in df.columns:
        df['test_mivie'] = df['test_mivie'].apply(standardize_mivie)
    
    # Extract niveau number for easier filtering
    if 'niveau_modification' in df.columns:
        df['niveau_simple'] = df['niveau_modification'].apply(extract_niveau)
    
    # Remove completely empty rows
    df.dropna(how='all', inplace=True)
    
    # Fill NaN values appropriately
    df['prix_euro'].fillna(0.0, inplace=True)
    df['duree_jours'].fillna(0.0, inplace=True)
    df['pourcentage_necessite'].fillna(0.0, inplace=True)
       # Remove duplicate test names
    if 'nom_de_test' in df.columns:
        initial_count = len(df)

        duplicates = df['nom_de_test'].duplicated().sum()

        if duplicates > 0:
            print(f"⚠️ Found {duplicates} duplicate test names")

        df = df.drop_duplicates(
            subset=['nom_de_test'],
            keep='first'
        )

        removed_count = initial_count - len(df)

        if removed_count > 0:
            print(f"🗑️ Removed {removed_count} duplicate rows")
    # Convert NaN to None
    df = df.replace({np.nan: None})
    print(f"✅ Preprocessing complete. {len(df)} tests loaded.")

    return df
    
    
def validate_uploaded_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate uploaded CSV matches required schema
    Returns validation results with warnings/errors
    """
    required_columns = [
        'Nom de test',
        'Catégorie de test',
        "Prix de l'essai en (€)",
        "Durée de l'essai (Jour)",
        'Zone de modification',
        'Niveau de modification'
    ]
    
    errors = []
    warnings = []
    
    # Check required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for duplicate test names
    if 'Nom de test' in df.columns:
        duplicates = df['Nom de test'].duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate test names")
    
    # Check data types
    if "Prix de l'essai en (€)" in df.columns:
        try:
            pd.to_numeric(df["Prix de l'essai en (€)"], errors='coerce')
        except:
            warnings.append("Price column contains non-numeric values")
    
    # Check for excessive missing values
    missing_threshold = 0.5
    for col in df.columns:
        missing_pct = df[col].isna().sum() / len(df)
        if missing_pct > missing_threshold:
            warnings.append(f"Column '{col}' has {missing_pct*100:.1f}% missing values")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'row_count': len(df),
        'column_count': len(df.columns)
    }


def get_unique_values(df: pd.DataFrame, column: str) -> list:
    """Get unique non-null values from a column"""
    if column not in df.columns:
        return []
    
    values = df[column].dropna().unique().tolist()
    return sorted([str(v) for v in values if str(v).strip()])


def get_filter_options(df: pd.DataFrame) -> Dict[str, list]:
    """
    Extract all unique filter options from dataframe
    Used to populate frontend filter dropdowns
    """
    return {
        'vehicle_categories': get_unique_values(df, 'categorie_vehicule'),
        'markets': get_unique_values(df, 'pays_commercialisation'),
        'test_categories': get_unique_values(df, 'categorie_de_test'),
        'zones': get_unique_values(df, 'zone_modification'),
        'niveaux': ['Niveau 1', 'Niveau 2', 'Niveau 3'],
        'test_locations': get_unique_values(df, 'lieu_realisation'),
        'jalons': get_unique_values(df, 'jalon'),
        'strategies': get_unique_values(df, 'strategie_validation')
    }