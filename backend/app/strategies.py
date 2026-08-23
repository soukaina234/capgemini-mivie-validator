"""
Test selection strategies
Implements 4 different approaches to building validation plans
"""

from typing import List, Dict, Any
from enum import Enum
from app.scoring import TestInfo, PlanConstraints
import math


class StrategyType(str, Enum):
    """Available test selection strategies"""
    MINIMUM = "minimum"
    BALANCED = "balanced"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"


def classify_test_tier(
    test: Dict[str, Any],
    modification_zones: List[str],
    modification_level: str
) -> int:
    """
    Classify test into tier 1-4
    Returns 0 if test should be EXCLUDED (doesn't match zones)
    """
    
    # First check if test matches modification zones
    test_zones_str = test.get('zone_modification', '')
    
    # If no zone specified in test, include it (general test)
    if not test_zones_str or test_zones_str.strip() == '':
        zone_match = True
    else:
        # Split test zones by & or comma
        test_zone_list = [z.strip().lower() for z in str(test_zones_str).replace('&', ',').split(',')]
        # Check if ANY modification zone matches ANY test zone
        zone_match = any(
            any(mod_zone.lower() in tz or tz in mod_zone.lower() 
                for tz in test_zone_list)
            for mod_zone in modification_zones
        )
    
    # If test doesn't match zones, EXCLUDE IT (return 0)
    if not zone_match:
        return 0
    
    # TIER 1: Mandatory (homologation or safety-critical)
    if test.get('test_homologation', False):
        return 1
    
    safety_keywords = ['crash', 'choc', 'passive', 'adas', 'freinage', 'airbag', 'safety', 'sécurité']
    test_name_lower = test.get('nom_de_test', '').lower()
    if any(keyword in test_name_lower for keyword in safety_keywords):
        return 1
    
    # TIER 2: High priority (70%+ necessity + zone match)
    necessity = test.get('pourcentage_necessite', 0)
    if necessity >= 70:
        return 2
    
    # TIER 3: Medium priority (40-69% necessity)
    if necessity >= 40:
        return 3
    
    # TIER 4: Optional
    return 4


def apply_minimum_strategy(
    all_tests: List[Dict[str, Any]],
    modification_zones: List[str],
    modification_level: str,
    constraints: PlanConstraints
) -> List[Dict[str, Any]]:
    """Strategy 1: MINIMUM - Only mandatory + minimum coverage"""
    selected = []
    current_cost = 0
    current_duration = 0
    
    # Add all Tier 1 tests
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:  # SKIP tests that don't match zones
            continue
        if tier == 1:
            test['tier'] = tier
            test['is_removable'] = False
            selected.append(test)
            current_cost += test.get('prix_euro', 0)
            if test.get('strategie_validation') == 'Test physique':
                current_duration += test.get('duree_jours', 0)
    
    # Check if mandatory tests already exceed constraints
    if constraints.max_budget and current_cost > constraints.max_budget:
        print(f"⚠️ WARNING: Mandatory tests (€{current_cost}) exceed budget (€{constraints.max_budget})")
    if constraints.max_duration and current_duration > constraints.max_duration:
        print(f"⚠️ WARNING: Mandatory tests ({current_duration} days) exceed timeline ({constraints.max_duration} days)")
    
    # Add minimum Tier 2 for each required zone (respecting constraints)
    covered_zones = set()
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:  # SKIP
            continue
        if tier == 2:
            test_cost = test.get('prix_euro', 0)
            test_duration = test.get('duree_jours', 0)
            is_physical = test.get('strategie_validation') == 'Test physique'
            
            # Check constraints
            if constraints.max_budget and (current_cost + test_cost) > constraints.max_budget:
                continue
            if constraints.max_duration and is_physical and (current_duration + test_duration) > constraints.max_duration:
                continue
            
            test_zones = test.get('zone_modification', '')
            if test_zones:
                test_zone_list = [z.strip() for z in str(test_zones).split('&')]
                
                for mod_zone in modification_zones:
                    if mod_zone not in covered_zones:
                        if any(mod_zone.lower() in tz.lower() for tz in test_zone_list):
                            test['tier'] = tier
                            test['is_removable'] = True
                            selected.append(test)
                            covered_zones.update(test_zone_list)
                            current_cost += test_cost
                            if is_physical:
                                current_duration += test_duration
                            break
    
    return selected


