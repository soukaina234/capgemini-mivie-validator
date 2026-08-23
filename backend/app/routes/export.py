"""
Export API endpoints
Handles PDF and Excel report generation
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import pandas as pd
from datetime import datetime
import os

from app.database import get_db
from app.models import ValidationPlan, PlanTest, Test
from app.config import settings

router = APIRouter()


def generate_pdf_report(plan_id: int, db: Session) -> str:
    """
    Generate PDF report for validation plan
    Returns: filepath to generated PDF
    """
    # Get plan data
    plan = db.query(ValidationPlan).filter(ValidationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    
    # Get tests
    plan_tests = db.query(PlanTest, Test).join(Test).filter(
        PlanTest.plan_id == plan_id
    ).all()
    
    # Create PDF filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"validation_plan_{plan_id}_{timestamp}.pdf"
    filepath = os.path.join(settings.EXPORT_TEMP_DIR, filename)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0066CC'),
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12
    )
    
    # Title
    story.append(Paragraph("CAPGEMINI ENGINEERING", title_style))
    story.append(Paragraph(f"Validation Plan Report: {plan.plan_name}", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Plan Information
    story.append(Paragraph("Plan Information", heading_style))
    
    info_data = [
        ['Plan ID:', str(plan.id)],
        ['Vehicle Category:', plan.vehicle_category],
        ['Mi-Vie Modification:', 'Yes' if plan.is_mivie else 'No'],
        ['Modification Zones:', ', '.join(plan.modification_zones)],
        ['Modification Level:', plan.modification_level],
        ['Target Markets:', ', '.join(plan.target_markets)],
        ['Strategy:', plan.strategy_type.upper()],
        ['Created:', plan.created_at.strftime("%Y-%m-%d %H:%M")]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6F2FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Feasibility Status
    story.append(Paragraph("Feasibility Assessment", heading_style))
    
    risk_score = float(plan.risk_score) if plan.risk_score else 0
    status = plan.feasibility_status
    
    # Color code status
    status_color = {
        'FEASIBLE': colors.green,
        'MARGINAL': colors.yellow,
        'RISKY': colors.orange,
        'IMPOSSIBLE': colors.red
    }.get(status, colors.grey)
    
    status_data = [
        ['Feasibility Status:', status],
        ['Risk Score:', f"{risk_score:.1f}/100"],
        ['Total Cost:', f"€{float(plan.total_cost):,.0f}" if plan.total_cost else "€0"],
        ['Physical Duration:', f"{plan.total_duration_physical} days"],
        ['Engineering Duration:', f"{plan.total_duration_engineering} days"]
    ]
    
    status_table = Table(status_data, colWidths=[2*inch, 4*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (1, 0), status_color),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white if status != 'MARGINAL' else colors.black),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Scoring Breakdown
    story.append(Paragraph("Detailed Scoring", heading_style))
    
    score_data = [
        ['Metric', 'Score', 'Max', 'Status'],
        ['Zone Coverage', f"{float(plan.score_coverage or 0):.1f}", '25', 
         '✓' if float(plan.score_coverage or 0) >= 20 else '✗'],
        ['Regulatory Compliance', f"{float(plan.score_regulatory or 0):.1f}", '30',
         '✓' if float(plan.score_regulatory or 0) >= 25 else '✗'],
        ['Safety Criticality', f"{float(plan.score_safety or 0):.1f}", '25',
         '✓' if float(plan.score_safety or 0) >= 20 else '✗'],
        ['Completeness', f"{float(plan.score_completeness or 0):.1f}", '10',
         '✓' if float(plan.score_completeness or 0) >= 7 else '✗'],
        ['Resource Efficiency', f"{float(plan.score_efficiency or 0):.1f}", '10',
         '✓' if float(plan.score_efficiency or 0) >= 5 else '✗'],
        ['Timeline Feasibility', f"{float(plan.score_timeline or 0):.1f}", '100',
         '✓' if float(plan.score_timeline or 0) >= 70 else '✗'],
        ['Budget Feasibility', f"{float(plan.score_budget or 0):.1f}", '100',
         '✓' if float(plan.score_budget or 0) >= 70 else '✗']
    ]
    
    score_table = Table(score_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
    ]))
    story.append(score_table)
    story.append(PageBreak())
    
    # Selected Tests
    story.append(Paragraph("Selected Tests", heading_style))
    
    # Group by tier
    tier_groups = {1: [], 2: [], 3: [], 4: []}
    for pt, test in plan_tests:
        tier_groups[pt.tier].append((pt, test))
    
    for tier in [1, 2, 3, 4]:
        if not tier_groups[tier]:
            continue
        
        story.append(Paragraph(f"Tier {tier} Tests ({len(tier_groups[tier])} tests)", styles['Heading3']))
        
        test_data = [['Test Name', 'Cost (€)', 'Duration (days)', 'Zone']]
        
        for pt, test in tier_groups[tier][:30]:  # Limit to 30 per tier for space
            test_data.append([
                test.nom_de_test[:50] + '...' if len(test.nom_de_test) > 50 else test.nom_de_test,
                f"{float(test.prix_euro):,.0f}" if test.prix_euro else "0",
                f"{float(test.duree_jours):.1f}" if test.duree_jours else "0",
                (test.zone_modification or 'N/A')[:30]
            ])
        
        test_table = Table(test_data, colWidths=[3*inch, 1*inch, 1*inch, 1.5*inch])
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
        ]))
        story.append(test_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Capgemini Engineering",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    
    return filepath


def generate_excel_report(plan_id: int, db: Session) -> str:
    """
    Generate Excel report for validation plan
    Returns: filepath to generated Excel file
    """
    # Get plan data
    plan = db.query(ValidationPlan).filter(ValidationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    
    # Get tests
    plan_tests = db.query(PlanTest, Test).join(Test).filter(
        PlanTest.plan_id == plan_id
    ).all()
    
    # Create Excel filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"validation_plan_{plan_id}_{timestamp}.xlsx"
    filepath = os.path.join(settings.EXPORT_TEMP_DIR, filename)
    
    # Create Excel writer
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        
        # Sheet 1: Plan Summary
        summary_data = {
            'Attribute': [
                'Plan ID', 'Plan Name', 'Vehicle Category', 'Mi-Vie', 
                'Modification Zones', 'Modification Level', 'Target Markets',
                'Strategy', 'Feasibility Status', 'Risk Score',
                'Total Tests', 'Total Cost (€)', 'Physical Duration (days)',
                'Engineering Duration (days)', 'Created At'
            ],
            'Value': [
                plan.id,
                plan.plan_name,
                plan.vehicle_category,
                'Yes' if plan.is_mivie else 'No',
                ', '.join(plan.modification_zones),
                plan.modification_level,
                ', '.join(plan.target_markets),
                plan.strategy_type,
                plan.feasibility_status,
                f"{float(plan.risk_score):.2f}" if plan.risk_score else "0",
                len(plan_tests),
                f"{float(plan.total_cost):,.2f}" if plan.total_cost else "0",
                plan.total_duration_physical,
                plan.total_duration_engineering,
                plan.created_at.strftime("%Y-%m-%d %H:%M")
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Plan Summary', index=False)
        
        # Sheet 2: Scoring
        scoring_data = {
            'Metric': [
                'Zone Coverage',
                'Regulatory Compliance',
                'Safety Criticality',
                'Completeness',
                'Resource Efficiency',
                'Timeline Feasibility',
                'Budget Feasibility',
                'TOTAL SCORE',
                'RISK SCORE'
            ],
            'Score': [
                float(plan.score_coverage or 0),
                float(plan.score_regulatory or 0),
                float(plan.score_safety or 0),
                float(plan.score_completeness or 0),
                float(plan.score_efficiency or 0),
                float(plan.score_timeline or 0),
                float(plan.score_budget or 0),
                sum([
                    float(plan.score_coverage or 0),
                    float(plan.score_regulatory or 0),
                    float(plan.score_safety or 0),
                    float(plan.score_completeness or 0),
                    float(plan.score_efficiency or 0)
                ]),
                float(plan.risk_score or 0)
            ],
            'Max Score': [25, 30, 25, 10, 10, 100, 100, 100, 100],
            'Percentage': [
                f"{(float(plan.score_coverage or 0)/25)*100:.1f}%",
                f"{(float(plan.score_regulatory or 0)/30)*100:.1f}%",
                f"{(float(plan.score_safety or 0)/25)*100:.1f}%",
                f"{(float(plan.score_completeness or 0)/10)*100:.1f}%",
                f"{(float(plan.score_efficiency or 0)/10)*100:.1f}%",
                                f"{float(plan.score_timeline or 0):.1f}%",
                f"{float(plan.score_budget or 0):.1f}%",
                f"{(sum([float(plan.score_coverage or 0), float(plan.score_regulatory or 0), float(plan.score_safety or 0), float(plan.score_completeness or 0), float(plan.score_efficiency or 0)])/100)*100:.1f}%",
                f"{float(plan.risk_score or 0):.1f}%"
            ]
        }
        scoring_df = pd.DataFrame(scoring_data)
        scoring_df.to_excel(writer, sheet_name='Scoring', index=False)
        
        # Sheet 3: All Tests
        tests_data = []
        for pt, test in plan_tests:
            tests_data.append({
                'Test ID': test.id,
                'Test Name': test.nom_de_test,
                'Tier': pt.tier,
                'Removable': 'Yes' if pt.is_removable else 'No',
                'Category': test.categorie_de_test,
                'Homologation': 'Yes' if test.test_homologation else 'No',
                'Cost (€)': float(test.prix_euro) if test.prix_euro else 0,
                'Duration (days)': float(test.duree_jours) if test.duree_jours else 0,
                'Zone': test.zone_modification,
                'Level': test.niveau_modification,
                'Location': test.lieu_realisation,
                'Necessity (%)': float(test.pourcentage_necessite) if test.pourcentage_necessite else 0,
                'Strategy': test.strategie_validation,
                'Markets': test.pays_commercialisation
            })
        
        tests_df = pd.DataFrame(tests_data)
        tests_df.to_excel(writer, sheet_name='All Tests', index=False)
        
        # Sheet 4: Tests by Tier
        for tier in [1, 2, 3, 4]:
            tier_tests = [t for t in tests_data if t['Tier'] == tier]
            if tier_tests:
                tier_df = pd.DataFrame(tier_tests)
                tier_df.to_excel(writer, sheet_name=f'Tier {tier} Tests', index=False)
        
        # Sheet 5: Cost Breakdown
        tier_costs = {1: 0, 2: 0, 3: 0, 4: 0}
        for pt, test in plan_tests:
            tier_costs[pt.tier] += float(test.prix_euro) if test.prix_euro else 0
        
        cost_data = {
            'Category': [
                'Tier 1 (Mandatory)',
                'Tier 2 (High Priority)',
                'Tier 3 (Medium Priority)',
                'Tier 4 (Optional)',
                'TOTAL'
            ],
            'Cost (€)': [
                tier_costs[1],
                tier_costs[2],
                tier_costs[3],
                tier_costs[4],
                sum(tier_costs.values())
            ],
            'Percentage': [
                f"{(tier_costs[1]/sum(tier_costs.values()))*100:.1f}%" if sum(tier_costs.values()) > 0 else "0%",
                f"{(tier_costs[2]/sum(tier_costs.values()))*100:.1f}%" if sum(tier_costs.values()) > 0 else "0%",
                f"{(tier_costs[3]/sum(tier_costs.values()))*100:.1f}%" if sum(tier_costs.values()) > 0 else "0%",
                f"{(tier_costs[4]/sum(tier_costs.values()))*100:.1f}%" if sum(tier_costs.values()) > 0 else "0%",
                "100%"
            ]
        }
        cost_df = pd.DataFrame(cost_data)
        cost_df.to_excel(writer, sheet_name='Cost Breakdown', index=False)
    
    return filepath


@router.get("/pdf/{plan_id}")
async def export_plan_to_pdf(plan_id: int, db: Session = Depends(get_db)):
    """
    Export validation plan to PDF
    Returns downloadable PDF file
    """
    try:
        filepath = generate_pdf_report(plan_id, db)
        
        return FileResponse(
            filepath,
            media_type='application/pdf',
            filename=os.path.basename(filepath),
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(filepath)}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/excel/{plan_id}")
async def export_plan_to_excel(plan_id: int, db: Session = Depends(get_db)):
    """
    Export validation plan to Excel
    Returns downloadable Excel file with multiple sheets
    """
    try:
        filepath = generate_excel_report(plan_id, db)
        
        return FileResponse(
            filepath,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(filepath),
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(filepath)}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")


@router.get("/formats")
def get_available_export_formats():
    """
    Get list of available export formats
    """
    return {
        'formats': [
            {
                'type': 'pdf',
                'name': 'PDF Report',
                'description': 'Comprehensive validation plan report with visual formatting',
                'endpoint': '/api/export/pdf/{plan_id}',
                'use_case': 'Client presentations, management approval'
            },
            {
                'type': 'excel',
                'name': 'Excel Workbook',
                'description': 'Multi-sheet Excel file with detailed test data',
                'endpoint': '/api/export/excel/{plan_id}',
                'use_case': 'Budget planning, detailed analysis, data manipulation'
            }
        ]
    }