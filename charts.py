import plotly.graph_objects as go
import plotly.express as px
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os
from calculations import (
    simulate_amortization,
    calculate_base_loan_details,
    simulate_emi_increase,
    simulate_annual_prepayment,
    simulate_lump_sum,
    simulate_interest_rate_comparison
)

# Dark Theme styling variables
DARK_THEME_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color='#F8FAFC', size=11),
    margin=dict(l=40, r=40, t=40, b=40),
    hoverlabel=dict(bgcolor='#1E293B', font_color='#F8FAFC', font_family='Inter'),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5,
        font=dict(size=10)
    )
)

AXIS_STYLE = dict(
    showgrid=True,
    gridcolor='#334155',
    linecolor='#475569',
    tickcolor='#475569',
    zeroline=False
)

def style_fig(fig):
    """
    Applies the custom fintech dark theme to a Plotly figure.
    """
    fig.update_layout(**DARK_THEME_LAYOUT)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# 1. EMI Breakdown Chart (Pie)
def generate_emi_breakdown_chart(principal, total_interest):
    labels = ['Principal Amount', 'Total Interest Payable']
    values = [principal, total_interest]
    colors = ['#10B981', '#EF4444'] # Green, Red
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5,
        marker=dict(colors=colors, line=dict(color='#1E293B', width=2)),
        textinfo='percent+label',
        hoverinfo='label+value'
    )])
    fig.update_layout(title="EMI Composition (Principal vs Interest)")
    return style_fig(fig)

# 2. Principal Remaining Timeline (Line)
def generate_principal_remaining_chart(baseline_schedule, optimized_schedule=None, label_opt="Optimized"):
    fig = go.Figure()
    
    months_base = [m["month"] for m in baseline_schedule]
    bal_base = [m["remaining_balance"] for m in baseline_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=bal_base, 
        mode='lines', 
        name='Baseline Loan',
        line=dict(color='#64748B', width=3) # Slate
    ))
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        bal_opt = [m["remaining_balance"] for m in optimized_schedule]
        fig.add_trace(go.Scatter(
            x=months_opt, 
            y=bal_opt, 
            mode='lines', 
            name=label_opt,
            line=dict(color='#EAB308', width=3, dash='dash') # Gold
        ))
        
    fig.update_layout(
        title="Remaining Principal Balance Over Time",
        xaxis_title="Month",
        yaxis_title="Outstanding Principal"
    )
    return style_fig(fig)

# 3. Interest Paid Over Time (Line)
def generate_interest_paid_chart(baseline_schedule, optimized_schedule=None, label_opt="Optimized"):
    fig = go.Figure()
    
    months_base = [m["month"] for m in baseline_schedule]
    int_base = [m["cumulative_interest"] for m in baseline_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=int_base, 
        mode='lines', 
        name='Baseline Loan Interest',
        line=dict(color='#EF4444', width=2) # Red
    ))
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        int_opt = [m["cumulative_interest"] for m in optimized_schedule]
        fig.add_trace(go.Scatter(
            x=months_opt, 
            y=int_opt, 
            mode='lines', 
            name=f'{label_opt} Interest',
            line=dict(color='#EAB308', width=3, dash='dot') # Gold
        ))
        
    fig.update_layout(
        title="Cumulative Interest Paid Over Time",
        xaxis_title="Month",
        yaxis_title="Cumulative Interest"
    )
    return style_fig(fig)

# 4. Principal Paid Over Time (Line)
def generate_principal_paid_chart(baseline_schedule, optimized_schedule=None, label_opt="Optimized"):
    fig = go.Figure()
    
    months_base = [m["month"] for m in baseline_schedule]
    pr_base = [m["cumulative_principal"] for m in baseline_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=pr_base, 
        mode='lines', 
        name='Baseline Principal Paid',
        line=dict(color='#10B981', width=2) # Green
    ))
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        pr_opt = [m["cumulative_principal"] for m in optimized_schedule]
        fig.add_trace(go.Scatter(
            x=months_opt, 
            y=pr_opt, 
            mode='lines', 
            name=f'{label_opt} Principal Paid',
            line=dict(color='#3B82F6', width=3, dash='dot') # Accent Blue
        ))
        
    fig.update_layout(
        title="Cumulative Principal Paid Over Time",
        xaxis_title="Month",
        yaxis_title="Cumulative Principal"
    )
    return style_fig(fig)

