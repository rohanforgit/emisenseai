import math
from datetime import datetime, timedelta

def calculate_emi(principal, annual_rate, tenure_months):
    """
    Calculate the monthly EMI using standard compounding formula.
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    if annual_rate <= 0:
        return principal / tenure_months
        
    r = (annual_rate / 12.0) / 100.0
    try:
        emi = principal * r * ((1 + r) ** tenure_months) / (((1 + r) ** tenure_months) - 1)
        return round(emi, 2)
    except ZeroDivisionError:
        return round(principal / tenure_months, 2)

def simulate_amortization(principal, annual_rate, tenure_months, 
                          extra_monthly=0.0, annual_prepayment=0.0, 
                          lump_sum=0.0, lump_sum_month=1):
    """
    Simulates a month-by-month amortization schedule, incorporating:
    - Standard monthly EMI
    - Additional monthly prepayments
    - Recurring annual prepayments (applied every 12 months)
    - A one-time lump-sum prepayment (applied at a specific month)
    
    Returns a dictionary with lists of interest, principal, balance, and cumulative metrics.
    """
    base_emi = calculate_emi(principal, annual_rate, tenure_months)
    r = (annual_rate / 12.0) / 100.0
    
    balance = principal
    schedule = []
    
    total_interest_paid = 0.0
    total_principal_paid = 0.0
    total_payment = 0.0
    
    month = 1
    # Safety limit to prevent infinite loops if EMI is too low to cover interest
    max_months = 600 # 50 years max
    
    if r > 0 and base_emi <= balance * r:
        # If EMI doesn't cover interest, force a higher minimum EMI or return warning
        # But here we simulate what we can. Let's make sure it doesn't loop infinitely.
        base_emi = balance * r + 1.0
        
    while balance > 0.01 and month <= max_months:
        interest_this_month = balance * r if r > 0 else 0.0
        
        # Calculate base payment
        payment_this_month = base_emi
        if payment_this_month > (balance + interest_this_month):
            payment_this_month = balance + interest_this_month
            
        principal_this_month = payment_this_month - interest_this_month
        if principal_this_month < 0:
            principal_this_month = 0.0
            
        balance -= principal_this_month
        
        # Apply extra monthly payment
        applied_extra_monthly = 0.0
        if balance > 0 and extra_monthly > 0:
            applied_extra_monthly = min(extra_monthly, balance)
            balance -= applied_extra_monthly
            
        # Apply lump sum (one-time)
        applied_lump_sum = 0.0
        if balance > 0 and lump_sum > 0 and month == lump_sum_month:
            applied_lump_sum = min(lump_sum, balance)
            balance -= applied_lump_sum
            
        # Apply annual prepayment (every 12th month)
        applied_annual = 0.0
        if balance > 0 and annual_prepayment > 0 and month % 12 == 0:
            applied_annual = min(annual_prepayment, balance)
            balance -= applied_annual
            
        actual_paid_principal = principal_this_month + applied_extra_monthly + applied_lump_sum + applied_annual
        actual_paid_interest = interest_this_month
        actual_total_payment = payment_this_month + applied_extra_monthly + applied_lump_sum + applied_annual
        
        total_interest_paid += actual_paid_interest
        total_principal_paid += actual_paid_principal
        total_payment += actual_total_payment
        
        schedule.append({
            "month": month,
            "interest": round(actual_paid_interest, 2),
            "principal": round(actual_paid_principal, 2),
            "extra_payment": round(applied_extra_monthly + applied_lump_sum + applied_annual, 2),
            "total_payment": round(actual_total_payment, 2),
            "remaining_balance": round(max(0.0, balance), 2),
            "cumulative_interest": round(total_interest_paid, 2),
            "cumulative_principal": round(total_principal_paid, 2),
            "cumulative_payment": round(total_payment, 2)
        })
        
        month += 1
        
    return schedule

def calculate_base_loan_details(principal, annual_rate, tenure_months, start_date=None):
    """
    Computes baseline stats: EMI, total interest, total payment, debt-free date, etc.
    """
    if start_date is None:
        start_date = datetime.now()
        
    emi = calculate_emi(principal, annual_rate, tenure_months)
    schedule = simulate_amortization(principal, annual_rate, tenure_months)
    
    total_interest = sum(m["interest"] for m in schedule)
    total_payment = sum(m["total_payment"] for m in schedule)
    actual_tenure = len(schedule)
    
    interest_percentage = (total_interest / total_payment * 100.0) if total_payment > 0 else 0.0
    debt_free_date = start_date + timedelta(days=actual_tenure * 30.4375) # average days per month
    
    return {
        "emi": emi,
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
        "interest_percentage": round(interest_percentage, 2),
        "actual_tenure_months": actual_tenure,
        "debt_free_date": debt_free_date,
        "schedule": schedule
    }

def simulate_emi_increase(principal, annual_rate, tenure_months, increase_percent):
    """
    Simulates scaling the standard EMI by a percentage.
    Calculates: New EMI, New Tenure, Interest Saved, Money Saved, Years Saved.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    base_emi = base["emi"]
    
    new_emi = base_emi * (1.0 + increase_percent / 100.0)
    extra_monthly = new_emi - base_emi
    
    # Run simulation with extra_monthly
    schedule = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=extra_monthly)
    
    new_total_interest = sum(m["interest"] for m in schedule)
    new_total_payment = sum(m["total_payment"] for m in schedule)
    new_tenure = len(schedule)
    
    interest_saved = base["total_interest"] - new_total_interest
    money_saved = base["total_payment"] - new_total_payment
    years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
    
    return {
        "new_emi": round(new_emi, 2),
        "new_tenure_months": new_tenure,
        "interest_saved": round(interest_saved, 2),
        "money_saved": round(money_saved, 2),
        "years_saved": round(max(0.0, years_saved), 2),
        "schedule": schedule
    }

