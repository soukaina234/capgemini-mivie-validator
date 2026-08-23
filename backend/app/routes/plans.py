"""
Validation Plans API endpoints
Handles plan creation, scoring, and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import Test, ValidationPlan, PlanTest
from app.scoring import (
    TestInfo, PlanConstraints, calculate_complete_score,
    calculate_timelines, determine_feasibility_status,
    get_missing_mandatory_tests, suggest_optional_improvements,
    calculate_tier_distribution, calculate_cost_breakdown
)
from app.strategies import (
    StrategyType, select_tests_by_strategy,
    get_strategy_description, compare_strategies
)

router = APIRouter()


# Pydantic models for request/response
class CreatePlanRequest(BaseModel):
    plan_name: str
    vehicle_category: str
    is_mivie: bool
    modification_zones: List[str]
    modification_level: str  # "Niveau 1", "Niveau 2", "Niveau 3"
    target_markets: List[str]
    max_budget: Optional[float] = None
    max_duration: Optional[int] = None
    strategy_type: str = "balanced"  # minimum, balanced, comprehensive, custom
    custom_preferences: Optional[Dict[str, Any]] = None


@router.post("/create")
def create_validation_plan(
    request: CreatePlanRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new validation plan with automatic test selection
    
    Steps:
    1. Filter available tests based on criteria
    2. Apply selected strategy
    3. Calculate scoring
    4. Save to database
    5. Return complete plan with recommendations
    """
    
    # Step 1: Get all available tests
    query = db.query(Test)
    
    # Filter by Mi-Vie if applicable
    if request.is_mivie:
        query = query.filter(Test.test_mivie == 'Oui')
    
    # Filter by vehicle category
    if request.vehicle_category and request.vehicle_category != 'Toutes catégories':
        query = query.filter(Test.categorie_vehicule.contains(request.vehicle_category))

    # Filter by target markets (if not "Toutes destinations")
    if request.target_markets and 'Toutes destinations' not in request.target_markets:
        # At least one market must match
        market_filters = []
        for market in request.target_markets:
            market_filters.append(Test.pays_commercialisation.contains(market))
        if market_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*market_filters))
    
    available_tests = query.all()
    
    if not available_tests:
        raise HTTPException(
            status_code=404,
            detail="No tests found matching the specified criteria"
        )
    print(f"✅ Found {len(available_tests)} tests matching initial filters")
    # Convert to dict for strategy processing
    tests_dict = [
        {
            'id': t.id,
            'nom_de_test': t.nom_de_test,
            'categorie_de_test': t.categorie_de_test,
            'test_homologation': t.test_homologation,
            'prix_euro': float(t.prix_euro) if t.prix_euro else 0,
            'duree_jours': float(t.duree_jours) if t.duree_jours else 0,
            'zone_modification': t.zone_modification,
            'niveau_modification': t.niveau_modification,
            'pourcentage_necessite': float(t.pourcentage_necessite) if t.pourcentage_necessite else 0,
            'strategie_validation': t.strategie_validation, 
            'pays_commercialisation': t.pays_commercialisation
        } 
        for t in available_tests
    ]
    
    # Step 2: Apply strategy
    constraints = PlanConstraints(
        max_budget=request.max_budget,
        max_duration=request.max_duration,
        required_zones=request.modification_zones,
        target_markets=request.target_markets
    )
    # DEBUG: Print what we're sending to strategies
    print(f"\n{'='*60}")
    print(f"🔍 Creating plan with constraints:")
    print(f"   max_budget from request: {request.max_budget} (type: {type(request.max_budget)})")
    print(f"   max_duration from request: {request.max_duration} (type: {type(request.max_duration)})")
    print(f"   Constraints object created:")
    print(f"      - max_budget: {constraints.max_budget}")
    print(f"      - max_duration: {constraints.max_duration}")
    print(f"      - required_zones: {constraints.required_zones}")
    print(f"{'='*60}\n")
    try:
        strategy = StrategyType(request.strategy_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy type. Must be one of: {[s.value for s in StrategyType]}"
        )

    selected_tests = select_tests_by_strategy(
        tests_dict,
        strategy,
        request.modification_zones,
        request.modification_level,
        constraints,
        request.custom_preferences
    )

    # Step 3: Calculate scoring
    # Convert to TestInfo objects
    test_info_list = []
    for test_dict in selected_tests:
        test_info_list.append(TestInfo(
            id=test_dict['id'],
            nom=test_dict['nom_de_test'],
            tier=test_dict.get('tier', 4),
            prix=test_dict['prix_euro'],
            duree=test_dict['duree_jours'],
            zone=test_dict.get('zone_modification', ''),
            is_homologation=test_dict.get('test_homologation', False),
            is_safety='crash' in test_dict['nom_de_test'].lower() or 'choc' in test_dict['nom_de_test'].lower(),
            is_numerical=test_dict['prix_euro'] == 0,
            pourcentage_necessite=test_dict['pourcentage_necessite']
        ))

    # Calculate totals
    total_cost = sum(t.prix for t in test_info_list)

    # Calculate timelines
    timelines = calculate_timelines(test_info_list)

    # Calculate complete score
    score_breakdown = calculate_complete_score(
        test_info_list,
        constraints,
        total_cost,
        timelines['critical_path_days']
    )

    # Determine feasibility
    feasibility_status = determine_feasibility_status(score_breakdown.risk_score)

    # Step 4: Save to database
    validation_plan = ValidationPlan(
        plan_name=request.plan_name,
        vehicle_category=request.vehicle_category,
        is_mivie=request.is_mivie,
        modification_zones=request.modification_zones,
        modification_level=request.modification_level,
        target_markets=request.target_markets,
        max_budget=request.max_budget,
        max_duration=request.max_duration,
        strategy_type=request.strategy_type,
        total_cost=total_cost,
        total_duration_physical=timelines['critical_path_days'],
        total_duration_engineering=timelines['engineering_workload_days'],
        parallel_capacity=timelines['parallel_optimized_days'],
        risk_score=score_breakdown.risk_score,
        feasibility_status=feasibility_status,
        score_coverage=score_breakdown.coverage,
        score_regulatory=score_breakdown.regulatory,
        score_safety=score_breakdown.safety,
        score_completeness=score_breakdown.completeness,
        score_efficiency=score_breakdown.efficiency,
        score_timeline=score_breakdown.timeline,
        score_budget=score_breakdown.budget
    )

    db.add(validation_plan)
    db.commit()
    db.refresh(validation_plan)

    # Add test associations
    for test_dict in selected_tests:
        plan_test = PlanTest(
            plan_id=validation_plan.id,
            test_id=test_dict['id'],
            tier=test_dict.get('tier', 4),
            is_removable=test_dict.get('is_removable', True)
        )
        db.add(plan_test)

    db.commit()

    # Step 5: Generate suggestions
    suggestions = suggest_optional_improvements(
        test_info_list,
        score_breakdown,
        constraints
    )

    # Get missing mandatory tests
    missing_mandatory = get_missing_mandatory_tests(
        test_info_list,
        [TestInfo(
            id=t['id'], 
            nom=t['nom_de_test'], 
            tier=4,
            prix=t['prix_euro'], 
            duree=t['duree_jours'],
            zone=t.get('zone_modification', ''),
            is_homologation=t.get('test_homologation', False),
            is_safety=False, 
            is_numerical=t['prix_euro'] == 0,
            pourcentage_necessite=t['pourcentage_necessite']
        ) for t in tests_dict],
        request.target_markets
    )

    # Get tier distribution
    tier_dist = calculate_tier_distribution(test_info_list)

    # Get cost breakdown
    cost_breakdown = calculate_cost_breakdown(test_info_list)

    # Return complete response
    return {
        'plan_id': validation_plan.id,
        'plan_name': validation_plan.plan_name,
        'feasibility_status': feasibility_status,
        'risk_score': float(score_breakdown.risk_score),
        'summary': {
            'total_tests': len(selected_tests),
            'total_cost': float(total_cost),
            'timelines': timelines,
            'tier_distribution': tier_dist,
            'cost_breakdown': {k: float(v) for k, v in cost_breakdown.items()}
        },
        'scoring': {
            'coverage': float(score_breakdown.coverage),
            'regulatory': float(score_breakdown.regulatory),
            'safety': float(score_breakdown.safety),
            'completeness': float(score_breakdown.completeness),
            'efficiency': float(score_breakdown.efficiency),
            'timeline': float(score_breakdown.timeline),
            'budget': float(score_breakdown.budget),
            'total': float(score_breakdown.total)
        },
        'constraints': {
            'max_budget': request.max_budget,
            'max_duration': request.max_duration,
            'budget_exceeded': total_cost > request.max_budget if request.max_budget else False,
            'timeline_exceeded': timelines['critical_path_days'] > request.max_duration if request.max_duration else False
        },
        'warnings': {
            'missing_mandatory_tests': missing_mandatory,
            'suggestions': suggestions
        },
        'selected_tests': [
            {
                'id': t['id'],
                'nom': t['nom_de_test'],
                'tier': t.get('tier', 4),
                'prix': t['prix_euro'],
                'duree': t['duree_jours'],
                'is_removable': t.get('is_removable', True),
                'zone': t.get('zone_modification'),
                'is_homologation': t.get('test_homologation', False)
            }
            for t in selected_tests
        ]
    }