def apply_balanced_strategy(
    all_tests: List[Dict[str, Any]],
    modification_zones: List[str],
    modification_level: str,
    constraints: PlanConstraints
) -> List[Dict[str, Any]]:
    """Strategy 2: BALANCED with STRICT budget and time respect"""
    selected = []
    current_cost = 0
    current_duration = 0
    
    # Add all Tier 1 (mandatory)
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:
            continue
        if tier == 1:
            test['tier'] = tier
            test['is_removable'] = False
            selected.append(test)
            current_cost += test.get('prix_euro', 0)
            if test.get('strategie_validation') == 'Test physique':
                current_duration += test.get('duree_jours', 0)
    
    # Check if Tier 1 already exceeds budget
    if constraints.max_budget and current_cost > constraints.max_budget:
        print(f"⚠️ WARNING: Mandatory tests (€{current_cost}) exceed budget (€{constraints.max_budget})")
        return selected
    
    if constraints.max_duration and current_duration > constraints.max_duration:
        print(f"⚠️ WARNING: Mandatory tests ({current_duration} days) exceed timeline ({constraints.max_duration} days)")
        return selected
    
    # Add Tier 2 (if constraints allow)
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:
            continue
        if tier == 2:
            test_cost = test.get('prix_euro', 0)
            test_duration = test.get('duree_jours', 0)
            is_physical = test.get('strategie_validation') == 'Test physique'
            
            # STRICT constraint checks
            if constraints.max_budget and (current_cost + test_cost) > constraints.max_budget:
                continue  # Skip if over budget
            if constraints.max_duration and is_physical and (current_duration + test_duration) > constraints.max_duration:
                continue  # Skip if over timeline
            
            test['tier'] = tier
            test['is_removable'] = True
            selected.append(test)
            current_cost += test_cost
            if is_physical:
                current_duration += test_duration
    
    # Add selected Tier 3 durability tests (if constraints allow)
    durability_keywords = ['endurance', 'durabilit', 'roulage', 'corrosion', 'vieillissement']
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:
            continue
        if tier == 3:
            test_name_lower = test.get('nom_de_test', '').lower()
            if any(keyword in test_name_lower for keyword in durability_keywords):
                test_cost = test.get('prix_euro', 0)
                test_duration = test.get('duree_jours', 0)
                is_physical = test.get('strategie_validation') == 'Test physique'
                
                # STRICT constraint checks
                if constraints.max_budget and (current_cost + test_cost) > constraints.max_budget:
                    continue  # Skip if over budget
                if constraints.max_duration and is_physical and (current_duration + test_duration) > constraints.max_duration:
                    continue  # Skip if over timeline
                
                test['tier'] = tier
                test['is_removable'] = True
                selected.append(test)
                current_cost += test_cost
                if is_physical:
                    current_duration += test_duration
    
    print(f"✅ Balanced strategy: {len(selected)} tests, €{current_cost}, {current_duration} days")
    return selected


def apply_comprehensive_strategy(
    all_tests: List[Dict[str, Any]],
    modification_zones: List[str],
    modification_level: str,
    constraints: PlanConstraints
) -> List[Dict[str, Any]]:
    """Strategy 3: COMPREHENSIVE - Maximum validation with constraint respect"""
    selected = []
    current_cost = 0
    current_duration = 0
    
    # Add Tier 1, 2, 3 (respecting constraints)
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:  # SKIP
            continue
        if tier in [1, 2, 3]:
            test_cost = test.get('prix_euro', 0)
            test_duration = test.get('duree_jours', 0)
            is_physical = test.get('strategie_validation') == 'Test physique'
            
            # Mandatory tests (Tier 1) always included, others checked
            if tier != 1:
                if constraints.max_budget and (current_cost + test_cost) > constraints.max_budget:
                    continue
                if constraints.max_duration and is_physical and (current_duration + test_duration) > constraints.max_duration:
                    continue
            
            test['tier'] = tier
            test['is_removable'] = (tier != 1)
            selected.append(test)
            current_cost += test_cost
            if is_physical:
                current_duration += test_duration
    
    # Add valuable Tier 4 tests (numerical or short duration, if constraints allow)
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:  # SKIP
            continue
        if tier == 4:
            test_cost = test.get('prix_euro', 0)
            test_duration = test.get('duree_jours', 0)
            is_physical = test.get('strategie_validation') == 'Test physique'
            
            if test_cost == 0 or test_duration <= 5:
                # Check constraints
                if constraints.max_budget and (current_cost + test_cost) > constraints.max_budget:
                    continue
                if constraints.max_duration and is_physical and (current_duration + test_duration) > constraints.max_duration:
                    continue
                
                test['tier'] = tier
                test['is_removable'] = True
                selected.append(test)
                current_cost += test_cost
                if is_physical:
                    current_duration += test_duration
    
    print(f"✅ Comprehensive strategy: {len(selected)} tests, €{current_cost}, {current_duration} days")
    return selected


