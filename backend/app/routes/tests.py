"""
Tests API endpoints
Handles test catalog retrieval and filtering
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from app.database import get_db
from app.models import Test
from app.preprocessing import get_filter_options
import pandas as pd

router = APIRouter()


@router.get("/")
def get_tests(
    db: Session = Depends(get_db),
    # Filters
    mivie: Optional[str] = Query(None, description="Oui/Non"),
    vehicle_category: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
    zone: Optional[str] = Query(None),
    niveau: Optional[str] = Query(None, description="Niveau 1/2/3"),
    test_category: Optional[str] = Query(None),
    homologation_only: bool = Query(False),
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get filtered list of tests
    
    Example:
        GET /api/tests?mivie=Oui&zone=Face avant&vehicle_category=M1
    """
    query = db.query(Test)
    
    # Apply filters
    if mivie:
        query = query.filter(Test.test_mivie == mivie)
    
    if vehicle_category:
        query = query.filter(Test.categorie_vehicule.contains(vehicle_category))
    
    if market:
        query = query.filter(Test.pays_commercialisation.contains(market))
    
    if zone:
        query = query.filter(Test.zone_modification.contains(zone))
    
    if niveau:
        query = query.filter(Test.niveau_modification.contains(niveau))
    
    if test_category:
        query = query.filter(Test.categorie_de_test == test_category)
    
    if homologation_only:
        query = query.filter(Test.test_homologation == True)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    tests = query.offset(skip).limit(limit).all()
    
    # Convert to dict
    results = [
        {
            'id': t.id,
            'nom_de_test': t.nom_de_test,
            'categorie_de_test': t.categorie_de_test,
            'test_homologation': t.test_homologation,
            'prix_euro': float(t.prix_euro) if t.prix_euro else 0,
            'duree_jours': float(t.duree_jours) if t.duree_jours else 0,
            'pourcentage_necessite': float(t.pourcentage_necessite) if t.pourcentage_necessite else 0,
            'zone_modification': t.zone_modification,
            'niveau_modification': t.niveau_modification,
            'test_mivie': t.test_mivie,
            'lieu_realisation': t.lieu_realisation,
            'strategie_validation': t.strategie_validation
        }
        for t in tests
    ]
    
    return {
        'total': total_count,
        'skip': skip,
        'limit': limit,
        'tests': results
    }


@router.get("/filter-options")
def get_available_filters(db: Session = Depends(get_db)):
    """
    Get all available filter options
    Used to populate filter dropdowns in frontend
    """
    # Get all tests as dataframe
    tests = db.query(Test).all()
    
    df = pd.DataFrame([
        {
            'categorie_vehicule': t.categorie_vehicule,
            'pays_commercialisation': t.pays_commercialisation,
            'categorie_de_test': t.categorie_de_test,
            'zone_modification': t.zone_modification,
            'niveau_modification': t.niveau_modification,
            'lieu_realisation': t.lieu_realisation,
            'jalon': t.jalon,
            'strategie_validation': t.strategie_validation
        }
        for t in tests
    ])
    
    from app.preprocessing import get_filter_options
    return get_filter_options(df)


@router.get("/{test_id}")
def get_test_by_id(test_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific test
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found")
    
    return {
        'id': test.id,
        'nom_de_test': test.nom_de_test,
        'categorie_de_test': test.categorie_de_test,
        'direction_metier': test.direction_metier,
        'repartition': test.repartition,
        'test_homologation': test.test_homologation,
        'pays_commercialisation': test.pays_commercialisation,
        'prestation': test.prestation,
        'sous_prestation': test.sous_prestation,
        'categorie_vehicule': test.categorie_vehicule,
        'strategie_validation': test.strategie_validation,
        'pourcentage_necessite': float(test.pourcentage_necessite) if test.pourcentage_necessite else 0,
        'prix_euro': float(test.prix_euro) if test.prix_euro else 0,
        'jalon': test.jalon,
        'duree_jours': float(test.duree_jours) if test.duree_jours else 0,
        'lieu_realisation': test.lieu_realisation,
        'description_essai': test.description_essai,
        'test_mivie': test.test_mivie,
        'zone_modification': test.zone_modification,
        'niveau_modification': test.niveau_modification,
        'type_moyen': test.type_moyen,
        'moyen_dedie_partage': test.moyen_dedie_partage,
        'created_at': test.created_at.isoformat() if test.created_at else None
    }


@router.get("/stats/summary")
def get_test_statistics(db: Session = Depends(get_db)):
    """
    Get overall test catalog statistics
    """
    total_tests = db.query(Test).count()
    homologation_tests = db.query(Test).filter(Test.test_homologation == True).count()
    mivie_tests = db.query(Test).filter(Test.test_mivie == 'Oui').count()
    
    # Average cost and duration
    from sqlalchemy import func
    avg_cost = db.query(func.avg(Test.prix_euro)).filter(Test.prix_euro > 0).scalar() or 0
    avg_duration = db.query(func.avg(Test.duree_jours)).filter(Test.duree_jours > 0).scalar() or 0
    
    return {
        'total_tests': total_tests,
        'homologation_tests': homologation_tests,
        'mivie_applicable_tests': mivie_tests,
        'avg_test_cost_euro': float(avg_cost),
        'avg_test_duration_days': float(avg_duration)
    }