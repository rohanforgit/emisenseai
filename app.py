import gradio as gr
import os
import json
import tempfile
from datetime import datetime
import pandas as pd

# Import modular engines
import calculations as calc
import charts
import ai_engine as ai
import pdf_generator as pdf

# Load styling stylesheet
with open("style.css", "r") as f:
    css_content = f.read()

# Define standard models per provider
PROVIDER_MODELS = {
    "Groq": [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b-specdec",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ],
    "OpenAI": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo"
    ],
    "HuggingFace": [
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta"
    ]
}

def update_model_choices(provider):
    """
    Updates the model dropdown selections based on selected AI provider.
    """
    models = PROVIDER_MODELS.get(provider, PROVIDER_MODELS["Groq"])
    return gr.Dropdown(choices=models, value=models[0])

def render_kpi_cards(emi, total_interest, total_payment, savings, health_score, health_status, debt_free_date, currency):
    """
    Generates standard visual KPI card blocks.
    """
    health_colors = {
        "Excellent": "success",
        "Good": "success",
        "Average": "info",
        "Poor": "warning",
        "Danger": "danger"
    }
    hc = health_colors.get(health_status, "info")
    
    if isinstance(debt_free_date, datetime):
        df_str = debt_free_date.strftime("%b %Y")
    else:
        df_str = str(debt_free_date)
        
    html = f"""
    <div class="kpi-grid">
      <div class="kpi-card border-accent">
        <div class="kpi-label">Monthly EMI</div>
        <div class="kpi-val accent">{currency}{emi:,.2f}</div>
        <div class="kpi-subtext">Baseline monthly EMI</div>
      </div>
      <div class="kpi-card border-danger">
        <div class="kpi-label">Interest Payable</div>
        <div class="kpi-val danger">{currency}{total_interest:,.2f}</div>
        <div class="kpi-subtext">Cumulative interest cost</div>
      </div>
      <div class="kpi-card border-accent">
        <div class="kpi-label">Total Payment</div>
        <div class="kpi-val">{currency}{total_payment:,.2f}</div>
        <div class="kpi-subtext">Principal + Interest</div>
      </div>
      <div class="kpi-card border-savings">
        <div class="kpi-label">Potential Savings</div>
        <div class="kpi-val savings">{currency}{savings:,.2f}</div>
        <div class="kpi-subtext">With prepayment plan</div>
      </div>
      <div class="kpi-card border-{hc}">
        <div class="kpi-label">Health Score</div>
        <div class="kpi-val {hc}">{health_score:.0f}/100</div>
        <div class="kpi-subtext">Status: {health_status}</div>
      </div>
      <div class="kpi-card border-success">
        <div class="kpi-label">Debt Free Date</div>
        <div class="kpi-val success">{df_str}</div>
        <div class="kpi-subtext">At optimized schedule</div>
      </div>
    </div>
    """
    return html

def render_alert_box(alerts):
    """
    Compiles HTML alert callouts.
    """
    if not alerts:
        return "<div class='alert-box success'>✅ <b>Financial Checklist Clear:</b> No high-risk items found on your loan parameters.</div>"
        
    html = ""
    for a in alerts:
        icon = "🚨" if a["type"] == "danger" else "⚠️" if a["type"] == "warning" else "💡" if a["type"] == "info" else "✅"
        html += f"""
        <div class="alert-box {a['type']}">
            <span style="font-size: 1.2rem; margin-right: 10px;">{icon}</span>
            <span>{a['message']}</span>
        </div>
        """
    return html