def apply_custom_strategy(
    all_tests: List[Dict[str, Any]],
    modification_zones: List[str],
    modification_level: str,
    constraints: PlanConstraints,
    user_preferences: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Strategy 4: CUSTOM - User-defined optimization with STRICT budget"""
    selected = []
    
    # Always include Tier 1 (mandatory)
    tier1_tests = []
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0:
            continue
        if tier == 1:
            test['tier'] = tier
            test['is_removable'] = False
            tier1_tests.append(test)
            selected.append(test)
    
    # Check if Tier 1 already exceeds budget
    tier1_cost = sum(t.get('prix_euro', 0) for t in tier1_tests)
    tier1_duration = sum(
        t.get('duree_jours', 0) 
        for t in tier1_tests 
        if t.get('strategie_validation') == 'Test physique'
    )
    
    if constraints.max_budget and tier1_cost > constraints.max_budget:
        print(f"⚠️ WARNING: Mandatory tests (€{tier1_cost}) exceed budget (€{constraints.max_budget})")
        return selected  # Return only mandatory tests
    
    if constraints.max_duration and tier1_duration > constraints.max_duration:
        print(f"⚠️ WARNING: Mandatory tests ({tier1_duration} days) exceed timeline ({constraints.max_duration} days)")
        return selected
    
    prioritize = user_preferences.get('prioritize', 'balanced')
    
    # Score remaining tests
    candidate_tests = []
    for test in all_tests:
        tier = classify_test_tier(test, modification_zones, modification_level)
        if tier == 0 or tier == 1:
            continue
        score = calculate_test_priority_score(test, tier, prioritize, modification_zones)
        candidate_tests.append({'test': test, 'tier': tier, 'score': score})
    
    # Sort by score (highest first)
    candidate_tests.sort(key=lambda x: x['score'], reverse=True)
    
    # Add tests one by one until budget/time limit reached
    current_cost = tier1_cost
    current_duration = tier1_duration
    
    for candidate in candidate_tests:
        test = candidate['test']
        test_cost = test.get('prix_euro', 0)
        test_duration = test.get('duree_jours', 0)
        is_physical = test.get('strategie_validation') == 'Test physique'
        
        # STRICT budget check
        if constraints.max_budget and (current_cost + test_cost) > constraints.max_budget:
            continue  # Skip this test
        
        # STRICT timeline check
        if constraints.max_duration and is_physical and (current_duration + test_duration) > constraints.max_duration:
            continue  # Skip this test
        
        # Add test
        test['tier'] = candidate['tier']
        test['is_removable'] = True
        selected.append(test)
        current_cost += test_cost
        if is_physical:
            current_duration += test_duration
    
    print(f"✅ Custom strategy: {len(selected)} tests, €{current_cost}, {current_duration} days (Budget: €{constraints.max_budget}, Timeline: {constraints.max_duration} days)")
    
    return selected


def calculate_test_priority_score(
    test: Dict[str, Any],
    tier: int,
    prioritize: str,
    modification_zones: List[str]
) -> float:
    """
    Calculate priority score for custom strategy
    Higher score = higher priority
    """
    base_score = {1: 100, 2: 75, 3: 50, 4: 25}[tier]
    
    necessity = test.get('pourcentage_necessite', 0)
    cost = test.get('prix_euro', 0)
    duration = test.get('duree_jours', 0)
    is_numerical = cost == 0
    
    # Zone matching bonus
    test_zones = test.get('zone_modification', '')
    zone_match = False
    if test_zones:
        test_zone_list = [z.strip() for z in str(test_zones).split('&')]
        zone_match = any(
            mod_zone.lower() in tz.lower() 
            for mod_zone in modification_zones 
            for tz in test_zone_list
        )
    
    if zone_match:
        base_score += 20
    
    # Apply priority-specific adjustments
    if prioritize == 'minimize_cost':
        if is_numerical:
            base_score += 30  # Big bonus for free tests
        elif cost < 5000:
            base_score += 15
        elif cost > 20000:
            base_score -= 20  # Penalty for expensive tests
    
    elif prioritize == 'minimize_time':
        if duration <= 5:
            base_score += 30
        elif duration <= 10:
            base_score += 15
        elif duration > 50:
            base_score -= 20
    
    elif prioritize == 'maximize_safety':
        safety_keywords = ['crash', 'choc', 'adas', 'freinage', 'safety', 'sécurité']
        test_name_lower = test.get('nom_de_test', '').lower()
        if any(keyword in test_name_lower for keyword in safety_keywords):
            base_score += 40
    
    elif prioritize == 'maximize_coverage':
        # Multi-zone tests get bonus
        if '&' in test_zones:
            base_score += 25
    
    # Necessity bonus
    base_score += necessity * 0.3
    
    return base_score


def get_strategy_description(strategy: StrategyType) -> Dict[str, str]:
    """Get human-readable description of strategy"""
    descriptions = {
        StrategyType.MINIMUM: {
            "name": "Regulatory Minimum",
            "description": "Include only mandatory homologation tests and minimum coverage for modified zones.",
            "risk_level": "HIGH",
            "typical_cost": "€30,000 - €80,000",
            "typical_duration": "30-60 days",
            "recommendation": "⚠️ Use only for minor modifications with low risk tolerance."
        },
        StrategyType.BALANCED: {
            "name": "Balanced (Recommended)",
            "description": "Optimal balance of mandatory tests, high-priority validations, and durability checks.",
            "risk_level": "MEDIUM",
            "typical_cost": "€80,000 - €150,000",
            "typical_duration": "60-120 days",
            "recommendation": "✅ Best choice for most Mi-Vie projects. Good coverage with reasonable cost/time."
        },
        StrategyType.COMPREHENSIVE: {
            "name": "Comprehensive",
            "description": "Maximum validation coverage across all tiers. Includes extensive durability and optional tests.",
            "risk_level": "LOW",
            "typical_cost": "€150,000 - €300,000",
            "typical_duration": "120-200 days",
            "recommendation": "🛡️ Recommended for major structural changes or safety-critical modifications."
        },
        StrategyType.CUSTOM: {
            "name": "Custom Optimization",
            "description": "User-defined priorities with constraint-based test selection.",
            "risk_level": "VARIABLE",
            "typical_cost": "Depends on constraints",
            "typical_duration": "Depends on constraints",
            "recommendation": "🎯 Best for projects with specific budget/timeline constraints."
        }
    }
    
    return descriptions.get(strategy, {})


def select_tests_by_strategy(
    all_tests: List[Dict[str, Any]],
    strategy: StrategyType,
    modification_zones: List[str],
    modification_level: str,
    constraints: PlanConstraints,
    user_preferences: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Main entry point for test selection
    
    Args:
        all_tests: All available tests from database
        strategy: Selected strategy type
        modification_zones: User's modification zones
        modification_level: Modification level (Niveau 1/2/3)
        constraints: Budget/time constraints
        user_preferences: Custom strategy preferences
    
    Returns:
        List of selected tests with tier assignments
    """
    if strategy == StrategyType.MINIMUM:
        return apply_minimum_strategy(
            all_tests, modification_zones, modification_level, constraints
        )
    
    elif strategy == StrategyType.BALANCED:
        return apply_balanced_strategy(
            all_tests, modification_zones, modification_level, constraints
        )
    
    elif strategy == StrategyType.COMPREHENSIVE:
        return apply_comprehensive_strategy(
            all_tests, modification_zones, modification_level, constraints
        )
    
    elif strategy == StrategyType.CUSTOM:
        return apply_custom_strategy(
            all_tests, modification_zones, modification_level, 
            constraints, user_preferences or {}
        )
    
    else:
        # Default to balanced
        return apply_balanced_strategy(
            all_tests, modification_zones, modification_level, constraints
        )
    

def compare_strategies(
    all_tests: List[Dict[str, Any]],
    modification_zones: List[str],
    modification_level: str,
    constraints: PlanConstraints
) -> Dict[str, Any]:
    """
    Compare all 4 strategies side-by-side
    
    Returns:
        Comparison data for each strategy
    """
    comparison = {}
    
    for strategy in StrategyType:
        selected = select_tests_by_strategy(
            all_tests, strategy, modification_zones, 
            modification_level, constraints
        )
        
        total_cost = sum(t.get('prix_euro', 0) for t in selected)
        physical_duration = sum(
            t.get('duree_jours', 0) 
            for t in selected 
            if t.get('strategie_validation') == 'Test physique'
        )
        
        tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for test in selected:
            tier = test.get('tier', 4)
            tier_counts[tier] += 1
        
        # Check if constraints are exceeded
        exceeds_budget = constraints.max_budget and total_cost > constraints.max_budget
        exceeds_duration = constraints.max_duration and physical_duration > constraints.max_duration
        
        comparison[strategy.value] = {
            'test_count': len(selected),
            'total_cost': total_cost,
            'physical_duration_days': physical_duration,
            'tier_distribution': tier_counts,
            'description': get_strategy_description(strategy),
            'exceeds_budget': exceeds_budget,
            'exceeds_duration': exceeds_duration,
            'is_feasible': not (exceeds_budget or exceeds_duration)
        }
    
    return comparison