def simulate_annual_prepayment(principal, annual_rate, tenure_months, annual_prepayment):
    """
    Simulates making a fixed extra payment once every 12 months.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    
    schedule = simulate_amortization(principal, annual_rate, tenure_months, annual_prepayment=annual_prepayment)
    
    new_total_interest = sum(m["interest"] for m in schedule)
    new_total_payment = sum(m["total_payment"] for m in schedule)
    new_tenure = len(schedule)
    
    interest_saved = base["total_interest"] - new_total_interest
    money_saved = base["total_payment"] - new_total_payment
    years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
    
    return {
        "new_tenure_months": new_tenure,
        "interest_saved": round(interest_saved, 2),
        "money_saved": round(money_saved, 2),
        "years_saved": round(max(0.0, years_saved), 2),
        "schedule": schedule
    }

def simulate_lump_sum(principal, annual_rate, tenure_months, lump_sum_amount, mode="reduce_tenure"):
    """
    Simulates a one-time lump sum payment.
    Modes:
      - "reduce_tenure": Keep EMI same, reduce tenure.
      - "reduce_emi": Keep tenure same, reduce EMI.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    
    if mode == "reduce_tenure":
        # Simply run with lump_sum at month 1
        schedule = simulate_amortization(principal, annual_rate, tenure_months, lump_sum=lump_sum_amount, lump_sum_month=1)
        new_total_interest = sum(m["interest"] for m in schedule)
        new_total_payment = sum(m["total_payment"] for m in schedule)
        new_tenure = len(schedule)
        
        interest_saved = base["total_interest"] - new_total_interest
        money_saved = base["total_payment"] - new_total_payment
        years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
        
        return {
            "mode": "reduce_tenure",
            "reduced_principal": max(0.0, principal - lump_sum_amount),
            "new_emi": base["emi"],
            "new_tenure_months": new_tenure,
            "interest_saved": round(interest_saved, 2),
            "money_saved": round(money_saved, 2),
            "years_saved": round(max(0.0, years_saved), 2),
            "schedule": schedule
        }
    else: # reduce_emi
        reduced_principal = max(0.0, principal - lump_sum_amount)
        new_emi = calculate_emi(reduced_principal, annual_rate, tenure_months)
        
        # Simulate with the new lower principal from month 0 and new emi
        # Equivalent to running amortization with reduced principal
        schedule = simulate_amortization(reduced_principal, annual_rate, tenure_months)
        
        # Add the lump sum payment to the initial payment stats for correct savings
        new_total_interest = sum(m["interest"] for m in schedule)
        new_total_payment = sum(m["total_payment"] for m in schedule) + lump_sum_amount
        new_tenure = len(schedule)
        
        interest_saved = base["total_interest"] - new_total_interest
        money_saved = base["total_payment"] - new_total_payment
        years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
        
        return {
            "mode": "reduce_emi",
            "reduced_principal": reduced_principal,
            "new_emi": round(new_emi, 2),
            "new_tenure_months": new_tenure,
            "interest_saved": round(interest_saved, 2),
            "money_saved": round(money_saved, 2),
            "years_saved": round(max(0.0, years_saved), 2),
            "schedule": schedule
        }

