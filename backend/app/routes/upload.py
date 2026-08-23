"""
Data Upload API endpoints
Handles partial CSV uploads with duplicate checking
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import pandas as pd
import io
from typing import Dict, Any

from app.database import get_db
from app.models import Test
from app.preprocessing import preprocess_dataframe, validate_uploaded_data

router = APIRouter()


@router.post("/csv")
async def upload_test_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload partial test data CSV
    
    - Validates column structure
    - Checks for duplicates by 'nom_de_test'
    - Updates existing tests or inserts new ones
    
    Returns:
    - new_tests: Number of new tests added
    - updated_tests: Number of tests updated
    - errors: List of validation errors
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV (.csv extension)"
        )
    
    try:
        # Read CSV content
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
        
    except UnicodeDecodeError:
        # Try alternative encoding
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding='iso-8859-1')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read CSV file: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV: {str(e)}"
        )
    
    # Validate data structure
    validation_result = validate_uploaded_data(df)
    
    if not validation_result['valid']:
        return {
            'success': False,
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings']
        }
    
    # Preprocess data
    try:
        df = preprocess_dataframe(df)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Data preprocessing failed: {str(e)}"
        )
    
    # Get existing test names
    existing_tests = db.query(Test.nom_de_test).all()
    existing_names = {t[0] for t in existing_tests}
    
    # Separate new and existing tests
    df['is_new'] = ~df['nom_de_test'].isin(existing_names)
    new_tests_df = df[df['is_new'] == True].copy()
    updated_tests_df = df[df['is_new'] == False].copy()
    
    new_count = 0
    updated_count = 0
    errors = []
    
    # Insert new tests
    if len(new_tests_df) > 0:
        try:
            for _, row in new_tests_df.iterrows():
                test = Test(
                    nom_de_test=row.get('nom_de_test'),
                    categorie_de_test=row.get('categorie_de_test'),
                    direction_metier=row.get('direction_metier'),
                    repartition=row.get('repartition'),
                    test_homologation=row.get('test_homologation', False),
                    pays_commercialisation=row.get('pays_commercialisation'),
                    prestation=row.get('prestation'),
                    sous_prestation=row.get('sous_prestation'),
                    categorie_vehicule=row.get('categorie_vehicule'),
                    strategie_validation=row.get('strategie_validation'),
                    pourcentage_necessite=row.get('pourcentage_necessite'),
                    prix_euro=row.get('prix_euro'),
                    jalon=row.get('jalon'),
                    duree_jours=row.get('duree_jours'),
                    lieu_realisation=row.get('lieu_realisation'),
                    description_essai=row.get('description_essai'),
                    test_mivie=row.get('test_mivie'),
                    zone_modification=row.get('zone_modification'),
                    niveau_modification=row.get('niveau_modification'),
                    type_moyen=row.get('type_moyen'),
                    moyen_dedie_partage=row.get('moyen_dedie_partage')
                )
                db.add(test)
                new_count += 1
            
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f"Failed to insert new tests: {str(e)}")
    
    # Update existing tests
    if len(updated_tests_df) > 0:
        try:
            for _, row in updated_tests_df.iterrows():
                test = db.query(Test).filter(
                    Test.nom_de_test == row.get('nom_de_test')
                ).first()
                
                if test:
                    # Update fields
                    test.categorie_de_test = row.get('categorie_de_test')
                    test.prix_euro = row.get('prix_euro')
                    test.duree_jours = row.get('duree_jours')
                    test.zone_modification = row.get('zone_modification')
                    test.niveau_modification = row.get('niveau_modification')
                    test.pourcentage_necessite = row.get('pourcentage_necessite')
                    # ... update other fields as needed
                    
                    updated_count += 1
            
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f"Failed to update tests: {str(e)}")
    
    # Get final test count
    total_tests_now = db.query(Test).count()
    
    return {
        'success': len(errors) == 0,
        'new_tests': new_count,
        'updated_tests': updated_count,
        'total_tests_now': total_tests_now,
        'warnings': validation_result['warnings'],
        'errors': errors
    }


@router.get("/template")
def download_csv_template():
    """
    Download CSV template with correct column structure
    """
    template_columns = [
        'Nom de test',
        'Catégorie de test',
        'Direction métier (Nomination Capgemin/MG2)',
        'Répartition (STM/ SSTM / SYNTHESE )',
        "Test d'homologation",
        'Pays de commercialisation',
        'Prestation à valider',
        'Sous prestation',
        'Catégorie du Véhicule',
        'Stratégie de Validation',
        "Pourcentage de la nécessité de la réalisation de l'essai",
        "Prix de l'essai en (€)",
        'Jalon',
        "Durée de l'essai (Jour)",
        "Lieu de réalisation de l'essai",
        "Description de l'essai",
        "Test à faire dans le cadre d'une Mi-vie",
        'Zone de modification',
        'Niveau de modification',
        'Type de moyen',
        'Moyen Dédié /Partagé'
    ]
    
    return {
        'columns': template_columns,
        'example_row': {
            'Nom de test': 'Example Test Name',
            'Catégorie de test': 'OPTIMIZE CONSUMPTION',
            "Test d'homologation": 'X',
            'Pays de commercialisation': 'Europe',
            "Prix de l'essai en (€)": '5000',
            "Durée de l'essai (Jour)": '10',
            'Zone de modification': 'Face avant',
            'Niveau de modification': 'Niveau 1',
            "Test à faire dans le cadre d'une Mi-vie": 'Oui'
        },
        'notes': [
            "All columns are required",
            "Use 'X' for homologation tests",
            "Price should be numeric (without currency symbol)",
            "Duration should be numeric (in days)",
            "Mi-vie column should be 'Oui' or 'Non'",
            "Test name must be unique (used to detect duplicates)"
        ]
    }


@router.get("/validation-rules")
def get_validation_rules():
    """
    Return validation rules for CSV uploads
    Helps users prepare their data correctly
    """
    return {
        'required_columns': [
            'Nom de test',
            'Catégorie de test',
            "Prix de l'essai en (€)",
            "Durée de l'essai (Jour)",
            'Zone de modification',
            'Niveau de modification'
        ],
        'data_types': {
            'Nom de test': 'text (unique)',
            "Prix de l'essai en (€)": 'numeric (or TBD/NC)',
            "Durée de l'essai (Jour)": 'numeric (or TBD/NC)',
            "Pourcentage de la nécessité": 'numeric (0-100 or percentage)',
            "Test d'homologation": 'X or empty',
            "Test à faire dans le cadre d'une Mi-vie": 'Oui/Non/OUI'
        },
        'special_values': {
            'TBD': 'To be defined (converted to 0)',
            'NC': 'Not communicated (converted to 0)',
            'X': 'Marks homologation test',
            'Oui/OUI': 'Yes for Mi-vie applicability',
            'Non': 'No for Mi-vie applicability'
        },
        'duplicate_handling': 'Tests with same name will be updated, not duplicated'
    }