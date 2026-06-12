import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib.units import inch
import charts

def generate_pdf_report(loan_data, base_details, sim_emi, sim_annual, sim_lump, combined_sim, refinance, health_score, health_status, score_deductions, alerts, ai_recommendations):
    """
    Creates a professional PDF report using ReportLab.
    Returns the PDF file contents as a bytes object.
    """
    buffer = io.BytesIO()
    
    # Page setup - 0.5 inch margins for data-rich layouts
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette to match UI
    bg_dark = colors.HexColor('#0F172A')
    panel_dark = colors.HexColor('#1E293B')
    accent_blue = colors.HexColor('#3B82F6')
    text_white = colors.HexColor('#F8FAFC')
    text_slate = colors.HexColor('#94A3B8')
    gold_savings = colors.HexColor('#EAB308')
    success_green = colors.HexColor('#10B981')
    warning_orange = colors.HexColor('#F59E0B')
    danger_red = colors.HexColor('#EF4444')
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=accent_blue,
        spaceAfter=4,
        alignment=0 # Left align
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        textColor=text_slate,
        spaceAfter=15,
        alignment=0
    )
    
    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=accent_blue,
        spaceBefore=15,
        spaceAfter=8,
        borderColor=accent_blue,
        borderWidth=1,
        borderRadius=4,
        borderPadding=5,
        backColor=colors.HexColor('#172554') # Deep navy background for headers
    )
    
    body_style = ParagraphStyle(
        'BodyTextWhite',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'), # Dark text for white paper print
        spaceBefore=4,
        spaceAfter=4
    )
    
    body_bold = ParagraphStyle(
        'BodyBoldText',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    alert_style = ParagraphStyle(
        'AlertText',
        parent=body_style,
        fontSize=9,
        textColor=colors.HexColor('#7F1D1D') # Deep red for warning block print
    )
    
    story = []
    
    # --- HEADER SECTION ---
    story.append(Paragraph("EMI Sense AI", title_style))
    story.append(Paragraph("AI-Powered Loan Optimization & Financial Advisor Report", subtitle_style))
    story.append(Paragraph(f"Report Generated On: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", body_style))
    story.append(Spacer(1, 10))
    
    # --- EXECUTIVE SUMMARY CARD ---
    currency = loan_data.get("currency", "₹")
    loan_type = loan_data.get("loan_type", "Custom Loan")
    
    summary_text = (
        f"This report outlines optimization strategies for your <b>{loan_type}</b>. "
        f"By implementing the recommended prepayment plans, you can significantly reduce "
        f"your total interest payment and shorten your debt timeline."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 15))
    
    # --- LOAN OVERVIEW TABLE ---
    story.append(Paragraph("1. Baseline Loan Summary", h1_style))
    
    table_data = [
        [Paragraph("<b>Financial Metric</b>", body_bold), Paragraph("<b>Value</b>", body_bold), Paragraph("<b>Optimized Metric</b>", body_bold), Paragraph("<b>Value</b>", body_bold)],
        ["Loan Type", loan_type, "Recommended Prepayment", f"{currency}{loan_data.get('extra_monthly_budget', 0.0):,.2f} / mo"],
        ["Principal Borrowed", f"{currency}{loan_data['loan_amount']:,.2f}", "New Adjusted EMI", f"{currency}{(base_details['emi'] + loan_data.get('extra_monthly_budget', 0.0)):,.2f}"],
        ["Interest Rate", f"{loan_data['interest_rate']}%", "Original Tenure", f"{loan_data['loan_tenure_months']} months"],
        ["Monthly EMI", f"{currency}{base_details['emi']:,.2f}", "New Optimized Tenure", f"{len(combined_sim)} months"],
        ["Total Interest Payable", f"{currency}{base_details['total_interest']:,.2f}", "Optimized Interest Payable", f"{currency}{sum(m['interest'] for m in combined_sim):,.2f}"],
        ["Total Amount Payable", f"{currency}{base_details['total_payment']:,.2f}", "Total Interest Saved", f"{currency}{(base_details['total_interest'] - sum(m['interest'] for m in combined_sim)):,.2f}"],
        ["Interest Contribution %", f"{base_details['interest_percentage']}%", "Years Saved", f"{round((base_details['actual_tenure_months'] - len(combined_sim))/12.0, 1)} years"]
    ]
    
    t1 = Table(table_data, colWidths=[2.0*inch, 1.5*inch, 2.3*inch, 1.5*inch])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))
    
    # --- LOAN HEALTH & FINANCIAL SECURITY ---
    story.append(Paragraph("2. Financial Health & Security Analysis", h1_style))
    health_text = (
        f"Your Loan Health Score is <b>{health_score}/100</b>, classifying the debt structure as <b>{health_status}</b>.<br/>"
        f"Your EMI consumes <b>{loan_data['emi_ratio']}%</b> of your monthly income (Recommended threshold is &lt; 30%)."
    )
    story.append(Paragraph(health_text, body_style))
    story.append(Spacer(1, 10))
    
    # Warnings table if any exist
    if alerts:
        alert_rows = [[Paragraph("<b>Severity</b>", body_bold), Paragraph("<b>Warning / Recommendation Alert</b>", body_bold)]]
        for a in alerts:
            sev = a["type"].upper()
            sev_color = danger_red if sev == "DANGER" else warning_orange if sev == "WARNING" else accent_blue
            alert_rows.append([
                Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", body_bold),
                Paragraph(a["message"], body_style)
            ])
            
        t_alerts = Table(alert_rows, colWidths=[1.2*inch, 6.1*inch])
        t_alerts.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFE4E6')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECDD3')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#FFF1F2')),
        ]))
        story.append(t_alerts)
        story.append(Spacer(1, 15))
        
    story.append(PageBreak()) # Move to next page for charts and optimization details
    
    # --- CHARTS SECTION ---
    story.append(Paragraph("3. Optimization Charts & Visualization", h1_style))
    
    # Render static charts using Matplotlib
    pie_bytes = charts.generate_static_pie_chart(loan_data['loan_amount'], base_details['total_interest'])
    timeline_bytes = charts.generate_static_timeline_chart(base_details['schedule'], combined_sim)
    
    img_pie = Image(io.BytesIO(pie_bytes), width=3.3*inch, height=2.2*inch)
    img_time = Image(io.BytesIO(timeline_bytes), width=4.0*inch, height=2.2*inch)
    
    # Place side by side in a layout table
    chart_table = Table([[img_pie, img_time]], colWidths=[3.4*inch, 4.0*inch])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(chart_table)
    story.append(Spacer(1, 15))
    
    # --- OPTIMIZATION SIMULATION COMPARISONS ---
    story.append(Paragraph("4. Optimization Simulations Comparison", h1_style))
    
    opt_table_data = [
        [
            Paragraph("<b>Optimization Strategy</b>", body_bold),
            Paragraph("<b>New EMI</b>", body_bold),
            Paragraph("<b>Tenure (Mo)</b>", body_bold),
            Paragraph("<b>Interest Saved</b>", body_bold),
            Paragraph("<b>Years Saved</b>", body_bold)
        ],
        [
            "Baseline Loan Schedule", 
            f"{currency}{base_details['emi']:,.2f}", 
            f"{base_details['actual_tenure_months']}", 
            "-", 
            "-"
        ],
        [
            f"EMI Increase (+{loan_data.get('emi_increase_pct', 10)}%)", 
            f"{currency}{sim_emi['new_emi']:,.2f}", 
            f"{sim_emi['new_tenure_months']}", 
            f"{currency}{sim_emi['interest_saved']:,.2f}", 
            f"{sim_emi['years_saved']} yrs"
        ],
        [
            f"Annual Prepayment", 
            f"{currency}{base_details['emi']:,.2f}", 
            f"{sim_annual['new_tenure_months']}", 
            f"{currency}{sim_annual['interest_saved']:,.2f}", 
            f"{sim_annual['years_saved']} yrs"
        ],
        [
            f"One-Time Lump Sum Payment", 
            f"{currency}{sim_lump['new_emi']:,.2f}", 
            f"{sim_lump['new_tenure_months']}", 
            f"{currency}{sim_lump['interest_saved']:,.2f}", 
            f"{sim_lump['years_saved']} yrs"
        ],
        [
            "Combined Strategy (All Above)",
            f"{currency}{(base_details['emi'] + loan_data.get('extra_monthly_budget', 0.0)):,.2f}",
            f"{len(combined_sim)}",
            f"{currency}{(base_details['total_interest'] - sum(m['interest'] for m in combined_sim)):,.2f}",
            f"{round((base_details['actual_tenure_months'] - len(combined_sim))/12.0, 1)} yrs"
        ]
    ]
    
    t_opt = Table(opt_table_data, colWidths=[2.3*inch, 1.2*inch, 1.1*inch, 1.5*inch, 1.2*inch])
    t_opt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,-2), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#FEF08A')), # Highlight combined row in gold
    ]))
    story.append(t_opt)
    story.append(Spacer(1, 15))
    
    # --- REFINANCING ANALYSIS ---
    if refinance:
        story.append(Paragraph("5. Refinancing Viability Assessment", h1_style))
        ref_status = "RECOMMENDED" if refinance["worth_refinancing"] else "NOT RECOMMENDED"
        ref_color = success_green if refinance["worth_refinancing"] else danger_red
        
        ref_text = (
            f"Analysis of balance transfer to rate <b>{loan_data.get('refinance_rate', 0.0)}%</b> with costs <b>{currency}{loan_data.get('refinance_cost', 0):,.2f}</b>:<br/>"
            f"Status: <b><font color='{ref_color}'>{ref_status}</font></b><br/>"
            f"Monthly EMI reduction: <b>{currency}{refinance['monthly_saving']:,.2f}</b><br/>"
            f"Gross interest savings over tenure: <b>{currency}{refinance['gross_interest_saved']:,.2f}</b><br/>"
            f"Net savings (after fees): <b>{currency}{refinance['net_savings']:,.2f}</b><br/>"
            f"Break-even point: <b>{refinance['break_even_months']} months</b>"
        )
        story.append(Paragraph(ref_text, body_style))
        story.append(Spacer(1, 15))
        
    story.append(PageBreak())
    
    # --- AI ADVICE & PERSONALIZED RECOMMENDATIONS ---
    story.append(Paragraph("6. AI Personalized Recommendations & Action Plan", h1_style))
    
    import re
    # Escape XML special characters
    clean_ai_recs = ai_recommendations.replace("&", "&amp;")
    
    # Properly map markdown bold to matching ReportLab HTML bold tags
    clean_ai_recs = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_ai_recs)
    
    # Map markdown headers
    clean_ai_recs = re.sub(r'### (.*?)(?:\n|$)', r'<b>\1</b><br/>', clean_ai_recs)
    clean_ai_recs = re.sub(r'## (.*?)(?:\n|$)', r'<b>\1</b><br/>', clean_ai_recs)
    
    # Replace emoji characters that standard PDF Helvetica font does not support
    emoji_replacements = {
        "💡": "*", "🏆": "*", "✅": "*", "🚨": "*", "⚠️": "*",
        "🥇": "1.", "🥈": "2.", "🥉": "3.", "💵": "INR", "📊": "Analysis:"
    }
    for emo, rep in emoji_replacements.items():
        clean_ai_recs = clean_ai_recs.replace(emo, rep)
        
    # Convert remaining newlines to breaks
    clean_ai_recs = clean_ai_recs.replace("\n", "<br/>")
    
    # Wrap in KeepTogether to ensure it doesn't break awkwardly
    story.append(Paragraph(clean_ai_recs, body_style))
    story.append(Spacer(1, 20))
    
    # --- DISCLAIMER ---
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=text_slate,
        alignment=1 # Center align
    )
    story.append(Spacer(1, 10))
    story.append(Paragraph("Disclaimer: This report is generated based on mathematical loan compounding models and AI heuristics. It is meant for educational and advisory purposes and does not constitute official legal or financial advice. Consult a certified financial planner before finalizing prepayment transfers.", disclaimer_style))
    
    # Build Document
    doc.build(story)
    
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