# Main callback calculations
def run_optimization_engine(
    loan_type, loan_amount, interest_rate, loan_tenure_months, 
    monthly_income, monthly_expenses, current_reserve, 
    extra_monthly_budget, annual_prepayment, lump_sum_amount, 
    emi_increase_pct, refinance_rate, refinance_cost, 
    risk_appetite, existing_investments, inflation, current_age, retirement_age,
    currency, api_key, api_provider, model_name
):
    # 1. Base loan details
    base = calc.calculate_base_loan_details(loan_amount, interest_rate, loan_tenure_months)
    
    # 2. Simulator runs
    sim_emi = calc.simulate_emi_increase(loan_amount, interest_rate, loan_tenure_months, emi_increase_pct)
    sim_annual = calc.simulate_annual_prepayment(loan_amount, interest_rate, loan_tenure_months, annual_prepayment)
    sim_lump = calc.simulate_lump_sum(loan_amount, interest_rate, loan_tenure_months, lump_sum_amount, mode="reduce_tenure")
    
    # 3. Combined Simulation (Extra monthly + annual + lump sum at month 1)
    combined_sim = calc.simulate_amortization(
        loan_amount, interest_rate, loan_tenure_months, 
        extra_monthly=extra_monthly_budget, 
        annual_prepayment=annual_prepayment, 
        lump_sum=lump_sum_amount, 
        lump_sum_month=1
    )
    combined_interest = sum(m["interest"] for m in combined_sim)
    combined_savings = base["total_interest"] - combined_interest
    combined_tenure = len(combined_sim)
    
    # 4. Specific calculations
    refinance = calc.calculate_refinancing(loan_amount, interest_rate, loan_tenure_months, refinance_rate, refinance_cost)
    emi_ratio, emi_status, emi_advice = calc.calculate_emi_to_income(base["emi"], monthly_income)
    em_fund = calc.calculate_emergency_fund(monthly_expenses, base["emi"], current_reserve)
    
    # Health score
    score, status, deductions = calc.calculate_health_score(
        loan_amount, interest_rate, loan_tenure_months, base["emi"],
        monthly_income, monthly_expenses, current_reserve, extra_monthly_budget, loan_type
    )
    
    # Smart alerts
    alerts = calc.generate_smart_alerts(loan_amount, interest_rate, loan_tenure_months, base["emi"], monthly_income, monthly_expenses, current_reserve)
    
    # Milestones
    milestones = calc.get_financial_milestones(current_age, retirement_age, loan_tenure_months, combined_tenure)
    
    # What-If
    what_if = calc.simulate_what_if_analysis(
        loan_amount, interest_rate, loan_tenure_months, monthly_income, monthly_expenses, current_reserve,
        extra_monthly_budget, risk_appetite, existing_investments, inflation, current_age, retirement_age
    )
    
    # Loan specific features
    specifics = calc.get_loan_specific_features(loan_type, loan_amount, interest_rate, loan_tenure_months, base["emi"])
    
    # Package data for AI model context
    loan_data = {
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "loan_tenure_months": loan_tenure_months,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "extra_monthly_budget": extra_monthly_budget,
        "annual_prepayment": annual_prepayment,
        "lump_sum_amount": lump_sum_amount,
        "emi_increase_pct": emi_increase_pct,
        "refinance_rate": refinance_rate,
        "refinance_cost": refinance_cost,
        "refinance_net_savings": refinance.get("net_savings", 0),
        "currency": currency,
        "emi_ratio": emi_ratio,
        "emergency_savings": current_reserve,
        "risk_appetite": risk_appetite,
        "loan_type": loan_type,
        "home_loan_special_savings": specifics.get("extra_emi_effect", {}).get("interest_saved", 0.0) if loan_type == "Home Loan" else 0.0,
        "home_loan_special_years": specifics.get("extra_emi_effect", {}).get("years_saved", 0.0) if loan_type == "Home Loan" else 0.0,
        "depreciation_text": str(specifics.get("depreciation_timeline", "N/A")) if loan_type == "Car Loan" else "N/A"
    }
    
    # Fetch AI advice
    ai_advice = ai.get_ai_recommendations(
        loan_data, base, sim_emi, sim_annual, sim_lump, refinance,
        score, status, deductions, api_provider, api_key, model_name
    )
    
    # Build charts
    c1 = charts.generate_emi_breakdown_chart(loan_amount, base["total_interest"])
    c2 = charts.generate_principal_remaining_chart(base["schedule"], combined_sim, "Combined Strategy")
    c3 = charts.generate_interest_paid_chart(base["schedule"], combined_sim, "Combined Strategy")
    c4 = charts.generate_principal_paid_chart(base["schedule"], combined_sim, "Combined Strategy")
    c5 = charts.generate_emi_increase_savings_chart(loan_amount, interest_rate, loan_tenure_months)
    c6 = charts.generate_lump_sum_savings_chart(loan_amount, interest_rate, loan_tenure_months)
    c7 = charts.generate_annual_prepayment_savings_chart(loan_amount, interest_rate, loan_tenure_months)
    c8 = charts.generate_rate_comparison_chart(loan_amount, loan_tenure_months, interest_rate)
    c9 = charts.generate_combined_timeline_chart(loan_amount, interest_rate, loan_tenure_months, extra_monthly_budget, annual_prepayment, lump_sum_amount)
    
    # Debt-free chart
    opt_months_emi = sim_emi["new_tenure_months"]
    opt_months_annual = sim_annual["new_tenure_months"]
    opt_months_lump = sim_lump["new_tenure_months"]
    c10 = charts.generate_debt_free_timeline_chart(current_age, loan_tenure_months, opt_months_emi, opt_months_annual, opt_months_lump, combined_tenure)
    
    # Format HTML Outputs
    kpi_html = render_kpi_cards(base["emi"], base["total_interest"], base["total_payment"], combined_savings, score, status, base["debt_free_date"] - (base["debt_free_date"] - datetime.now()) * (1 - (combined_tenure / loan_tenure_months)), currency)
    alert_html = render_alert_box(alerts)
    
    summary_markdown = f"""
### Base Loan Breakdown
* **Monthly EMI:** {currency}{base['emi']:,.2f}
* **Total Interest Payable:** {currency}{base['total_interest']:,.2f}
* **Total Repayment:** {currency}{base['total_payment']:,.2f}
* **Interest to Principal Ratio:** {base['interest_percentage']}% of total amount goes to interest!
* **Debt Free Date:** {base['debt_free_date'].strftime('%d %B %Y')} ({round(loan_tenure_months / 12.0, 1)} years duration)

### 📊 Base vs. Optimized Combined Schedule
* **New Optimized Tenure:** **{combined_tenure} months** (Saved **{round((loan_tenure_months - combined_tenure)/12.0, 1)} years**!)
* **Interest Payable with Optimizations:** {currency}{combined_interest:,.2f}
* **Net Financial Savings:** **{currency}{combined_savings:,.2f}**
"""
    
    sim_emi_txt = f"""
* **New Adjusted EMI:** {currency}{sim_emi['new_emi']:,.2f}
* **Interest Saved:** {currency}{sim_emi['interest_saved']:,.2f}
* **Years Trimmed Off Tenure:** {sim_emi['years_saved']} years
* **Remaining Months:** {sim_emi['new_tenure_months']} months
"""
    
    sim_annual_txt = f"""
* **Annual Extra Prepayment:** {currency}{annual_prepayment:,.2f} / year
* **Interest Saved:** {currency}{sim_annual['interest_saved']:,.2f}
* **Years Trimmed Off Tenure:** {sim_annual['years_saved']} years
* **Remaining Months:** {sim_annual['new_tenure_months']} months
"""

    sim_lump_txt = f"""
* **One-time Prepayment:** {currency}{lump_sum_amount:,.2f}
* **Interest Saved:** {currency}{sim_lump['interest_saved']:,.2f}
* **Years Trimmed Off Tenure:** {sim_lump['years_saved']} years
* **Remaining Months:** {sim_lump['new_tenure_months']} months
"""

    # Refinancing Text output
    ref_color = "green" if refinance["worth_refinancing"] else "red"
    refinance_txt = f"""
* **Current EMI:** {currency}{refinance['current_emi']:,.2f}
* **New Refinanced EMI:** {currency}{refinance['new_emi']:,.2f}
* **Monthly Savings:** {currency}{refinance['monthly_saving']:,.2f}
* **Gross Interest Saved:** {currency}{refinance['gross_interest_saved']:,.2f}
* **Refinancing Costs:** {currency}{refinance_cost:,.2f}
* **Net Lifetime Savings:** **{currency}{refinance['net_savings']:,.2f}**
* **Break-Even Point:** **{refinance['break_even_months']} months**
* **Refinance Recommendation:** <span style="color:{ref_color}; font-weight:bold;">{"RECOMMENDED" if refinance['worth_refinancing'] else "NOT RECOMMENDED (Net savings <= 0 or break-even is too long)"}</span>
"""

    # Advanced Analysis panel outputs
    emi_ratio_txt = f"""
### Debt-to-Income Ratio
* **Your EMI / Income Ratio:** **{emi_ratio}%**
* **Risk Classification:** <span style="font-weight:bold;">{emi_status}</span>
* **Advice:** {emi_advice}
"""

    em_fund_txt = f"""
### Emergency Runway Calculations
* **Monthly Outflow (Expenses + EMI):** {currency}{em_fund['monthly_outflow']:,.2f}
* **3-Month Buffer:** {currency}{em_fund['fund_3m']:,.2f}
* **6-Month Buffer (Recommended):** {currency}{em_fund['fund_6m']:,.2f}
* **12-Month Buffer:** {currency}{em_fund['fund_12m']:,.2f}
* **Current Reserve:** {currency}{em_fund['current_reserve']:,.2f}
* **Required Reserve Gap:** {currency}{em_fund['gap']:,.2f}
* **Runway Advice:** {em_fund['advice']}
"""

    score_details_txt = f"""
### Loan Health Index Score: {score}/100 ({status})
The health index checks interest rates, leverage levels, prepayment options, emergency funds, and overall cash buffers.

**Health Score Deductions / Areas of Concern:**
"""
    if deductions:
        for d in deductions:
            score_details_txt += f"\n- {d}"
    else:
        score_details_txt += "\n- Perfect score! Your loan and capital structures are highly optimized."

    milestones_txt = f"""
### Debt Payoff Milestones Timeline
* **Current Age:** {current_age}
* **Base Loan Payoff Age:** **{milestones['loan_end_age']}**
* **Optimized Loan Payoff Age:** **{milestones['debt_free_age']}**
* **Difference (Years Saved):** **{round(milestones['loan_end_age'] - milestones['debt_free_age'], 1)} years earlier!**
* **Retirement Age:** {retirement_age}
* **Retirement Runway Gap (Optimized):** You will be completely debt-free **{milestones['retirement_gap_opt']} years** before your retirement target.
* **Advisory:** {milestones['advice']}
"""

    # Prepay vs Invest txt
    p_vs_i = what_if["prepay_vs_invest"]
    prepay_vs_invest_txt = f"""
### Option A: Prepay Loan (Guaranteed Return)
* **Interest Rate Saved:** **{interest_rate}%**
* **Guaranteed Lifetime Interest Savings:** {currency}{p_vs_i['interest_saved_prepay']:,.2f}
* **Payoff speedup:** debt-free {p_vs_i['prepay_years_saved']} years faster.

### Option B: Invest Extra Budget (Expected Return)
* **Investment Profile:** {risk_appetite} Risk Profile
* **Expected Return Rate:** **{p_vs_i['investment_return_rate']}%**
* **Estimated Investment Value:** {currency}{p_vs_i['investment_value']:,.2f} (Profit: {currency}{p_vs_i['investment_profit']:,.2f})

### ⚖️ Comparison & Advice
* **Prepay Strategy Net Value:** {currency}{p_vs_i['prepay_strategy_value']:,.2f} (includes freed EMI compound value)
* **Advisor Suggestion:** {p_vs_i['advice']}
"""

    # What If Scenarios table
    what_if_headers = ["What-If Scenario Event", "Tenure Months", "Interest Saved / Extra Cost", "Years Trimmed"]
    what_if_data = [
        ["Higher Salary (+15% income)", str(what_if['higher_salary']['new_tenure_months']), f"{currency}{what_if['higher_salary']['interest_saved']:,.2f}", f"+{what_if['higher_salary']['years_saved']} yrs"],
        ["Lower Salary (-15% income)", str(what_if['lower_salary']['new_tenure_months']), f"-{currency}{abs(what_if['lower_salary']['interest_saved']):,.2f}", f"{what_if['lower_salary']['years_saved']} yrs"],
        ["Family Expansion (+30% expenses)", str(what_if['family_expansion']['new_tenure_months']), f"-{currency}{abs(what_if['family_expansion']['interest_saved']):,.2f}", f"{what_if['family_expansion']['years_saved']} yrs"],
        ["Interest Rate Jump (+2.0%)", f"{loan_tenure_months} (fixed)", f"Cost: +{currency}{what_if['rate_increase']['interest_difference']:,.2f}", "0 (EMI Adjusted)"],
        ["Interest Rate Drop (-2.0%)", f"{loan_tenure_months} (fixed)", f"Saved: {currency}{abs(what_if['rate_decrease']['interest_difference']):,.2f}", "0 (EMI Adjusted)"]
    ]
    df_what_if = pd.DataFrame(what_if_data, columns=what_if_headers)
    
    # Save parameters for PDF export cache in state or file
    # We will generate the PDF immediately and output the path for download
    pdf_data = pdf.generate_pdf_report(
        loan_data, base, sim_emi, sim_annual, sim_lump, combined_sim, refinance,
        score, status, deductions, alerts, ai_advice
    )
    
    # Save PDF data to a temp file
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, "EMI_Sense_AI_Report.pdf")
    with open(pdf_path, "wb") as f_pdf:
        f_pdf.write(pdf_data)
        
    # Return everything
    return (
        kpi_html, alert_html, summary_markdown, ai_advice,
        sim_emi_txt, c5,
        sim_annual_txt, c7,
        sim_lump_txt, c6,
        refinance_txt, c8,
        emi_ratio_txt, em_fund_txt, score_details_txt, milestones_txt,
        df_what_if, prepay_vs_invest_txt,
        c1, c2, c3, c4, c9, c10,
        pdf_path,
        gr.update(selected="tab_diagnostic")
    )