def simulate_interest_rate_comparison(principal, tenure_months, current_rate):
    """
    Compares standard rates from 7.0% to 10.0% (in 0.5% increments) against the current rate.
    """
    rates = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    if current_rate not in rates:
        rates.append(current_rate)
    rates = sorted(list(set(rates)))
    
    base = calculate_base_loan_details(principal, current_rate, tenure_months)
    comparison = []
    
    for rate in rates:
        details = calculate_base_loan_details(principal, rate, tenure_months)
        emi_diff = details["emi"] - base["emi"]
        interest_diff = details["total_interest"] - base["total_interest"]
        savings = -interest_diff # if positive, it means savings. If negative, it means cost.
        
        comparison.append({
            "rate": rate,
            "emi": details["emi"],
            "total_interest": details["total_interest"],
            "total_payment": details["total_payment"],
            "emi_difference": round(emi_diff, 2),
            "interest_difference": round(interest_diff, 2),
            "total_savings": round(savings, 2)
        })
        
    return comparison

def calculate_refinancing(principal, current_rate, remaining_tenure_months, new_rate, refinancing_cost):
    """
    Analyzes refinancing viability.
    """
    base = calculate_base_loan_details(principal, current_rate, remaining_tenure_months)
    new_loan = calculate_base_loan_details(principal, new_rate, remaining_tenure_months)
    
    monthly_saving = base["emi"] - new_loan["emi"]
    gross_interest_saved = base["total_interest"] - new_loan["total_interest"]
    net_savings = gross_interest_saved - refinancing_cost
    
    if monthly_saving > 0:
        break_even_months = refinancing_cost / monthly_saving
    else:
        break_even_months = float('inf')
        
    worth_refinancing = net_savings > 0 and break_even_months < remaining_tenure_months
    
    return {
        "current_emi": base["emi"],
        "new_emi": new_loan["emi"],
        "monthly_saving": round(monthly_saving, 2),
        "gross_interest_saved": round(gross_interest_saved, 2),
        "net_savings": round(net_savings, 2),
        "break_even_months": round(break_even_months, 2) if break_even_months != float('inf') else "N/A",
        "worth_refinancing": worth_refinancing
    }

