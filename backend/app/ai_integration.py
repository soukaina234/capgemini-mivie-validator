"""
Capgemini Generative Engine API Integration
Handles AI-powered recommendations with rate limiting
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import time

from app.config import settings
from app.models import AICallLog


class CapgeminiAIClient:
    """Client for Capgemini Generative Engine API"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = settings.CAPGEMINI_API_KEY
        self.endpoint = settings.CAPGEMINI_API_ENDPOINT
        self.model = settings.CAPGEMINI_MODEL
        self.max_calls_per_week = settings.AI_CALLS_PER_WEEK
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """
        Check if we have API calls remaining this week
        
        Returns:
            {
                'can_call': bool,
                'calls_used': int,
                'calls_remaining': int,
                'resets_at': datetime
            }
        """
        # Get start of current week
        now = datetime.now()
        days_since_monday = (now.weekday()) % 7
        week_start = now - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count calls this week
        calls_this_week = self.db.query(func.count(AICallLog.id)).filter(
            AICallLog.created_at >= week_start
        ).scalar()
        
        calls_remaining = self.max_calls_per_week - calls_this_week
        
        # Calculate reset time (next Monday)
        days_until_monday = (7 - days_since_monday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        resets_at = week_start + timedelta(days=days_until_monday)
        
        return {
            'can_call': calls_remaining > 0,
            'calls_used': calls_this_week,
            'calls_remaining': max(0, calls_remaining),
            'resets_at': resets_at
        }
    
    def generate_recommendation(
        self,
        request_type: str,
        context: Dict[str, Any],
        plan_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate AI recommendation
        
        Args:
            request_type: 'gap_analysis', 'optimization', 'bundling', 'general'
            context: Plan and test details
            plan_id: Optional plan ID for logging
        
        Returns:
            {
                'success': bool,
                'recommendation': str,
                'used_ai': bool,
                'tokens_used': int
            }
        """
        # Check rate limit
        rate_limit_status = self.check_rate_limit()
        
        if not rate_limit_status['can_call']:
            return {
                'success': True,
                'recommendation': self._fallback_rule_based_recommendation(request_type, context),
                'used_ai': False,
                'rate_limit_exceeded': True,
                'resets_at': rate_limit_status['resets_at'].isoformat()
            }
        
        # Build prompt
        prompt = self._build_prompt(request_type, context)
        
        # Call API
        start_time = time.time()
        
        try:
            response = self._call_api(prompt)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log success
            self._log_api_call(
                plan_id=plan_id,
                request_type=request_type,
                prompt_text=prompt[:500],  # Store first 500 chars
                tokens_used=response.get('tokens_used', 0),
                response_time_ms=response_time_ms,
                success=True
            )
            
            return {
                'success': True,
                'recommendation': response['text'],
                'used_ai': True,
                'tokens_used': response.get('tokens_used', 0),
                'response_time_ms': response_time_ms
            }
        
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log failure
            self._log_api_call(
                plan_id=plan_id,
                request_type=request_type,
                prompt_text=prompt[:500],
                tokens_used=0,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            # Fallback to rule-based
            return {
                'success': True,
                'recommendation': self._fallback_rule_based_recommendation(request_type, context),
                'used_ai': False,
                'error': str(e)
            }
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """
        Make actual API call to Capgemini Gen Engine
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.3,  # Low temperature for consistent recommendations
            "top_p": 0.9
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            'text': data.get('choices', [{}])[0].get('text', '').strip(),
            'tokens_used': data.get('usage', {}).get('total_tokens', 0)
        }
    def _build_prompt(self, request_type: str, context: Dict[str, Any]) -> str:
        """Build specialized prompt based on request type"""
    
        base_context = f"""
    You are an automotive validation expert at Capgemini Engineering with 20+ years of experience.

    PROJECT CONTEXT:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • Vehicle Category: {context.get('vehicle_category', 'N/A')}
    • Mi-Vie Modification: {'YES ✓' if context.get('is_mivie', False) else 'NO'}
    • Modification Zones: {', '.join(context.get('zones', []))}
    • Modification Level: {context.get('level', 'N/A')}
    • Target Markets: {', '.join(context.get('markets', []))}

    CURRENT VALIDATION PLAN:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • Total Tests: {context.get('num_tests', 0)}
    • Total Cost: €{context.get('total_cost', 0):,.0f}
    • Physical Duration: {context.get('total_days', 0)} days
    • Risk Score: {context.get('risk_score', 0):.1f}/100

    BUDGET & TIMELINE:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • Max Budget: €{context.get('max_budget', 'No limit')}
    • Max Duration: {context.get('max_duration', 'No limit')} days
    • Budget Status: {'❌ EXCEEDED' if context.get('budget_exceeded', False) else '✅ OK'}
    • Timeline Status: {'❌ EXCEEDED' if context.get('timeline_exceeded', False) else '✅ OK'}

    DETAILED SCORING BREAKDOWN:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    • Zone Coverage: {context.get('score_coverage', 0):.1f}/25 ({(context.get('score_coverage', 0)/25*100):.0f}%)
    • Regulatory Compliance: {context.get('score_regulatory', 0):.1f}/30 ({(context.get('score_regulatory', 0)/30*100):.0f}%)
    • Safety Criticality: {context.get('score_safety', 0):.1f}/25 ({(context.get('score_safety', 0)/25*100):.0f}%)
    • Timeline Feasibility: {context.get('score_timeline', 0):.1f}/100
    • Budget Feasibility: {context.get('score_budget', 0):.1f}/100

    SELECTED TESTS (First 15):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {context.get('test_list', 'No tests listed')}
    """
        
        if request_type == 'gap_analysis':
            return f"""{base_context}

    MISSION: COMPREHENSIVE GAP ANALYSIS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Analyze this validation plan and identify ALL critical gaps. Provide:

    1. **MISSING MANDATORY TESTS** (Critical Priority)
    • List each missing homologation test by exact name
    • Explain WHY each is mandatory for the target markets
    • State the regulatory reference (e.g., ECE R94, FMVSS 208)

    2. **UNCOVERED MODIFICATION ZONES** (High Priority)
    • Identify which zones lack sufficient test coverage
    • Recommend specific tests for each uncovered zone
    • Explain the risk of insufficient zone coverage

    3. **MISSING SAFETY-CRITICAL TESTS** (High Priority)
    • List missing crash tests, ADAS validations, braking tests
    • Explain safety implications of each missing test
    • Prioritize by severity

    4. **REGULATORY COMPLIANCE GAPS** (Medium Priority)
    • Check compliance for: {', '.join(context.get('markets', []))}
    • List market-specific requirements not yet covered
    • Warn about homologation rejection risks

    5. **ACTIONABLE RECOMMENDATIONS**
    • Provide 5-7 specific tests to add (with exact names)
    • Estimate cost and duration impact
    • Prioritize by urgency (CRITICAL / HIGH / MEDIUM)

    Format: Use bullet points, bold headers, and clear sections.
    Length: 500-700 words with detailed explanations.
    """
        
        elif request_type == 'optimization':
            return f"""{base_context}

    MISSION: COST & TIME OPTIMIZATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Current Issues:
    • Budget: {'EXCEEDED by €' + str(int(context.get('total_cost', 0) - context.get('max_budget', 0))) if context.get('budget_exceeded') else 'Within limits'}
    • Timeline: {'EXCEEDED by ' + str(int(context.get('total_days', 0) - context.get('max_duration', 0))) + ' days' if context.get('timeline_exceeded') else 'Within limits'}

    Provide detailed optimization strategies:

    1. **REPLACE PHYSICAL WITH NUMERICAL TESTS** (Highest Savings)
    • Identify 5-7 expensive physical tests that can be replaced
    • For each: "Replace [Test A] (€X, Y days) with [Numerical Test B] (€0, parallel execution)"
    • Calculate total savings: €XX,XXX and XX days

    2. **TEST BUNDLING OPPORTUNITIES** (Time Savings)
    • Group tests by location: {', '.join(context.get('test_locations', [])[:5])}
    • Example: "Bundle [Test 1, Test 2, Test 3] at IDIADA → Save €X in vehicle prep"
    • Identify shared equipment/setup opportunities

    3. **REMOVE REDUNDANT TESTS** (Cost Savings)
    • Find Tier 4 optional tests with minimal value
    • For each: "Remove [Test X] (€Y, Z days) - Reason: [Redundant with Test W]"
    • Ensure no regulatory/safety impact

    4. **PARALLEL EXECUTION STRATEGY** (Timeline Optimization)
    • Show which tests can run simultaneously
    • Example: "Run [Test A] at IDIADA while [Test B] at UTAC → Save 20 days"
    • Calculate optimized timeline

    5. **COST-BENEFIT ANALYSIS**
    • Summarize total potential savings
    • Show trade-offs (cost vs risk vs quality)
    • Recommend best approach based on priorities

    Format: Specific test names, exact cost/time figures, clear action items.
    Length: 600-800 words with calculations.
    """
        
        elif request_type == 'bundling':
            test_locations = context.get('test_locations', [])
            return f"""{base_context}

    MISSION: TEST BUNDLING & LOGISTICS OPTIMIZATION
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Test Facilities in Plan:
    {chr(10).join(f'  • {loc}' for loc in test_locations)}

    Analyze and provide:

    1. **LOCATION-BASED BUNDLING**
    • For each test center, list all tests that can be bundled
    • Example: "IDIADA Bundle: [Test 1, Test 2, Test 3] → Use same vehicle, save €8,000 prep cost"
    • Calculate cost savings per bundle

    2. **VEHICLE CONFIGURATION SHARING**
    • Identify tests requiring same vehicle setup
    • Group by configuration (e.g., "All tests needing Face Avant modifications")
    • Show vehicle re-use opportunities

    3. **EQUIPMENT SHARING**
    • Find tests using same equipment (MC - Full test equipment, etc.)
    • Suggest scheduling to minimize equipment conflicts
    • Calculate resource utilization improvements

    4. **SEQUENTIAL vs PARALLEL EXECUTION**
    • Create optimal test sequence at each facility
    • Example: "At UTAC: Run Tests A→B→C sequentially (15 days) OR A+B parallel, then C (10 days)"
    • Show timeline optimization per location

    5. **LOGISTICS & SCHEDULING PLAN**
    • Recommend vehicle transport sequence between facilities
    • Identify tests that MUST be sequential vs can overlap
    • Create week-by-week execution roadmap

    6. **COST SAVINGS BREAKDOWN**
    • Vehicle preparation: €X saved
    • Transport logistics: €Y saved
    • Equipment rental: €Z saved
    • Total bundling savings: €[X+Y+Z]

    Format: Tables, location-grouped lists, timeline diagrams in text.
    Length: 500-700 words with specific facility names and test combinations.
    """
        
        else:  # general
            return f"""{base_context}

    MISSION: COMPREHENSIVE VALIDATION PLAN ASSESSMENT
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Provide a holistic evaluation of this validation plan:

    OVERALL QUALITY ASSESSMENT (Score: X/10)
    • Strengths: What is well-covered?
    • Weaknesses: What major gaps exist?
    • Completeness: Are all modification zones validated?
    • Balance: Good mix of mandatory/recommended/optional tests?

    RISK ANALYSIS (Current Risk Score: {context.get('risk_score', 0):.1f}/100)
    • Technical risks: Insufficient testing in critical areas?
    • Regulatory risks: Homologation rejection probability?
    • Safety risks: Crash/ADAS validation adequacy?
    • Commercial risks: Market-specific compliance gaps?

    STRATEGIC RECOMMENDATION
    ✅ APPROVE: If risk score ≥85 and no critical gaps
    ⚠️ APPROVE WITH MODIFICATIONS: If 70-84, list required additions
    🔴 REJECT: If <70, explain why plan is insufficient

    RESOURCE ALLOCATION
    • Budget efficiency: €{context.get('total_cost', 0):,.0f} - Is this reasonable?
    • Timeline feasibility: {context.get('total_days', 0)} days - Realistic?
    • Personnel needs: How many engineers required?
    • Facility booking: Any capacity concerns?

    TOP 5 ACTION ITEMS (Prioritized)
    1. [CRITICAL] Action with immediate impact
    2. [HIGH] Important improvement
    3. [MEDIUM] Nice-to-have enhancement
    4. [LOW] Optional optimization
    5. [INFO] Additional consideration

    EXECUTIVE SUMMARY (3 sentences)
    • One-line verdict
    • Key strengths
    • Main concern

    Format: Clear sections, bold priorities, executive-friendly language.
    Length: 700-900 words with strategic insights.
    """

    def _fallback_rule_based_recommendation(
        self,
        request_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Enhanced rule-based recommendations with more detail"""
        
        risk_score = context.get('risk_score', 0)
        score_regulatory = context.get('score_regulatory', 0)
        score_coverage = context.get('score_coverage', 0)
        score_safety = context.get('score_safety', 0)
        score_budget = context.get('score_budget', 0)
        score_timeline = context.get('score_timeline', 0)
        total_cost = context.get('total_cost', 0)
        max_budget = context.get('max_budget', 0)
        total_days = context.get('total_days', 0)
        max_duration = context.get('max_duration', 0)
        
        recommendations = []
        
        if request_type == 'gap_analysis':
            recommendations.append("## 🔍 GAP ANALYSIS REPORT (Rule-Based)\n")
            
            if score_regulatory < 30:
                recommendations.append(f"""
    ### 🔴 CRITICAL: Missing Mandatory Homologation Tests

    **Issue:** Regulatory compliance score is only {(score_regulatory/30)*100:.0f}% (Target: 100%)

    **Required Actions:**
    1. Add ALL tests marked with 'X' in the homologation column
    2. Key mandatory tests typically include:
    - ECER94: Frontal Crash Test (40% offset, 56 km/h)
    - ECER95: Side Impact Test (50 km/h)
    - ECER135: Pole Side Impact (32 km/h)
    - WLTP Emissions Testing (for Europe)
    - Lighting & Signalization Homologation

    **Risk:** Plan will be REJECTED by homologation authorities without these tests.
    **Estimated Cost Impact:** +€50,000 - €80,000
    **Timeline Impact:** +30-60 days
    """)
            
            if score_coverage < 20:
                uncovered = set(context.get('zones', [])) - set(context.get('covered_zones', []))
                recommendations.append(f"""
    ### ⚠️ HIGH PRIORITY: Insufficient Zone Coverage

    **Issue:** Only {(score_coverage/25)*100:.0f}% of modification zones are adequately tested.

    **Uncovered Zones:** {', '.join(uncovered) if uncovered else 'Multiple zones need more tests'}

    **Recommended Actions:**
    1. Add durability tests for each modification zone
    2. Include étanchéité (sealing) tests for exterior zones
    3. Add bruits parasites (noise) tests for habitacle zones

    **Specific Test Suggestions:**
    - Face avant: Add "Essai gravillonnage" (stone impact resistance)
    - Habitacle: Add "Confort Acoustique" tests
    - Face arrière: Add "Essai étanchéité dynamique"

    **Risk:** Inadequate validation may lead to field failures and recalls.
    """)
            
            if score_safety < 15:
                recommendations.append(f"""
    ### 🔴 HIGH PRIORITY: Insufficient Safety Validation

    **Issue:** Safety test coverage is only {(score_safety/25)*100:.0f}% (Target: ≥80%)

    **Critical Missing Tests:**
    1. **Crash Tests:** Ensure frontal, lateral, and rear impact tests are included
    2. **ADAS Validation:** If vehicle has driver assistance systems
    3. **Braking Tests:** Freinage principal homologation
    4. **ESC Testing:** Electronic Stability Control validation

    **Regulatory Impact:** Many markets require comprehensive safety testing for homologation.
    **Estimated Additional Cost:** €40,000 - €100,000
    """)
        
        elif request_type == 'optimization':
            recommendations.append("## ⚡ COST & TIME OPTIMIZATION REPORT (Rule-Based)\n")
            
            if score_budget < 80 and max_budget > 0:
                over_budget = total_cost - max_budget
                recommendations.append(f"""
    ### 💰 BUDGET OPTIMIZATION NEEDED

    **Current Situation:**
    - Plan Cost: €{total_cost:,.0f}
    - Budget Limit: €{max_budget:,.0f}
    - **Overage: €{over_budget:,.0f} ({(over_budget/max_budget)*100:.1f}% over budget)**

    **Optimization Strategies:**

    1. **Replace Physical with Numerical Tests (€0 cost)**
    - Look for CAE/simulation alternatives
    - Examples: "Calcul bruits parasites" instead of physical noise tests
    - Potential savings: €15,000 - €30,000

    2. **Remove Tier 4 Optional Tests**
    - Focus on Tier 1 (mandatory) and Tier 2 (high priority) only
    - Review tests with necessity <40%
    - Potential savings: €10,000 - €25,000

    3. **Bundle Tests at Same Location**
    - Reduce vehicle preparation costs
    - Minimize transport between facilities
    - Potential savings: €5,000 - €15,000

    4. **Negotiate Multi-Test Packages**
    - Some test centers offer discounts for bundled bookings
    - Potential savings: 10-15% off total

    **Target:** Reduce cost to €{max_budget:,.0f} (need to cut €{over_budget:,.0f})
    """)
            
            if score_timeline < 70 and max_duration > 0:
                over_time = total_days - max_duration
                recommendations.append(f"""
    ### ⏱️ TIMELINE OPTIMIZATION NEEDED

    **Current Situation:**
    - Plan Duration: {total_days} days
    - Deadline: {max_duration} days
    - **Delay: {over_time} days ({(over_time/max_duration)*100:.1f}% over deadline)**

    **Acceleration Strategies:**

    1. **Parallel Execution at Multiple Facilities**
    - Run tests simultaneously at IDIADA, UTAC, and FEV
    - Can reduce timeline by 30-40%
    - Potential savings: {int(total_days * 0.35)} days

    2. **Prioritize Short-Duration Tests**
    - Remove tests >50 days duration
    - Focus on essential validation
    - Potential savings: {int(over_time * 0.6)} days

    3. **Fast-Track Homologation Tests**
    - Book priority slots at test centers
    - May cost +10% but saves 2-3 weeks

    **Target:** Complete in {max_duration} days (need to save {over_time} days)
    """)
        
        elif request_type == 'bundling':
            test_locations = context.get('test_locations', [])
            recommendations.append(f"""
    ## 📦 TEST BUNDLING OPPORTUNITIES (Rule-Based)

    **Test Facilities in Your Plan:** {len(test_locations)} locations

    **Bundling Strategy:**

    ### Location-Based Groups:
    """)
            
            for loc in test_locations[:5]:
                recommendations.append(f"""
    **{loc}:**
    - Bundle all tests at this facility to share vehicle setup
    - Estimated vehicle prep cost: €3,000-5,000 per vehicle
    - By using same vehicle for multiple tests: Save €2,000-4,000
    - Coordinate scheduling to minimize downtime
    """)
            
            recommendations.append("""
    ### Execution Timeline Optimization:
    1. **Week 1-2:** Tests at IDIADA (parallel execution)
    2. **Week 3-4:** Tests at UTAC (while IDIADA tests finalize)
    3. **Week 5-6:** Tests at other facilities

    ### Cost Savings Estimate:
    - Vehicle preparation bundling: €8,000 - €15,000
    - Transport optimization: €2,000 - €5,000
    - Equipment rental efficiency: €3,000 - €8,000
    - **Total Potential Savings: €13,000 - €28,000**
    """)
        
        else:  # general
            recommendations.append(f"""
    ## 📊 VALIDATION PLAN ASSESSMENT (Rule-Based)

    ### Overall Quality Score: {risk_score:.1f}/100

    **Plan Status:** {context.get('feasibility_status', 'UNKNOWN')}

    ### Scoring Breakdown:
    - ✅ Zone Coverage: {score_coverage:.1f}/25 ({(score_coverage/25)*100:.0f}%)
    - ✅ Regulatory: {score_regulatory:.1f}/30 ({(score_regulatory/30)*100:.0f}%)
    - ✅ Safety: {score_safety:.1f}/25 ({(score_safety/25)*100:.0f}%)
    - ✅ Budget: {score_budget:.1f}/100
    - ✅ Timeline: {score_timeline:.1f}/100

    ### Strategic Recommendation:
    """)
            
            if risk_score >= 85:
                recommendations.append("""
    **✅ APPROVE THIS PLAN**

    This validation plan is well-structured and comprehensive:
    - All mandatory requirements covered
    - Good balance of test types
    - Within budget and timeline constraints
    - Adequate safety and zone coverage

    **Next Steps:**
    1. Get stakeholder approval
    2. Book test facilities
    3. Prepare test vehicles
    4. Execute according to schedule
    """)
            elif risk_score >= 70:
                recommendations.append("""
    **⚠️ APPROVE WITH MODIFICATIONS**

    This plan is acceptable but needs improvements:
    - Add missing mandatory tests
    - Increase coverage in weak zones
    - Consider budget/timeline optimizations

    **Priority Actions:**
    1. Address regulatory gaps (if score < 100%)
    2. Add safety tests (if score < 80%)
    3. Improve zone coverage
    """)
            else:
                recommendations.append(f"""
    **🔴 PLAN NEEDS MAJOR REVISION**

    Risk score of {risk_score:.1f}/100 is too low for approval.

    **Critical Issues to Address:**
    - {'Missing mandatory homologation tests' if score_regulatory < 25 else ''}
    - {'Insufficient safety validation' if score_safety < 15 else ''}
    - {'Poor zone coverage' if score_coverage < 15 else ''}
    - {'Budget constraints not met' if score_budget < 50 else ''}

    **Recommendation:** Revise plan with a more comprehensive strategy.
    """)
        
        return "\n".join(recommendations)

    def _log_api_call(
        self,
        request_type: str,
        prompt_text: str,
        tokens_used: int,
        response_time_ms: int,
        success: bool,
        plan_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log API call to database"""
        log_entry = AICallLog(
            plan_id=plan_id,
            request_type=request_type,
            prompt_text=prompt_text,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message
        )
        
        self.db.add(log_entry)
        self.db.commit()

def get_usage_stats(self) -> Dict[str, Any]:
    """Get current week's usage statistics"""
    rate_limit = self.check_rate_limit()
    
    # Get success rate
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_calls = self.db.query(func.count(AICallLog.id)).filter(
        AICallLog.created_at >= week_start
    ).scalar()
    
    successful_calls = self.db.query(func.count(AICallLog.id)).filter(
        AICallLog.created_at >= week_start,
        AICallLog.success == True
    ).scalar()
    
    avg_response_time = self.db.query(func.avg(AICallLog.response_time_ms)).filter(
        AICallLog.created_at >= week_start,
        AICallLog.success == True
    ).scalar() or 0
    
    return {
        'calls_used': rate_limit['calls_used'],
        'calls_remaining': rate_limit['calls_remaining'],
        'success_rate': (successful_calls / total_calls * 100) if total_calls > 0 else 0,
        'avg_response_time_ms': int(avg_response_time),
        'resets_at': rate_limit['resets_at'].isoformat()
    }


def generate_ai_recommendation(
    db: Session,
    request_type: str,
    context: Dict[str, Any],
    plan_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate AI recommendations
    
    Usage:
        from app.ai_integration import generate_ai_recommendation
        
        result = generate_ai_recommendation(
            db=db,
            request_type='gap_analysis',
            context={
                'vehicle_category': 'M1',
                'zones': ['Face avant', 'Habitacle'],
                'risk_score': 75.5,
                ...
            },
            plan_id=123
        )
    """
    client = CapgeminiAIClient(db)
    return client.generate_recommendation(request_type, context, plan_id)


def get_ai_usage_stats(db: Session) -> Dict[str, Any]:
    """Get AI API usage statistics"""
    client = CapgeminiAIClient(db)
    return client.get_usage_stats()

def generate_recommendation(
    self,
    request_type: str,
    context: Dict[str, Any],
    plan_id: Optional[int] = None
) -> Dict[str, Any]:
    """Generate AI recommendation with cache busting"""
    
    # Add timestamp to make each request unique
    import time
    context['request_timestamp'] = time.time()
    context['request_id'] = f"{plan_id}_{request_type}_{int(time.time())}"
    
    # Check rate limit
    rate_limit_status = self.check_rate_limit()
    
    if not rate_limit_status['can_call']:
        return {
            'success': True,
            'recommendation': self._fallback_rule_based_recommendation(request_type, context),
            'used_ai': False,
            'rate_limit_exceeded': True,
            'resets_at': rate_limit_status['resets_at'].isoformat()
        }
    
    # Build prompt
    prompt = self._build_prompt(request_type, context)
    
    # Call API
    start_time = time.time()
    
    try:
        response = self._call_api(prompt)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log success
        self._log_api_call(
            plan_id=plan_id,
            request_type=request_type,
            prompt_text=prompt[:500],
            tokens_used=response.get('tokens_used', 0),
            response_time_ms=response_time_ms,
            success=True
        )
        
        return {
            'success': True,
            'recommendation': response['text'],
            'used_ai': True,
            'tokens_used': response.get('tokens_used', 0),
            'response_time_ms': response_time_ms
        }
    
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log failure
        self._log_api_call(
            plan_id=plan_id,
            request_type=request_type,
            prompt_text=prompt[:500],
            tokens_used=0,
            response_time_ms=response_time_ms,
            success=False,
            error_message=str(e)
        )
        
        # Fallback to rule-based
        return {
            'success': True,
            'recommendation': self._fallback_rule_based_recommendation(request_type, context),
            'used_ai': False,
            'error': str(e)
        }