# Sidebar helper actions
def reset_inputs():
    """
    Resets all input forms back to defaults.
    """
    return [
        "Home Loan", 5000000.0, 8.5, 240, 200000.0, 80000.0, 400000.0,
        20000.0, 100000.0, 200000.0, 10.0, 8.0, 10000.0, "Moderate", 500000.0,
        6.0, 30, 60, "₹", "Groq"
    ]

# Chatbot handler
def chat_callback(message, history, loan_type, loan_amount, interest_rate, loan_tenure_months, 
                  monthly_income, extra_monthly_budget, current_reserve, annual_prepayment, lump_sum_amount,
                  currency, api_key, api_provider, model_name):
    # Recompute quick metrics for LLM context
    base = calc.calculate_base_loan_details(loan_amount, interest_rate, loan_tenure_months)
    sim_emi = calc.simulate_emi_increase(loan_amount, interest_rate, loan_tenure_months, 10.0) # default 10%
    sim_annual = calc.simulate_annual_prepayment(loan_amount, interest_rate, loan_tenure_months, annual_prepayment)
    sim_lump = calc.simulate_lump_sum(loan_amount, interest_rate, loan_tenure_months, lump_sum_amount, mode="reduce_tenure")
    
    score, status, _ = calc.calculate_health_score(
        loan_amount, interest_rate, loan_tenure_months, base["emi"],
        monthly_income, 80000.0, current_reserve, extra_monthly_budget, loan_type
    )
    
    loan_data = {
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "loan_tenure_months": loan_tenure_months,
        "monthly_income": monthly_income,
        "extra_monthly_budget": extra_monthly_budget,
        "emergency_savings": current_reserve,
        "currency": currency,
        "loan_type": loan_type
    }
    
    response = ai.chat_with_coach(
        history, message, loan_data, base, score, status, sim_emi, sim_annual, sim_lump,
        api_provider, api_key, model_name
    )
    
    history.append((message, response))
    return history, ""