# 5. Savings from EMI Increase (Bar)
def generate_emi_increase_savings_chart(principal, annual_rate, tenure_months):
    percentages = [5, 10, 15, 20, 25, 50]
    savings = []
    
    for pct in percentages:
        res = simulate_emi_increase(principal, annual_rate, tenure_months, pct)
        savings.append(res["interest_saved"])
        
    fig = go.Figure(data=[go.Bar(
        x=[f"+{p}% EMI" for p in percentages],
        y=savings,
        marker_color='#3B82F6', # Accent Blue
        text=[f"₹{s:,.0f}" for s in savings],
        textposition='auto',
        hoverinfo='y'
    )])
    
    fig.update_layout(
        title="Interest Saved by EMI Increase %",
        xaxis_title="EMI Increase Scenario",
        yaxis_title="Total Interest Saved"
    )
    return style_fig(fig)

# 6. Savings from Lump Sum Payment (Bar)
def generate_lump_sum_savings_chart(principal, annual_rate, tenure_months):
    # Test 3 lump sum amounts: 5%, 10%, 20% of principal
    amounts = [principal * 0.05, principal * 0.10, principal * 0.20]
    savings = []
    
    for amt in amounts:
        res = simulate_lump_sum(principal, annual_rate, tenure_months, amt, mode="reduce_tenure")
        savings.append(res["interest_saved"])
        
    fig = go.Figure(data=[go.Bar(
        x=[f"5% (₹{amounts[0]:,.0f})", f"10% (₹{amounts[1]:,.0f})", f"20% (₹{amounts[2]:,.0f})"],
        y=savings,
        marker_color='#EAB308', # Gold
        text=[f"₹{s:,.0f}" for s in savings],
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Interest Saved by One-time Lump Sum Payment Amount",
        xaxis_title="Lump Sum Amount (% of Principal)",
        yaxis_title="Total Interest Saved"
    )
    return style_fig(fig)

# 7. Savings from Annual Prepayment (Bar)
def generate_annual_prepayment_savings_chart(principal, annual_rate, tenure_months):
    # Test 3 annual prepayment levels: 1% of principal, 2.5%, 5%
    amounts = [principal * 0.01, principal * 0.025, principal * 0.05]
    savings = []
    
    for amt in amounts:
        res = simulate_annual_prepayment(principal, annual_rate, tenure_months, amt)
        savings.append(res["interest_saved"])
        
    fig = go.Figure(data=[go.Bar(
        x=[f"1% (₹{amounts[0]:,.0f}/yr)", f"2.5% (₹{amounts[1]:,.0f}/yr)", f"5% (₹{amounts[2]:,.0f}/yr)"],
        y=savings,
        marker_color='#10B981', # Green
        text=[f"₹{s:,.0f}" for s in savings],
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Interest Saved by Recurring Annual Prepayment Level",
        xaxis_title="Annual Prepayment Amount (% of Principal)",
        yaxis_title="Total Interest Saved"
    )
    return style_fig(fig)

# 8. Interest Rate Comparison Chart (Grouped Bar)
def generate_rate_comparison_chart(principal, tenure_months, current_rate):
    comparison = simulate_interest_rate_comparison(principal, tenure_months, current_rate)
    
    rates = [f"{c['rate']}%" for c in comparison]
    emis = [c['emi'] for c in comparison]
    total_interests = [c['total_interest'] for c in comparison]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rates,
        y=emis,
        name='Monthly EMI',
        marker_color='#3B82F6'
    ))
    fig.add_trace(go.Bar(
        x=rates,
        y=total_interests,
        name='Total Interest',
        marker_color='#EF4444'
    ))
    
    fig.update_layout(
        title="Comparison of Monthly EMI and Total Interest by Rates",
        xaxis_title="Annual Interest Rate",
        yaxis_title="Amount",
        barmode='group'
    )
    return style_fig(fig)

# 9. Loan Balance Timeline - Combined prepays vs baseline
def generate_combined_timeline_chart(principal, annual_rate, tenure_months, 
                                     extra_monthly=0.0, annual_prepayment=0.0, lump_sum=0.0):
    fig = go.Figure()
    
    base_schedule = simulate_amortization(principal, annual_rate, tenure_months)
    months_base = [m["month"] for m in base_schedule]
    bal_base = [m["remaining_balance"] for m in base_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=bal_base, 
        mode='lines', 
        name='Baseline (No prepayments)',
        line=dict(color='#64748B', width=2)
    ))
    
    opt_schedule = simulate_amortization(
        principal, annual_rate, tenure_months, 
        extra_monthly=extra_monthly, 
        annual_prepayment=annual_prepayment, 
        lump_sum=lump_sum, 
        lump_sum_month=1
    )
    months_opt = [m["month"] for m in opt_schedule]
    bal_opt = [m["remaining_balance"] for m in opt_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_opt, 
        y=bal_opt, 
        mode='lines', 
        name='Combined Strategy (Active Prepayments)',
        line=dict(color='#10B981', width=3)
    ))
    
    fig.update_layout(
        title="Amortization Schedule: Baseline vs. Combined Strategy",
        xaxis_title="Month",
        yaxis_title="Loan Balance"
    )
    return style_fig(fig)

