"""
Feasibility and risk scoring algorithms
Implements the 7-component scoring system
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import math


@dataclass
class TestInfo:
    """Information about a single test"""
    id: int
    nom: str
    tier: int
    prix: float
    duree: float
    zone: str
    is_homologation: bool
    is_safety: bool
    is_numerical: bool
    pourcentage_necessite: float


@dataclass
class PlanConstraints:
    """User-defined constraints for the plan"""
    max_budget: float = None
    max_duration: int = None
    required_zones: List[str] = None
    target_markets: List[str] = None


@dataclass
class ScoreBreakdown:
    """Detailed scoring breakdown"""
    coverage: float  # 0-25
    regulatory: float  # 0-30
    safety: float  # 0-25
    completeness: float  # 0-10
    efficiency: float  # 0-10
    timeline: float  # 0-100 (separate)
    budget: float  # 0-100 (separate)
    total: float  # 0-100
    risk_score: float  # 0-100


def calculate_coverage_score(
    tests: List[TestInfo],
    required_zones: List[str]
) -> float:
    """
    Calculate zone coverage score (25% weight)
    
    Formula: (zones_covered / zones_required) * 25
    """
    if not required_zones:
        return 25.0
    
    covered_zones = set()
    for test in tests:
        if test.zone:
            # Handle multi-zone tests
            test_zones = [z.strip() for z in test.zone.split('&')]
            covered_zones.update(test_zones)
    
    coverage_ratio = len(covered_zones) / len(required_zones)
    score = coverage_ratio * 25.0
    
    return min(25.0, score)


def calculate_regulatory_score(
    tests: List[TestInfo],
    target_markets: List[str]
) -> float:
    """
    Calculate regulatory compliance score (30% weight)
    
    All mandatory homologation tests MUST be included
    """
    mandatory_tests = [t for t in tests if t.is_homologation]
    
    if not mandatory_tests:
        # No mandatory tests required
        return 30.0
    
    # Check if all mandatory tests are included (tier 1)
    included_mandatory = [t for t in mandatory_tests if t.tier == 1]
    
    compliance_ratio = len(included_mandatory) / len(mandatory_tests)
    score = compliance_ratio * 30.0
    
    # Penalty if missing any mandatory test
    if compliance_ratio < 1.0:
        score = score * 0.5  # Severe penalty
    
    return score


def calculate_safety_score(tests: List[TestInfo]) -> float:
    """
    Calculate safety criticality score (25% weight)
    
    Checks for crash tests, ADAS validation, braking tests
    """
    safety_categories = [
        'Choc', 'Crash', 'ADAS', 'Freinage', 'Braking',
        'SAFE', 'PASSIVE', 'SECURITY', 'Sécurité'
    ]
    
    safety_tests = [
        t for t in tests 
        if t.is_safety or any(cat.lower() in t.nom.lower() for cat in safety_categories)
    ]
    
    # Scoring based on number of safety tests
    if len(safety_tests) >= 10:
        return 25.0
    elif len(safety_tests) >= 5:
        return 20.0
    elif len(safety_tests) >= 3:
        return 15.0
    elif len(safety_tests) >= 1:
        return 10.0
    else:
        return 0.0


def calculate_completeness_score(tests: List[TestInfo]) -> float:
    """
    Calculate tier completeness score (10% weight)
    
    Checks if all 4 tiers are represented
    """
    represented_tiers = set(t.tier for t in tests)
    
    # Ideal: All 4 tiers represented
    if len(represented_tiers) == 4:
        return 10.0
    elif len(represented_tiers) == 3:
        return 8.0
    elif len(represented_tiers) == 2:
        return 5.0
    else:
        return 3.0


def calculate_efficiency_score(tests: List[TestInfo]) -> float:
    """
    Calculate resource efficiency score (10% weight)
    
    Rewards tests that cover multiple zones/problems
    """
    multi_zone_tests = [t for t in tests if '&' in (t.zone or '')]
    
    efficiency_ratio = len(multi_zone_tests) / max(len(tests), 1)
    score = efficiency_ratio * 10.0
    
    return min(10.0, score)


def calculate_timeline_score(
    total_days: int,
    max_days: int = None
) -> float:
    """
    Calculate timeline feasibility (0-100)
    
    Formula: max(0, 100 * (1 - (total_days / max_days)))
    """
    if max_days is None or max_days == 0:
        return 100.0
    
    if total_days <= max_days:
        # Under budget: scale from 100 down to 80
        ratio = total_days / max_days
        return 100.0 - (ratio * 20.0)
    else:
        # Over budget: penalty
        overage_ratio = (total_days - max_days) / max_days
        penalty = overage_ratio * 50.0
        return max(0, 80.0 - penalty)


def calculate_budget_score(
    total_cost: float,
    max_budget: float = None
) -> float:
    """
    Calculate budget feasibility (0-100)
    
    Formula: max(0, 100 * (1 - (total_cost / max_budget)))
    """
    if max_budget is None or max_budget == 0:
        return 100.0
    
    if total_cost <= max_budget:
        # Under budget: scale from 100 down to 80
        ratio = total_cost / max_budget
        return 100.0 - (ratio * 20.0)
    else:
        # Over budget: penalty
        overage_ratio = (total_cost - max_budget) / max_budget
        penalty = overage_ratio * 50.0
        return max(0, 80.0 - penalty)


def calculate_risk_score(breakdown: ScoreBreakdown) -> float:
    """
    Calculate overall risk score (0-100)
    
    Risk Factors (penalties):
    - Missing homologation: -50
    - Low safety: -30
    - Budget exceeded >20%: -20
    - Timeline exceeded >30%: -25
    - Coverage <80%: -15
    """
    base_score = 100.0
    
    # Regulatory penalty
    if breakdown.regulatory < 30.0:
        missing_ratio = 1 - (breakdown.regulatory / 30.0)
        base_score -= missing_ratio * 50.0
    
    # Safety penalty
    if breakdown.safety < 20.0:
        base_score -= 30.0
    elif breakdown.safety < 15.0:
        base_score -= 20.0
    
    # Budget penalty
    if breakdown.budget < 60.0:
        base_score -= 20.0
    elif breakdown.budget < 80.0:
        base_score -= 10.0
    
    # Timeline penalty
    if breakdown.timeline < 50.0:
        base_score -= 25.0
    elif breakdown.timeline < 70.0:
        base_score -= 15.0
    
    # Coverage penalty
    if breakdown.coverage < 20.0:  # Less than 80% of max 25
        base_score -= 15.0
    
    return max(0.0, min(100.0, base_score))


def determine_feasibility_status(risk_score: float) -> str:
    """
    Determine feasibility status based on risk score
    
    - 90-100: FEASIBLE (GREEN)
    - 75-89: MARGINAL (YELLOW)
    - 60-74: RISKY (ORANGE)
    - <60: IMPOSSIBLE (RED)
    """
    if risk_score >= 90:
        return "FEASIBLE"
    elif risk_score >= 75:
        return "MARGINAL"
    elif risk_score >= 60:
        return "RISKY"
    else:
        return "IMPOSSIBLE"


def calculate_complete_score(
    tests: List[TestInfo],
    constraints: PlanConstraints,
    total_cost: float,
    total_duration_physical: int
) -> ScoreBreakdown:
    """
    Calculate complete scoring breakdown
    
    Args:
        tests: List of selected tests
        constraints: User-defined constraints
        total_cost: Total cost of all tests
        total_duration_physical: Total physical test duration
    
    Returns:
        Complete score breakdown
    """
    # Calculate individual components
    coverage = calculate_coverage_score(tests, constraints.required_zones)
    regulatory = calculate_regulatory_score(tests, constraints.target_markets)
    safety = calculate_safety_score(tests)
    completeness = calculate_completeness_score(tests)
    efficiency = calculate_efficiency_score(tests)
    
    timeline = calculate_timeline_score(
        total_duration_physical,
        constraints.max_duration
    )
    
    budget = calculate_budget_score(
        total_cost,
        constraints.max_budget
    )
    
    # Calculate total weighted score
    total = coverage + regulatory + safety + completeness + efficiency
    
    # Create breakdown
    breakdown = ScoreBreakdown(
        coverage=coverage,
        regulatory=regulatory,
        safety=safety,
        completeness=completeness,
        efficiency=efficiency,
        timeline=timeline,
        budget=budget,
        total=total,
        risk_score=0.0  # Will be calculated next
    )
    
    # Calculate risk score
    breakdown.risk_score = calculate_risk_score(breakdown)
    
    return breakdown


def calculate_timelines(tests: List[TestInfo]) -> Dict[str, int]:
    """
    Calculate 3 different timeline views
    
    Returns:
        - critical_path: Physical tests only (sequential)
        - engineering_workload: Physical + Numerical duration
        - parallel_capacity: Maximum tests that can run simultaneously
    """
    physical_tests = [t for t in tests if not t.is_numerical and t.duree > 0]
    numerical_tests = [t for t in tests if t.is_numerical and t.duree > 0]
    
    # Critical path: physical tests run sequentially
    critical_path = sum(t.duree for t in physical_tests)
    
    # Engineering workload: all tests (but numerical can overlap)
    engineering_workload = critical_path + sum(t.duree for t in numerical_tests)
    
    # Parallel capacity: assume max 3 physical tests can run simultaneously
    if len(physical_tests) > 0:
        parallel_capacity = math.ceil(critical_path / 3)
    else:
        parallel_capacity = 0
    
    return {
        'critical_path_days': int(critical_path),
        'engineering_workload_days': int(engineering_workload),
        'parallel_optimized_days': int(parallel_capacity),
        'physical_test_count': len(physical_tests),
        'numerical_test_count': len(numerical_tests)
    }


def get_missing_mandatory_tests(
    selected_tests: List[TestInfo],
    all_available_tests: List[TestInfo],
    target_markets: List[str]
) -> List[str]:
    """
    Identify mandatory tests that are missing from the plan
    
    Returns:
        List of missing test names
    """
    selected_ids = {t.id for t in selected_tests}
    
    missing = []
    for test in all_available_tests:
        if test.is_homologation and test.id not in selected_ids:
            missing.append(test.nom)
    
    return missing


def suggest_optional_improvements(
    tests: List[TestInfo],
    breakdown: ScoreBreakdown,
    constraints: PlanConstraints
) -> List[Dict[str, str]]:
    """
    Generate suggestions to improve the plan
    
    Returns:
        List of actionable suggestions
    """
    suggestions = []
    
    # Coverage suggestions
    if breakdown.coverage < 20.0:
        suggestions.append({
            'type': 'coverage',
            'severity': 'high',
            'message': f"Zone coverage is {(breakdown.coverage/25)*100:.0f}%. Add tests for uncovered modification zones."
        })
    
    # Safety suggestions
    if breakdown.safety < 15.0:
        suggestions.append({
            'type': 'safety',
            'severity': 'high',
            'message': "Low safety test coverage. Consider adding crash or ADAS validation tests."
        })
    
    # Budget optimization
    if constraints.max_budget and breakdown.budget < 80.0:
        suggestions.append({
            'type': 'budget',
            'severity': 'medium',
            'message': "Budget exceeded. Replace expensive physical tests with numerical simulations where possible."
        })
    
    # Timeline optimization
    if constraints.max_duration and breakdown.timeline < 70.0:
        suggestions.append({
            'type': 'timeline',
            'severity': 'medium',
            'message': "Timeline exceeded. Consider removing Tier 4 tests or bundling tests at same location."
        })
    
    # Efficiency suggestion
    if breakdown.efficiency < 5.0:
        suggestions.append({
            'type': 'efficiency',
            'severity': 'low',
            'message': "Add multi-zone tests to improve resource efficiency."
        })
    
    return suggestions


def calculate_tier_distribution(tests: List[TestInfo]) -> Dict[int, int]:
    """Calculate how many tests in each tier"""
    distribution = {1: 0, 2: 0, 3: 0, 4: 0}
    
    for test in tests:
        if test.tier in distribution:
            distribution[test.tier] += 1
    
    return distribution


def calculate_cost_breakdown(tests: List[TestInfo]) -> Dict[str, float]:
    """Calculate cost by tier and type"""
    breakdown = {
        'tier_1_cost': sum(t.prix for t in tests if t.tier == 1),
        'tier_2_cost': sum(t.prix for t in tests if t.tier == 2),
        'tier_3_cost': sum(t.prix for t in tests if t.tier == 3),
        'tier_4_cost': sum(t.prix for t in tests if t.tier == 4),
        'physical_cost': sum(t.prix for t in tests if not t.is_numerical),
        'numerical_cost': sum(t.prix for t in tests if t.is_numerical),
        'total_cost': sum(t.prix for t in tests)
    }
    
    return breakdown