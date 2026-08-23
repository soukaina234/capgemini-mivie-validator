"""
AI Recommendations API endpoints
Handles Capgemini Generative Engine integration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.database import get_db
from app.models import ValidationPlan, PlanTest, Test
from app.ai_integration import generate_ai_recommendation, get_ai_usage_stats

router = APIRouter()


class AIRecommendationRequest(BaseModel):
    plan_id: int
    request_type: str  # 'gap_analysis', 'optimization', 'bundling', 'general'


@router.post("/recommend")
def get_ai_recommendation(
    request: AIRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered recommendation for a validation plan
    
    Request Types:
    - gap_analysis: Identify missing tests
    - optimization: Cost/time reduction suggestions
    - bundling: Test bundling opportunities
    - general: Overall assessment
    """
    
    # Validate request type
    valid_types = ['gap_analysis', 'optimization', 'bundling', 'general']
    if request.request_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request_type. Must be one of: {valid_types}"
        )
    
    # Get plan from database
    plan = db.query(ValidationPlan).filter(ValidationPlan.id == request.plan_id).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {request.plan_id} not found")
    
    # Get plan tests
    plan_tests = db.query(PlanTest, Test).join(Test).filter(
        PlanTest.plan_id == request.plan_id
    ).all()
    
    # Build context for AI
    context = {
        'vehicle_category': plan.vehicle_category,
        'is_mivie': plan.is_mivie,
        'zones': plan.modification_zones,
        'level': plan.modification_level,
        'markets': plan.target_markets,
        'num_tests': len(plan_tests),
        'total_cost': float(plan.total_cost) if plan.total_cost else 0,
        'total_days': plan.total_duration_physical or 0,
        'risk_score': float(plan.risk_score) if plan.risk_score else 0,
        'max_budget': plan.max_budget,
        'max_duration': plan.max_duration,
        'budget_exceeded': (float(plan.total_cost) > plan.max_budget) if plan.max_budget else False,
        'timeline_exceeded': (plan.total_duration_physical > plan.max_duration) if plan.max_duration else False,
        'score_coverage': float(plan.score_coverage) if plan.score_coverage else 0,
        'score_regulatory': float(plan.score_regulatory) if plan.score_regulatory else 0,
        'score_safety': float(plan.score_safety) if plan.score_safety else 0,
        'score_timeline': float(plan.score_timeline) if plan.score_timeline else 0,
        'score_budget': float(plan.score_budget) if plan.score_budget else 0,
        'test_list': '\n'.join([
            f"- {test.nom_de_test} (Tier {pt.tier}, €{test.prix_euro}, {test.duree_jours} days)"
            for pt, test in plan_tests[:20]  # Limit to first 20 for prompt size
        ]),
        'test_locations': list(set([
            test.lieu_realisation 
            for pt, test in plan_tests 
            if test.lieu_realisation
        ])),
        'coverage': (float(plan.score_coverage) / 25.0) if plan.score_coverage else 0
    }
    
    # Get covered zones
    covered_zones = set()
    for pt, test in plan_tests:
        if test.zone_modification:
            zones = [z.strip() for z in test.zone_modification.split('&')]
            covered_zones.update(zones)
    context['covered_zones'] = list(covered_zones)
    
    # Generate recommendation
    result = generate_ai_recommendation(
        db=db,
        request_type=request.request_type,
        context=context,
        plan_id=request.plan_id
    )
    
    return {
        'plan_id': request.plan_id,
        'request_type': request.request_type,
        'recommendation': result['recommendation'],
        'used_ai': result['used_ai'],
        'metadata': {
            'tokens_used': result.get('tokens_used', 0),
            'response_time_ms': result.get('response_time_ms', 0),
            'rate_limit_exceeded': result.get('rate_limit_exceeded', False),
            'resets_at': result.get('resets_at')
        }
    }


@router.get("/usage")
def get_usage_statistics(db: Session = Depends(get_db)):
    """
    Get AI API usage statistics for current week
    """
    stats = get_ai_usage_stats(db)
    
    return {
        'current_week': stats,
        'rate_limit': {
            'max_calls_per_week': 100,
            'calls_used': stats['calls_used'],
            'calls_remaining': stats['calls_remaining'],
            'percentage_used': (stats['calls_used'] / 100) * 100
        }
    }


@router.post("/batch-recommend")
def get_batch_recommendations(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate all 4 recommendation types at once
    Useful for comprehensive plan review
    """
    
    # Check if plan exists
    plan = db.query(ValidationPlan).filter(ValidationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    
    # Check rate limit (need 4 calls)
    from app.ai_integration import CapgeminiAIClient
    client = CapgeminiAIClient(db)
    rate_status = client.check_rate_limit()
    
    if rate_status['calls_remaining'] < 4:
        return {
            'error': 'Insufficient API calls remaining',
            'calls_remaining': rate_status['calls_remaining'],
            'calls_needed': 4,
            'message': 'Please use individual recommendations or wait until rate limit resets'
        }
    
    # Generate all recommendations
    request_types = ['gap_analysis', 'optimization', 'bundling', 'general']
    results = {}
    
    for req_type in request_types:
        try:
            recommendation = get_ai_recommendation(
                AIRecommendationRequest(plan_id=plan_id, request_type=req_type),
                db=db
            )
            results[req_type] = recommendation
        except Exception as e:
            results[req_type] = {
                'error': str(e),
                'recommendation': None
            }
    
    return {
        'plan_id': plan_id,
        'recommendations': results,
        'api_calls_used': sum(1 for r in results.values() if r.get('used_ai', False))
    }