# 10. Debt Free Timeline (Horizontal Milestone Bar Chart)
def generate_debt_free_timeline_chart(age, base_months, opt_months_emi, opt_months_annual, opt_months_lump, opt_months_combined):
    scenarios = ['Baseline', 'EMI +10%', 'Annual Prepay', 'Lump Sum 10%', 'Combined']
    months = [base_months, opt_months_emi, opt_months_annual, opt_months_lump, opt_months_combined]
    
    years = [m / 12.0 for m in months]
    ages = [age + y for y in years]
    
    fig = go.Figure()
    
    # We display the age at which the user becomes debt-free
    fig.add_trace(go.Bar(
        y=scenarios,
        x=ages,
        orientation='h',
        marker_color=['#64748B', '#3B82F6', '#10B981', '#EAB308', '#22C55E'],
        text=[f"Age {a:.1f} ({y:.1f} yrs)" for a, y in zip(ages, years)],
        textposition='inside',
        insidetextanchor='end',
        hoverinfo='x'
    ))
    
    fig.update_layout(
        title="Age of Becoming Debt-Free by Scenario",
        xaxis_title="Age",
        yaxis_title="Scenario",
        xaxis=dict(range=[age, max(ages) + 2])
    )
    return style_fig(fig)


# =====================================================================
# MATPLOTLIB HELPER FUNCTIONS FOR PDF EMBEDDING
# These functions output static figures saved as bytes arrays.
# =====================================================================

def generate_static_pie_chart(principal, total_interest):
    """
    Returns bytes of a static pie chart for PDF.
    """
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 4), facecolor='#1E293B')
    ax.set_facecolor('#1E293B')
    
    labels = ['Principal', 'Interest']
    sizes = [principal, total_interest]
    colors = ['#10B981', '#EF4444']
    
    ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=colors, 
        textprops={'color': '#F8FAFC', 'fontsize': 10},
        wedgeprops=dict(width=0.4, edgecolor='#1E293B', linewidth=2)
    )
    
    ax.set_title("EMI Composition", color='#F8FAFC', fontsize=12, pad=15)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def generate_static_timeline_chart(baseline_schedule, optimized_schedule=None):
    """
    Returns bytes of a static timeline comparison chart for PDF.
    """
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 4), facecolor='#1E293B')
    ax.set_facecolor('#1E293B')
    
    months_base = [m["month"] for m in baseline_schedule]
    bal_base = [m["remaining_balance"] for m in baseline_schedule]
    ax.plot(months_base, bal_base, color='#64748B', linewidth=2, label='Baseline')
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        bal_opt = [m["remaining_balance"] for m in optimized_schedule]
        ax.plot(months_opt, bal_opt, color='#EAB308', linewidth=2, linestyle='--', label='Optimized')
        
    ax.set_title("Remaining Balance Timeline", color='#F8FAFC', fontsize=12)
    ax.set_xlabel("Month", color='#F8FAFC')
    ax.set_ylabel("Balance Outstanding", color='#F8FAFC')
    ax.tick_params(colors='#F8FAFC')
    ax.grid(True, color='#334155', linestyle=':')
    ax.legend(facecolor='#1E293B', edgecolor='#334155')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