def calculate_emi_to_income(monthly_emi, monthly_income):
    """
    Calculates EMI-to-Income ratio and returning category.
    """
    if monthly_income <= 0:
        return 0.0, "Dangerous", "Invalid Income"
        
    ratio = (monthly_emi / monthly_income) * 100.0
    
    if ratio < 20.0:
        category = "Excellent"
        advice = "Your debt load is very healthy. You have significant buffer for savings and investments."
    elif ratio < 30.0:
        category = "Good"
        advice = "Your debt load is manageable. Normal for home and personal financing. Try to keep it below 30%."
    elif ratio < 40.0:
        category = "Moderate"
        advice = "You are spending a significant portion of your income on debt. Avoid taking any new loans."
    elif ratio < 50.0:
        category = "Risky"
        advice = "Debt payments consume nearly half your income. Consider prepayment or refinancing immediately to reduce EMI."
    else:
        category = "Dangerous"
        advice = "DANGER! Debt payments exceed 50% of income. You are at high risk of financial distress. Reprioritize expenses immediately."
        
    return round(ratio, 2), category, advice

def calculate_emergency_fund(monthly_expenses, monthly_emi, current_reserve):
    """
    Compares current reserves with 3/6/12 months of expenses + EMI.
    """
    monthly_outflow = monthly_expenses + monthly_emi
    
    fund_3m = monthly_outflow * 3
    fund_6m = monthly_outflow * 6
    fund_12m = monthly_outflow * 12
    
    # Recommended reserve is 6 months
    recommended = fund_6m
    gap = recommended - current_reserve
    
    if current_reserve >= fund_12m:
        advice = "Superb! You have over 12 months of runway. You can safely allocate some cash towards prepaying your loans."
    elif current_reserve >= fund_6m:
        advice = "Excellent. You have a solid 6-month buffer. You are well-positioned to make prepayments with any additional cash flows."
    elif current_reserve >= fund_3m:
        advice = "Adequate. You have a 3-month buffer. While stable, it's safer to grow it to 6 months before aggressively prepaying low-interest debt."
    else:
        advice = "Warning! Your reserves are below the 3-month threshold. Focus on building your emergency savings before making any extra loan prepayments."
        
    return {
        "monthly_outflow": round(monthly_outflow, 2),
        "fund_3m": round(fund_3m, 2),
        "fund_6m": round(fund_6m, 2),
        "fund_12m": round(fund_12m, 2),
        "recommended": round(recommended, 2),
        "current_reserve": round(current_reserve, 2),
        "gap": round(max(0.0, gap), 2),
        "advice": advice
    }