# Compare loans callback
def compare_loans(
    loan_type_a, loan_amount_a, interest_rate_a, loan_tenure_a,
    loan_type_b, loan_amount_b, interest_rate_b, loan_tenure_b,
    currency
):
    base_a = calc.calculate_base_loan_details(loan_amount_a, interest_rate_a, loan_tenure_a)
    base_b = calc.calculate_base_loan_details(loan_amount_b, interest_rate_b, loan_tenure_b)
    
    comparison_headers = ["Financial Parameter", "Loan Option A", "Loan Option B", "Difference"]
    comparison_rows = [
        ["Loan Type", loan_type_a, loan_type_b, "-"],
        ["Principal Borrowed", f"{currency}{loan_amount_a:,.2f}", f"{currency}{loan_amount_b:,.2f}", f"{currency}{(loan_amount_a - loan_amount_b):,.2f}"],
        ["Interest Rate", f"{interest_rate_a}%", f"{interest_rate_b}%", f"{round(interest_rate_a - interest_rate_b, 2)}%"],
        ["Tenure (Months)", f"{loan_tenure_a} months", f"{loan_tenure_b} months", f"{loan_tenure_a - loan_tenure_b} months"],
        ["Monthly EMI", f"{currency}{base_a['emi']:,.2f}", f"{currency}{base_b['emi']:,.2f}", f"{currency}{(base_a['emi'] - base_b['emi']):,.2f}"],
        ["Total Interest Payable", f"{currency}{base_a['total_interest']:,.2f}", f"{currency}{base_b['total_interest']:,.2f}", f"{currency}{(base_a['total_interest'] - base_b['total_interest']):,.2f}"],
        ["Total Repayment", f"{currency}{base_a['total_payment']:,.2f}", f"{currency}{base_b['total_payment']:,.2f}", f"{currency}{(base_a['total_payment'] - base_b['total_payment']):,.2f}"],
        ["Interest % of Payment", f"{base_a['interest_percentage']}%", f"{base_b['interest_percentage']}%", f"{round(base_a['interest_percentage'] - base_b['interest_percentage'], 2)}%"]
    ]
    return pd.DataFrame(comparison_rows, columns=comparison_headers)