@router.get("/{plan_id}")
def get_plan_by_id(plan_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific validation plan"""
    
    plan = db.query(ValidationPlan).filter(ValidationPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan with ID {plan_id} not found")

    # Get associated tests
    plan_tests = db.query(PlanTest, Test).join(Test).filter(
        PlanTest.plan_id == plan_id
    ).all()

    tests = [
        {
            'id': test.id,
            'nom': test.nom_de_test,
            'tier': pt.tier,
            'prix': float(test.prix_euro) if test.prix_euro else 0,
            'duree': float(test.duree_jours) if test.duree_jours else 0,
            'is_removable': pt.is_removable,
            'zone': test.zone_modification,
            'is_homologation': test.test_homologation
        }
        for pt, test in plan_tests
    ]

    return {
        'id': plan.id,
        'plan_name': plan.plan_name,
        'vehicle_category': plan.vehicle_category,
        'is_mivie': plan.is_mivie,
        'modification_zones': plan.modification_zones,
        'modification_level': plan.modification_level,
        'target_markets': plan.target_markets,
        'strategy_type': plan.strategy_type,
        'feasibility_status': plan.feasibility_status,
        'risk_score': float(plan.risk_score) if plan.risk_score else 0,
        'summary': {
            'total_tests': len(tests),
            'total_cost': float(plan.total_cost) if plan.total_cost else 0,
            'total_duration_physical': plan.total_duration_physical,
            'total_duration_engineering': plan.total_duration_engineering,
            'parallel_capacity': plan.parallel_capacity
        },
        'scoring': {
            'coverage': float(plan.score_coverage) if plan.score_coverage else 0,
            'regulatory': float(plan.score_regulatory) if plan.score_regulatory else 0,
            'safety': float(plan.score_safety) if plan.score_safety else 0,
            'completeness': float(plan.score_completeness) if plan.score_completeness else 0,
            'efficiency': float(plan.score_efficiency) if plan.score_efficiency else 0,
            'timeline': float(plan.score_timeline) if plan.score_timeline else 0,
            'budget': float(plan.score_budget) if plan.score_budget else 0
        },
        'tests': tests,
        'created_at': plan.created_at.isoformat()
    }


@router.get("/")
def list_plans(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get list of all validation plans"""
    
    plans = db.query(ValidationPlan).offset(skip).limit(limit).all()
    total = db.query(ValidationPlan).count()

    return {
        'total': total,
        'plans': [
            {
                'id': p.id,
                'plan_name': p.plan_name,
                'vehicle_category': p.vehicle_category,
                'feasibility_status': p.feasibility_status,
                'risk_score': float(p.risk_score) if p.risk_score else 0,
                'total_cost': float(p.total_cost) if p.total_cost else 0,
                'created_at': p.created_at.isoformat()
            }
            for p in plans
        ]
    }


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a validation plan"""
    
    plan = db.query(ValidationPlan).filter(ValidationPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan with ID {plan_id} not found")

    db.delete(plan)
    db.commit()

    return {"message": f"Plan {plan_id} deleted successfully"}


@router.post("/compare-strategies")
def compare_all_strategies(
    request: CreatePlanRequest,
    db: Session = Depends(get_db)
):
    """
    Compare all 4 strategies side-by-side without saving
    Useful for helping user choose the best strategy
    """
    
    # Get available tests
    query = db.query(Test)
    if request.is_mivie:
        query = query.filter(Test.test_mivie == 'Oui')
    if request.vehicle_category:
        query = query.filter(Test.categorie_vehicule.contains(request.vehicle_category))

    available_tests = query.all()

    tests_dict = [
        {
            'id': t.id,
            'nom_de_test': t.nom_de_test,
            'test_homologation': t.test_homologation,
            'prix_euro': float(t.prix_euro) if t.prix_euro else 0,
            'duree_jours': float(t.duree_jours) if t.duree_jours else 0,
            'zone_modification': t.zone_modification,
            'niveau_modification': t.niveau_modification,
            'pourcentage_necessite': float(t.pourcentage_necessite) if t.pourcentage_necessite else 0,
            'strategie_validation': t.strategie_validation,
            'pays_commercialisation': t.pays_commercialisation
        }
        for t in available_tests
    ]

    constraints = PlanConstraints(
        max_budget=request.max_budget,
        max_duration=request.max_duration,
        required_zones=request.modification_zones,
        target_markets=request.target_markets
    )

    comparison = compare_strategies(
        tests_dict,
        request.modification_zones,
        request.modification_level,
        constraints
    )

    return comparison