def calculate_health_score(principal, annual_rate, tenure_months, emi, income, 
                           expenses, current_reserve, extra_monthly, loan_type):
    """
    Computes a loan health score between 0 and 100 based on weighted metrics:
    1. Interest Rate Burden (25%)
    2. EMI-to-Income ratio (25%)
    3. Emergency Fund Gap (20%)
    4. Tenure Risk (15%)
    5. Prepayment Capacity (15%)
    """
    score = 100.0
    deductions = []
    
    # 1. Interest Rate (Compare to benchmark for loan types)
    # Lower benchmarks are safer.
    benchmarks = {
        "Home Loan": 8.0,
        "Car Loan": 9.0,
        "Bike Loan": 10.0,
        "Education Loan": 9.5,
        "Personal Loan": 12.0,
        "Business Loan": 11.0,
        "Gold Loan": 9.0,
        "Custom Loan": 9.5
    }
    benchmark = benchmarks.get(loan_type, 9.5)
    rate_diff = annual_rate - benchmark
    if rate_diff > 0:
        penalty = min(25.0, rate_diff * 4) # 4 points per 1% above benchmark
        score -= penalty
        deductions.append(f"Interest rate is {annual_rate}% which is above the benchmark for {loan_type} ({benchmark}%). (-{round(penalty, 1)} pts)")
        
    # 2. EMI-to-Income (Goal < 30%)
    ratio = (emi / income * 100.0) if income > 0 else 100.0
    if ratio >= 50.0:
        score -= 25.0
        deductions.append(f"EMI consumes {round(ratio, 1)}% of income (Critical threshold >50%). (-25 pts)")
    elif ratio >= 40.0:
        score -= 20.0
        deductions.append(f"EMI consumes {round(ratio, 1)}% of income (Risky 40-50%). (-20 pts)")
    elif ratio >= 30.0:
        score -= 12.0
        deductions.append(f"EMI consumes {round(ratio, 1)}% of income (Moderate 30-40%). (-12 pts)")
    elif ratio >= 20.0:
        score -= 5.0
        deductions.append(f"EMI consumes {round(ratio, 1)}% of income (Good 20-30%). (-5 pts)")
        
    # 3. Emergency Fund Gap (Goal: current_reserve >= 6 * (expenses + emi))
    monthly_outflow = expenses + emi
    recommended_reserve = monthly_outflow * 6
    if recommended_reserve > 0:
        coverage = current_reserve / recommended_reserve
        if coverage < 0.2:
            score -= 20.0
            deductions.append("Critical: Emergency fund covers less than 20% of the recommended 6-month buffer. (-20 pts)")
        elif coverage < 0.5:
            score -= 15.0
            deductions.append("Warning: Emergency fund covers less than 50% of the recommended 6-month buffer. (-15 pts)")
        elif coverage < 1.0:
            score -= 8.0
            deductions.append("Moderate: Emergency fund is below the recommended 6-month buffer. (-8 pts)")
            
    # 4. Tenure Risk (Longer loans accrue more interest)
    if tenure_months > 240: # > 20 years
        score -= 15.0
        deductions.append(f"High Tenure: Loan tenure of {tenure_months} months (>20 years) increases total interest burden. (-15 pts)")
    elif tenure_months > 120: # 10 to 20 years
        score -= 8.0
        deductions.append(f"Moderate Tenure: Loan tenure of {tenure_months} months (10-20 years). (-8 pts)")
        
    # 5. Prepayment Capacity (Can user afford to pay more?)
    # If budget is 0, they can't optimize, which is a risk.
    if extra_monthly <= 0:
        score -= 15.0
        deductions.append("No extra monthly budget allocated for prepayments, limiting optimization options. (-15 pts)")
    elif extra_monthly < emi * 0.05: # less than 5% of EMI
        score -= 8.0
        deductions.append(f"Low prepayment capacity ({round(extra_monthly, 2)} is <5% of EMI). (-8 pts)")
        
    score = max(0.0, min(100.0, score))
    
    if score >= 90.0:
        status = "Excellent"
    elif score >= 75.0:
        status = "Good"
    elif score >= 60.0:
        status = "Average"
    elif score >= 40.0:
        status = "Poor"
    else:
        status = "Danger"
        
    return round(score, 0), status, deductions