# JSON session save/load
def save_session_config(
    loan_type, loan_amount, interest_rate, loan_tenure_months, 
    monthly_income, monthly_expenses, current_reserve, 
    extra_monthly_budget, annual_prepayment, lump_sum_amount, 
    emi_increase_pct, refinance_rate, refinance_cost, 
    risk_appetite, existing_investments, inflation, current_age, retirement_age,
    currency
):
    config = {
        "loan_type": loan_type, "loan_amount": loan_amount, "interest_rate": interest_rate,
        "loan_tenure_months": loan_tenure_months, "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses, "current_reserve": current_reserve,
        "extra_monthly_budget": extra_monthly_budget, "annual_prepayment": annual_prepayment,
        "lump_sum_amount": lump_sum_amount, "emi_increase_pct": emi_increase_pct,
        "refinance_rate": refinance_rate, "refinance_cost": refinance_cost,
        "risk_appetite": risk_appetite, "existing_investments": existing_investments,
        "inflation": inflation, "current_age": current_age, "retirement_age": retirement_age,
        "currency": currency
    }
    
    temp_dir = tempfile.gettempdir()
    config_path = os.path.join(temp_dir, "emi_sense_session.json")
    with open(config_path, "w") as f_cfg:
        json.dump(config, f_cfg, indent=4)
        
    return config_path

def load_session_config(file_obj):
    if file_obj is None:
        return [gr.update() for _ in range(19)]
        
    try:
        with open(file_obj.name, "r") as f_cfg:
            config = json.load(f_cfg)
            
        return [
            config.get("loan_type", "Home Loan"),
            config.get("loan_amount", 5000000.0),
            config.get("interest_rate", 8.5),
            config.get("loan_tenure_months", 240),
            config.get("monthly_income", 200000.0),
            config.get("monthly_expenses", 80000.0),
            config.get("current_reserve", 400000.0),
            config.get("extra_monthly_budget", 20000.0),
            config.get("annual_prepayment", 100000.0),
            config.get("lump_sum_amount", 200000.0),
            config.get("emi_increase_pct", 10.0),
            config.get("refinance_rate", 8.0),
            config.get("refinance_cost", 10000.0),
            config.get("risk_appetite", "Moderate"),
            config.get("existing_investments", 500000.0),
            config.get("inflation", 6.0),
            config.get("current_age", 30),
            config.get("retirement_age", 60),
            config.get("currency", "₹")
        ]
    except Exception as e:
        print(f"Error loading session: {str(e)}")
        # Return updates unchanged
        return [gr.update() for _ in range(19)]