def simulate_what_if_analysis(principal, annual_rate, tenure_months, income, expenses, current_reserve,
                               extra_monthly, risk_appetite, investments, inflation, age, retirement_age):
    """
    Simulates advanced what-if events and calculates their financial impact on the loan:
    1. Higher Salary (+15% income -> increases extra monthly budget)
    2. Lower Salary (-15% income -> decreases extra monthly budget)
    3. Job Loss (Income = 0 for 6 months -> emergency fund drains, EMIs still need to be paid)
    4. Interest Rate Increase (+2% interest rate)
    5. Interest Rate Decrease (-2% interest rate)
    6. Marriage / Family Expansion (+30% expenses -> decreases extra budget)
    7. Prepay vs Invest (Compare prepaying with extra_monthly vs investing it at expected return based on risk)
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    base_emi = base["emi"]
    
    # 1. Higher Salary
    new_inc_high = income * 1.15
    added_budget = new_inc_high - income
    new_extra_monthly_high = extra_monthly + added_budget
    sim_high_sal = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=new_extra_monthly_high)
    high_sal_interest = sum(m["interest"] for m in sim_high_sal)
    high_sal_months = len(sim_high_sal)
    
    # 2. Lower Salary
    new_inc_low = income * 0.85
    subtracted_budget = income - new_inc_low
    new_extra_monthly_low = max(0.0, extra_monthly - subtracted_budget)
    sim_low_sal = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=new_extra_monthly_low)
    low_sal_interest = sum(m["interest"] for m in sim_low_sal)
    low_sal_months = len(sim_low_sal)
    
    # 3. Job Loss
    # We check if Emergency Fund covers 6 months of outflow (expenses + EMI)
    monthly_outflow = expenses + base_emi
    cost_for_6_months = monthly_outflow * 6.0
    
    # 4. Interest Rate Increase (+2.0%)
    sim_rate_high = calculate_base_loan_details(principal, annual_rate + 2.0, tenure_months)
    
    # 5. Interest Rate Decrease (-2.0%)
    sim_rate_low = calculate_base_loan_details(principal, max(1.0, annual_rate - 2.0), tenure_months)
    
    # 6. Marriage / Child
    new_exp_family = expenses * 1.30
    family_extra_budget = max(0.0, extra_monthly - (new_exp_family - expenses))
    sim_family = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=family_extra_budget)
    family_interest = sum(m["interest"] for m in sim_family)
    family_months = len(sim_family)
    
    # 7. Prepay vs Invest
    # Risk appetite determines expected investment returns: Conservative (7%), Moderate (10%), Aggressive (13%)
    expected_returns = {
        "Conservative": 7.0,
        "Moderate": 10.0,
        "Aggressive": 13.0
    }
    return_rate = expected_returns.get(risk_appetite, 10.0)
    
    # Compare:
    # Option A: Prepay loan with extra_monthly (saves interest, reduces tenure)
    prepay_sim = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=extra_monthly)
    prepay_interest_paid = sum(m["interest"] for m in prepay_sim)
    prepay_months = len(prepay_sim)
    
    # Option B: Maintain baseline loan (pay base EMI), and invest extra_monthly in a compound account
    # We compound monthly: A = P_monthly * [ (1 + r_inv)^N - 1 ] / r_inv
    r_inv = (return_rate / 12.0) / 100.0
    total_months_to_compare = base["actual_tenure_months"]
    
    invested_value = 0.0
    total_invested_capital = 0.0
    for m in range(total_months_to_compare):
        invested_value = (invested_value + extra_monthly) * (1.0 + r_inv)
        total_invested_capital += extra_monthly
        
    investment_profit = invested_value - total_invested_capital
    
    # Financial benefit of prepaying:
    # Baseline interest paid minus Prepay interest paid
    interest_saved_by_prepaying = base["total_interest"] - prepay_interest_paid
    # Also, we free up the EMI payment early!
    # If prepaying makes us debt free in K months, for the remaining (N - K) months, we can invest the full (base_emi + extra_monthly)
    full_investment_value = 0.0
    if prepay_months < total_months_to_compare:
        months_freed = total_months_to_compare - prepay_months
        for m in range(months_freed):
            full_investment_value = (full_investment_value + base_emi + extra_monthly) * (1.0 + r_inv)
            
    total_value_prepay_strategy = invested_value + interest_saved_by_prepaying if prepay_months >= total_months_to_compare else full_investment_value + interest_saved_by_prepaying
    
    # Simple advice
    if return_rate > annual_rate:
        prepay_vs_invest_advice = f"Investing extra money at {return_rate}% expected return yields higher growth than prepaying a {annual_rate}% loan. However, prepaying gives a guaranteed return and makes you debt-free {round((base['actual_tenure_months']-prepay_months)/12, 1)} years earlier."
    else:
        prepay_vs_invest_advice = f"Prepaying your loan at {annual_rate}% guarantees a return higher than the {return_rate}% expected investment return. Focus on debt payoff first."
        
    return {
        "higher_salary": {
            "new_tenure_months": high_sal_months,
            "interest_saved": round(base["total_interest"] - high_sal_interest, 2),
            "years_saved": round((base["actual_tenure_months"] - high_sal_months) / 12.0, 1)
        },
        "lower_salary": {
            "new_tenure_months": low_sal_months,
            "interest_saved": round(base["total_interest"] - low_sal_interest, 2),
            "years_saved": round((base["actual_tenure_months"] - low_sal_months) / 12.0, 1)
        },
        "job_loss": {
            "outflow_6m": round(cost_for_6_months, 2),
            "has_enough_reserve": current_reserve >= cost_for_6_months
        },
        "rate_increase": {
            "new_emi": sim_rate_high["emi"],
            "total_interest": sim_rate_high["total_interest"],
            "interest_difference": round(sim_rate_high["total_interest"] - base["total_interest"], 2)
        },
        "rate_decrease": {
            "new_emi": sim_rate_low["emi"],
            "total_interest": sim_rate_low["total_interest"],
            "interest_difference": round(sim_rate_low["total_interest"] - base["total_interest"], 2)
        },
        "family_expansion": {
            "new_tenure_months": family_months,
            "interest_saved": round(base["total_interest"] - family_interest, 2),
            "years_saved": round((base["actual_tenure_months"] - family_months) / 12.0, 1)
        },
        "prepay_vs_invest": {
            "investment_return_rate": return_rate,
            "investment_value": round(invested_value, 2),
            "investment_profit": round(investment_profit, 2),
            "interest_saved_prepay": round(interest_saved_by_prepaying, 2),
            "prepay_years_saved": round((base["actual_tenure_months"] - prepay_months) / 12.0, 1),
            "prepay_strategy_value": round(total_value_prepay_strategy, 2),
            "advice": prepay_vs_invest_advice
        }
    }

def get_loan_specific_features(loan_type, principal, annual_rate, tenure_months, base_emi):
    """
    Returns specific calculations and alerts for each loan type.
    """
    results = {}
    
    if loan_type == "Home Loan":
        # Indian standard context: Tax deduction under Section 24b up to 2,00,000 INR
        # For general, write standard deduction message.
        tax_limit = 200000
        interest_deduction_val = min(tax_limit, base_emi * 12 * 0.5) # approximate yearly interest
        results["tax_deduction_estimate"] = round(interest_deduction_val, 2)
        results["advice"] = "For Home Loans, you can save taxes under local sections (e.g. Section 24b). Making one extra EMI payment every year speeds up debt payoff dramatically."
        
        # Home Loan Special: 1 extra EMI payment per year
        # An extra EMI payment means prepaying 'base_emi' once every 12 months
        special_sim = simulate_amortization(principal, annual_rate, tenure_months, annual_prepayment=base_emi)
        base = calculate_base_loan_details(principal, annual_rate, tenure_months)
        new_tenure = len(special_sim)
        interest_saved = base["total_interest"] - sum(m["interest"] for m in special_sim)
        years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
        
        results["extra_emi_effect"] = {
            "new_tenure_months": new_tenure,
            "interest_saved": round(interest_saved, 2),
            "years_saved": round(years_saved, 1)
        }
        
    elif loan_type == "Car Loan":
        # Vehicle depreciation: approx 15% per year
        car_val = principal
        value_timeline = []
        for year in range(1, int(math.ceil(tenure_months / 12.0)) + 1):
            car_val = car_val * 0.85
            value_timeline.append((year, round(car_val, 2)))
        results["depreciation_timeline"] = value_timeline
        results["advice"] = "Cars deprecate rapidly (~15% annually). Aim to prepay early to avoid becoming 'underwater' where you owe more than the car is worth."
        
    elif loan_type == "Bike Loan":
        results["advice"] = "Bike loans have shorter tenures but slightly higher rates. Pay this off quickly by increasing EMI by 10-15% to clear high interest costs."
        
    elif loan_type == "Education Loan":
        results["advice"] = "Education loans usually have moratorium benefits (no payments during studies). Try to pay interest during college to avoid compounding interest buildup."
        
    elif loan_type == "Personal Loan":
        results["advice"] = "Personal loans carry high rates (12-20%). Prepay as fast as possible. If you have multiple loans, consolidate them into a single low-rate loan."
        
    elif loan_type == "Business Loan":
        # ROI suggestions
        results["advice"] = "Verify if business expansion returns (ROI) exceed the loan interest rate. If business ROI is 15% and loan is 11%, reinvesting capital is better than prepaying."
        
    elif loan_type == "Gold Loan":
        results["advice"] = "Gold loans are asset-backed and have lower rates. However, watch the Loan-to-Value (LTV) ratio. If gold prices fall, lenders may demand immediate margins."
        
    else:
        results["advice"] = "Custom Loan. Check local tax incentives, prepay terms, and refinancing opportunities."
        
    return results

def get_financial_milestones(age, retirement_age, current_tenure_months, optimized_tenure_months):
    """
    Computes and displays milestones for loan duration.
    """
    current_tenure_years = current_tenure_months / 12.0
    optimized_tenure_years = optimized_tenure_months / 12.0
    
    loan_end_age = age + current_tenure_years
    debt_free_age = age + optimized_tenure_years
    
    retirement_gap_base = retirement_age - loan_end_age
    retirement_gap_opt = retirement_age - debt_free_age
    
    if debt_free_age < retirement_age:
        advice = f"Fantastic! You will be debt-free at {round(debt_free_age, 1)}, which is {round(retirement_gap_opt, 1)} years before retirement. This allows you to redirect your EMI money towards retirement investments."
    else:
        advice = f"Warning: Your debt outstanding runs until age {round(debt_free_age, 1)}, which is after your retirement age of {retirement_age}. Try optimizing your loan to finish payments before retiring."
        
    return {
        "current_age": age,
        "loan_end_age": round(loan_end_age, 1),
        "debt_free_age": round(debt_free_age, 1),
        "retirement_gap_base": round(retirement_gap_base, 1),
        "retirement_gap_opt": round(retirement_gap_opt, 1),
        "advice": advice
    }

def generate_smart_alerts(principal, annual_rate, tenure_months, emi, income, expenses, current_reserve):
    """
    Finds critical risk points and outputs alerts.
    """
    alerts = []
    
    # 1. High EMI Burden
    ratio = (emi / income * 100.0) if income > 0 else 100.0
    if ratio > 40.0:
        alerts.append({
            "type": "danger",
            "message": f"High Debt Burden: Your EMIs consume {round(ratio, 1)}% of your monthly income. Maintain a ratio below 30%."
        })
        
    # 2. Insufficient Emergency Fund
    monthly_outflow = expenses + emi
    six_month_fund = monthly_outflow * 6.0
    if current_reserve < six_month_fund:
        alerts.append({
            "type": "warning",
            "message": f"Critical Reserve Gap: Your emergency reserve is ₹{round(current_reserve, 2)}, which is below the recommended 6-month buffer of ₹{round(six_month_fund, 2)}."
        })
        
    # 3. High Interest Rate Alert
    if annual_rate > 11.5:
        alerts.append({
            "type": "warning",
            "message": f"High Interest Rate Alert: Your rate of {annual_rate}% is high. Check refinancing options or focus on rapid prepayment."
        })
        
    # 4. Long Tenure Alert
    if tenure_months > 180: # 15 years
        alerts.append({
            "type": "info",
            "message": f"Long-Term Interest Trapping: A {tenure_months}-month tenure means you will pay substantial interest. Prepay to reduce tenure."
        })
        
    # 5. Opportunity alerts
    if current_reserve > six_month_fund * 1.5:
        alerts.append({
            "type": "success",
            "message": "Prepayment Opportunity: You have excess emergency cash. Consider a one-time lump sum payment to reduce your tenure."
        })
        
    return alerts