# --- GRADIO INTERFACE LAYOUT ---
with gr.Blocks(title="EMI Sense AI - Loan Optimization Dashboard", css=css_content) as demo:
    
    # Custom Application Header
    gr.HTML("""
    <div class="app-header">
        <h1>EMI Sense AI</h1>
        <p>💡 "Don't just calculate your loan. Optimize it." — Premium AI-Powered Financial Loan Optimization Advisor</p>
    </div>
    """)
    
    with gr.Row():
        # --- LEFT SIDEBAR PANEL (SCROLLABLE CONFIGURATION) ---
        with gr.Column(scale=1, elem_classes="sidebar-panel"):
            gr.HTML("""
            <div style="text-align: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #3B82F6; font-size: 1.35rem; font-weight: 700;">EMI Sense AI</h3>
                <span style="font-size: 0.8rem; color: #94A3B8;">Loan Optimization System</span>
            </div>
            """)
            
            # Group 1: AI Configuration
            with gr.Accordion("🔑 AI Coach Settings", open=False):
                api_provider = gr.Dropdown(choices=["Groq", "OpenAI", "HuggingFace"], label="AI Provider", value="Groq")
                api_key = gr.Textbox(label="API Access Key", placeholder="Enter key (sk-...) to activate AI features", type="password")
                models = PROVIDER_MODELS["Groq"]
                model_name = gr.Dropdown(choices=models, label="AI Model", value=models[0], allow_custom_value=True)
                api_provider.change(update_model_choices, inputs=[api_provider], outputs=[model_name])
                
            # Group 2: Core Loan Details
            with gr.Accordion("💵 Core Loan Details", open=True):
                currency = gr.Dropdown(choices=["₹", "$", "€", "£", "¥"], label="Currency Symbol", value="₹")
                loan_type = gr.Dropdown(
                    choices=["Home Loan", "Car Loan", "Bike Loan", "Education Loan", "Personal Loan", "Business Loan", "Gold Loan", "Custom Loan"], 
                    label="Loan Classification", 
                    value="Home Loan"
                )
                loan_amount = gr.Number(label="Loan Principal Amount", value=5000000.0, precision=2)
                interest_rate = gr.Slider(minimum=0.0, maximum=30.0, step=0.1, label="Interest Rate (% Annual)", value=8.5)
                loan_tenure_months = gr.Slider(minimum=12, maximum=480, step=12, label="Loan Tenure (Months)", value=240)
                
            # Group 3: Cash Flow & Security Reserves
            with gr.Accordion("🛡️ Cash Flow & Security Reserves", open=True):
                monthly_income = gr.Number(label="Monthly Net Income", value=200000.0)
                monthly_expenses = gr.Number(label="Monthly Living Expenses", value=80000.0)
                current_reserve = gr.Number(label="Emergency Cash Reserve", value=400000.0)
                extra_monthly_budget = gr.Number(label="Extra Monthly Prepay Budget", value=20000.0)
                
            # Group 4: Risk & Strategy Profile
            with gr.Accordion("⚖️ Risk & Strategy Profile", open=False):
                risk_appetite = gr.Dropdown(choices=["Conservative", "Moderate", "Aggressive"], label="Risk Appetite", value="Moderate")
                existing_investments = gr.Number(label="Existing Investments Total", value=500000.0)
                inflation = gr.Slider(minimum=0.0, maximum=15.0, step=0.5, label="Expected Inflation Rate (%)", value=6.0)
                current_age = gr.Slider(minimum=18, maximum=80, label="Your Current Age", value=30)
                retirement_age = gr.Slider(minimum=40, maximum=90, label="Expected Retirement Age", value=60)
                
            # Group 5: Session Controls & PDF
            with gr.Accordion("💾 Session Controls & PDF", open=False):
                btn_reset = gr.Button("🔄 Reset Dashboard", elem_classes="btn-secondary")
                gr.Markdown("### 📄 Export PDF Report")
                export_pdf_btn = gr.File(label="Download Generated PDF Report", interactive=False)
                gr.Markdown("### 💾 Session File")
                btn_save_session = gr.Button("📂 Save Config File", elem_classes="btn-secondary")
                session_file_download = gr.File(label="Config File Download", interactive=False)
                session_file_upload = gr.File(label="Upload Session Config File", file_types=[".json"])
                
            gr.Markdown("---")
            btn_calc = gr.Button("🚀 Calculate & Optimize", elem_classes="btn-primary", size="lg")

        # --- MAIN BODY DISPLAY (RIGHT COLUMN TABS) ---
        with gr.Column(scale=3):
            
            # Tabs for layout structure (No Configure/Input Tab here)
            with gr.Tabs(elem_classes="tabs-container") as tabs_container:
                
                # Tab 1: Dashboard Overview
                with gr.TabItem("📊 Advisor Diagnostic & AI Recommendation", id="tab_diagnostic"):
                    
                    # Result Display components placed inside this tab!
                    kpi_display = gr.HTML(label="Key Indicators")
                    alert_display = gr.HTML(label="Risk Alerts")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("### 📌 Executive Loan Analysis Summary")
                            summary_display = gr.Markdown("Click 'Calculate & Optimize' to run financial models...")
                        with gr.Column(scale=3):
                            gr.Markdown("### 🏆 AI Coach Recommendations & Top Actions")
                            ai_display = gr.Markdown("Provide your API key and click Calculate to receive personalized AI recommendations.")
                            
                    gr.Markdown("---")
                    
                    # AI chatbot coach row
                    gr.Markdown("### 💬 AI Loan Coach Chat Room")
                    chatbot = gr.Chatbot(label="EMI Sense Loan Coach Chatbot", height=300)
                    with gr.Row():
                        chat_msg = gr.Textbox(placeholder="Ask your loan coach (e.g. 'Should I pay a lump sum or increase my EMI?')", scale=4, show_label=False)
                        chat_send = gr.Button("💬 Send Question", scale=1, elem_classes="btn-primary")
                
                # Tab 2: Interactive Optimizations
                with gr.TabItem("⚡ Real-time Prepayment Simulators"):
                    gr.Markdown("Use the controls below to run real-time what-if simulations on prepayments and interest rates.")
                    
                    with gr.Row():
                        with gr.Column(elem_classes="premium-card"):
                            gr.Markdown("### 📈 EMI Increase Simulator")
                            emi_increase_pct = gr.Slider(minimum=0, maximum=100, step=5, label="Increase Monthly EMI By %", value=10)
                            emi_inc_out = gr.Markdown()
                            chart_emi_inc = gr.Plot(label="EMI Increase Savings")
                            
                        with gr.Column(elem_classes="premium-card"):
                            gr.Markdown("### 💰 One-Time Lump Sum Simulator")
                            lump_sum_amount = gr.Number(label="Lump Sum Prepayment Amount", value=200000.0)
                            lump_out = gr.Markdown()
                            chart_lump = gr.Plot(label="Lump Sum Savings")
                            
                    with gr.Row():
                        with gr.Column(elem_classes="premium-card"):
                            gr.Markdown("### 🗓️ Recurring Annual Prepayment Simulator")
                            annual_prepayment = gr.Number(label="Annual Prepayment Amount", value=100000.0)
                            annual_out = gr.Markdown()
                            chart_annual = gr.Plot(label="Annual Prepayment Savings")
                            
                        with gr.Column(elem_classes="premium-card"):
                            gr.Markdown("### 🔄 Balance Transfer & Refinance Analyzer")
                            refinance_rate = gr.Slider(minimum=4.0, maximum=20.0, step=0.1, label="Target Refinance Interest Rate (%)", value=8.0)
                            refinance_cost = gr.Number(label="Refinancing Cost / Balance Transfer Fees", value=10000.0)
                            refinance_out = gr.Markdown()
                            chart_rate_comp = gr.Plot(label="Interest Rate Savings")
                            
                # Tab 3: Advanced Analyses
                with gr.TabItem("🔍 Risk & Strategic Analyses"):
                    with gr.Row():
                        with gr.Column(scale=1, elem_classes="premium-card"):
                            emi_ratio_display = gr.Markdown()
                            
                        with gr.Column(scale=1, elem_classes="premium-card"):
                            emergency_fund_display = gr.Markdown()
                            
                    with gr.Row():
                        with gr.Column(scale=1, elem_classes="premium-card"):
                            score_details_display = gr.Markdown()
                            
                        with gr.Column(scale=1, elem_classes="premium-card"):
                            milestones_display = gr.Markdown()
                            
                    gr.Markdown("---")
                    
                    with gr.Row():
                        with gr.Column(scale=3, elem_classes="premium-card"):
                            gr.Markdown("### 🌪️ Advanced What-If Scenario Simulations Matrix")
                            df_what_if_display = gr.DataFrame(label="Scenario Matrix Table")
                            
                        with gr.Column(scale=2, elem_classes="premium-card"):
                            gr.Markdown("### ⚖️ Prepay vs. Investment Growth Trade-off")
                            prepay_vs_invest_display = gr.Markdown()
                            
                    gr.Markdown("---")
                    
                    # Scenario comparison sub-panel
                    with gr.Group():
                        gr.Markdown("### 👥 Compare Two Distinct Loan Structures")
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("**Structure A Parameters**")
                                comp_type_a = gr.Dropdown(choices=["Home Loan", "Car Loan", "Personal Loan", "Custom Loan"], label="Loan A Type", value="Home Loan")
                                comp_amt_a = gr.Number(label="Loan A Amount", value=5000000.0)
                                comp_rate_a = gr.Slider(minimum=0.0, maximum=30.0, step=0.1, label="Loan A Rate", value=8.5)
                                comp_tenure_a = gr.Slider(minimum=12, maximum=480, step=12, label="Loan A Tenure (Months)", value=240)
                            with gr.Column():
                                gr.Markdown("**Structure B Parameters**")
                                comp_type_b = gr.Dropdown(choices=["Home Loan", "Car Loan", "Personal Loan", "Custom Loan"], label="Loan B Type", value="Car Loan")
                                comp_amt_b = gr.Number(label="Loan B Amount", value=5000000.0)
                                comp_rate_b = gr.Slider(minimum=0.0, maximum=30.0, step=0.1, label="Loan B Rate", value=7.5)
                                comp_tenure_b = gr.Slider(minimum=12, maximum=480, step=12, label="Loan B Tenure (Months)", value=180)
                        
                        btn_compare = gr.Button("⚔️ Run Side-By-Side Comparison Table", elem_classes="btn-primary")
                        df_comparison = gr.DataFrame(label="Comparison Result Sheet Table")
                        
                        btn_compare.click(
                            compare_loans,
                            inputs=[comp_type_a, comp_amt_a, comp_rate_a, comp_tenure_a, comp_type_b, comp_amt_b, comp_rate_b, comp_tenure_b, currency],
                            outputs=[df_comparison]
                        )
                        
                # Tab 4: Interactive Charts
                with gr.TabItem("📈 interactive Schedules & Timelines Charts"):
                    gr.Markdown("Select tabs below to zoom, hover, and analyze details of the amortization timelines.")
                    
                    with gr.Tabs():
                        with gr.TabItem("EMI Composition"):
                            chart_pie = gr.Plot()
                        with gr.TabItem("Principal Outstanding"):
                            chart_pr_rem = gr.Plot()
                        with gr.TabItem("Cumulative Interest"):
                            chart_int_cum = gr.Plot()
                        with gr.TabItem("Cumulative Principal"):
                            chart_pr_cum = gr.Plot()
                        with gr.TabItem("Baseline vs Prepay Strategy"):
                            chart_comb_time = gr.Plot()
                        with gr.TabItem("Debt-Free Age Milestone"):
                            chart_df_milestone = gr.Plot()
 
    # BIND BUTTON ACTION CALBACKS
    btn_calc.click(
        run_optimization_engine,
        inputs=[
            loan_type, loan_amount, interest_rate, loan_tenure_months,
            monthly_income, monthly_expenses, current_reserve,
            extra_monthly_budget, annual_prepayment, lump_sum_amount,
            emi_increase_pct, refinance_rate, refinance_cost,
            risk_appetite, existing_investments, inflation, current_age, retirement_age,
            currency, api_key, api_provider, model_name
        ],
        outputs=[
            kpi_display, alert_display, summary_display, ai_display,
            emi_inc_out, chart_emi_inc,
            annual_out, chart_annual,
            lump_out, chart_lump,
            refinance_out, chart_rate_comp,
            emi_ratio_display, emergency_fund_display, score_details_display, milestones_display,
            df_what_if_display, prepay_vs_invest_display,
            chart_pie, chart_pr_rem, chart_int_cum, chart_pr_cum, chart_comb_time, chart_df_milestone,
            export_pdf_btn,
            tabs_container
        ]
    )
    
    # Real-time sliders bindings for reactive updates
    # When sliders change, we update their sections instantly via local calculations without hitting AI API
    def reactive_emi_change(principal, rate, tenure, pct, currency):
        res = calc.simulate_emi_increase(principal, rate, tenure, pct)
        txt = f"""
* **New Adjusted EMI:** {currency}{res['new_emi']:,.2f}
* **Interest Saved:** {currency}{res['interest_saved']:,.2f}
* **Years Trimmed Off Tenure:** {res['years_saved']} years
* **Remaining Months:** {res['new_tenure_months']} months
"""
        c = charts.generate_emi_increase_savings_chart(principal, rate, tenure)
        return txt, c
        
    emi_increase_pct.change(
        reactive_emi_change,
        inputs=[loan_amount, interest_rate, loan_tenure_months, emi_increase_pct, currency],
        outputs=[emi_inc_out, chart_emi_inc]
    )

    def reactive_lump_change(principal, rate, tenure, amt, currency):
        res = calc.simulate_lump_sum(principal, rate, tenure, amt, mode="reduce_tenure")
        txt = f"""
* **One-time Prepayment:** {currency}{amt:,.2f}
* **Interest Saved:** {currency}{res['interest_saved']:,.2f}
* **Years Trimmed Off Tenure:** {res['years_saved']} years
* **Remaining Months:** {res['new_tenure_months']} months
"""
        c = charts.generate_lump_sum_savings_chart(principal, rate, tenure)
        return txt, c
        
    lump_sum_amount.change(
        reactive_lump_change,
        inputs=[loan_amount, interest_rate, loan_tenure_months, lump_sum_amount, currency],
        outputs=[lump_out, chart_lump]
    )

    def reactive_annual_change(principal, rate, tenure, amt, currency):
        res = calc.simulate_annual_prepayment(principal, rate, tenure, amt)
        txt = f"""
* **Annual Extra Prepayment:** {currency}{amt:,.2f} / year
* **Interest Saved:** {currency}{res['interest_saved']:,.2f}
* **Years Trimmed Off Tenure:** {res['years_saved']} years
* **Remaining Months:** {res['new_tenure_months']} months
"""
        c = charts.generate_annual_prepayment_savings_chart(principal, rate, tenure)
        return txt, c
        
    annual_prepayment.change(
        reactive_annual_change,
        inputs=[loan_amount, interest_rate, loan_tenure_months, annual_prepayment, currency],
        outputs=[annual_out, chart_annual]
    )

    def reactive_refinance_change(principal, current_rate, tenure, new_rate, cost, currency):
        res = calc.calculate_refinancing(principal, current_rate, tenure, new_rate, cost)
        ref_color = "green" if res["worth_refinancing"] else "red"
        txt = f"""
* **Current EMI:** {currency}{res['current_emi']:,.2f}
* **New Refinanced EMI:** {currency}{res['new_emi']:,.2f}
* **Monthly Savings:** {currency}{res['monthly_saving']:,.2f}
* **Gross Interest Saved:** {currency}{res['gross_interest_saved']:,.2f}
* **Refinancing Costs:** {currency}{cost:,.2f}
* **Net Lifetime Savings:** **{currency}{res['net_savings']:,.2f}**
* **Break-Even Point:** **{res['break_even_months']} months**
* **Refinance Recommendation:** <span style="color:{ref_color}; font-weight:bold;">{"RECOMMENDED" if res['worth_refinancing'] else "NOT RECOMMENDED"}</span>
"""
        c = charts.generate_rate_comparison_chart(principal, tenure, current_rate)
        return txt, c
        
    refinance_rate.change(
        reactive_refinance_change,
        inputs=[loan_amount, interest_rate, loan_tenure_months, refinance_rate, refinance_cost, currency],
        outputs=[refinance_out, chart_rate_comp]
    )
    refinance_cost.change(
        reactive_refinance_change,
        inputs=[loan_amount, interest_rate, loan_tenure_months, refinance_rate, refinance_cost, currency],
        outputs=[refinance_out, chart_rate_comp]
    )

    # Chat send button bindings
    chat_send.click(
        chat_callback,
        inputs=[
            chat_msg, chatbot, loan_type, loan_amount, interest_rate, loan_tenure_months,
            monthly_income, extra_monthly_budget, current_reserve, annual_prepayment, lump_sum_amount,
            currency, api_key, api_provider, model_name
        ],
        outputs=[chatbot, chat_msg]
    )
    chat_msg.submit(
        chat_callback,
        inputs=[
            chat_msg, chatbot, loan_type, loan_amount, interest_rate, loan_tenure_months,
            monthly_income, extra_monthly_budget, current_reserve, annual_prepayment, lump_sum_amount,
            currency, api_key, api_provider, model_name
        ],
        outputs=[chatbot, chat_msg]
    )

    # Reset parameters callback
    btn_reset.click(
        reset_inputs,
        outputs=[
            loan_type, loan_amount, interest_rate, loan_tenure_months,
            monthly_income, monthly_expenses, current_reserve,
            extra_monthly_budget, annual_prepayment, lump_sum_amount,
            emi_increase_pct, refinance_rate, refinance_cost,
            risk_appetite, existing_investments, inflation, current_age, retirement_age,
            currency, api_provider
        ]
    )
    
    # Session File Load Callback
    session_file_upload.change(
        load_session_config,
        inputs=[session_file_upload],
        outputs=[
            loan_type, loan_amount, interest_rate, loan_tenure_months, 
            monthly_income, monthly_expenses, current_reserve, 
            extra_monthly_budget, annual_prepayment, lump_sum_amount, 
            emi_increase_pct, refinance_rate, refinance_cost, 
            risk_appetite, existing_investments, inflation, current_age, retirement_age,
            currency
        ]
    )

    btn_save_session.click(
        save_session_config,
        inputs=[
            loan_type, loan_amount, interest_rate, loan_tenure_months, 
            monthly_income, monthly_expenses, current_reserve, 
            extra_monthly_budget, annual_prepayment, lump_sum_amount, 
            emi_increase_pct, refinance_rate, refinance_cost, 
            risk_appetite, existing_investments, inflation, current_age, retirement_age,
            currency
        ],
        outputs=[session_file_download]
    )

    # Automatically trigger initial run on application launch
    demo.load(
        run_optimization_engine,
        inputs=[
            loan_type, loan_amount, interest_rate, loan_tenure_months,
            monthly_income, monthly_expenses, current_reserve,
            extra_monthly_budget, annual_prepayment, lump_sum_amount,
            emi_increase_pct, refinance_rate, refinance_cost,
            risk_appetite, existing_investments, inflation, current_age, retirement_age,
            currency, api_key, api_provider, model_name
        ],
        outputs=[
            kpi_display, alert_display, summary_display, ai_display,
            emi_inc_out, chart_emi_inc,
            annual_out, chart_annual,
            lump_out, chart_lump,
            refinance_out, chart_rate_comp,
            emi_ratio_display, emergency_fund_display, score_details_display, milestones_display,
            df_what_if_display, prepay_vs_invest_display,
            chart_pie, chart_pr_rem, chart_int_cum, chart_pr_cum, chart_comb_time, chart_df_milestone,
            export_pdf_btn,
            tabs_container
        ]
    )

# Run app locally
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
