from openai import OpenAI
import traceback

def get_client(provider, api_key):
    """
    Initializes the OpenAI client based on the provider.
    Checks environment variables if the key is not explicitly provided.
    """
    if not api_key:
        import os
        if provider == "Groq":
            api_key = os.environ.get("GROQ_API_KEY")
        elif provider == "HuggingFace":
            api_key = os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
        else: # OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return None
        
    try:
        if provider == "Groq":
            return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        elif provider == "HuggingFace":
            return OpenAI(api_key=api_key, base_url="https://router.huggingface.co/v1")
        else: # OpenAI
            return OpenAI(api_key=api_key)
    except Exception:
        return None

def generate_local_fallback_advice(loan_data, base_details, sim_emi, sim_annual, sim_lump, refinance, health_score, score_status):
    """
    Generates structured financial advice locally using pre-calculated values
    when no API key is provided or when the API call fails.
    """
    currency = loan_data.get("currency", "₹")
    loan_type = loan_data.get("loan_type", "Custom Loan")
    
    # Calculate top actions
    actions = []
    
    # Action 1: EMI Increase
    if sim_emi["interest_saved"] > 0:
        actions.append({
            "title": f"Increase Monthly EMI by {loan_data.get('emi_increase_pct', 10)}%",
            "savings": sim_emi["interest_saved"],
            "description": f"By increasing your EMI, you will finish your loan {sim_emi['years_saved']} years early and save {currency}{sim_emi['interest_saved']:,.2f} in interest."
        })
        
    # Action 2: Annual Prepayment
    if sim_annual["interest_saved"] > 0:
        actions.append({
            "title": f"Pay {currency}{loan_data.get('annual_prepayment', 0):,.2f} Annually",
            "savings": sim_annual["interest_saved"],
            "description": f"Making a recurring annual prepayment reduces tenure and saves {currency}{sim_annual['interest_saved']:,.2f} in interest."
        })
        
    # Action 3: Lump Sum
    if sim_lump["interest_saved"] > 0:
        actions.append({
            "title": f"Make a One-time Lump Sum of {currency}{loan_data.get('lump_sum_amount', 0):,.2f}",
            "savings": sim_lump["interest_saved"],
            "description": f"Prepaying this lump sum immediately reduces outstanding principal and saves {currency}{sim_lump['interest_saved']:,.2f} in interest."
        })
        
    # Action 4: Refinancing
    if refinance and refinance.get("worth_refinancing"):
        actions.append({
            "title": f"Refinance Loan to {loan_data.get('refinance_rate', 0.0)}%",
            "savings": refinance["net_savings"],
            "description": f"Transferring your balance to a lower rate saves {currency}{refinance['net_savings']:,.2f} net of refinancing costs, breaking even in {refinance['break_even_months']} months."
        })
        
    # Sort actions by savings descending
    actions = sorted(actions, key=lambda x: x["savings"], reverse=True)
    
    # Generate Top 3 Actions markdown
    actions_md = ""
    for idx, act in enumerate(actions[:3], 1):
        actions_md += f"### {idx}. {act['title']}\n"
        actions_md += f"**Potential Interest Savings:** {currency}{act['savings']:,.2f}\n\n"
        actions_md += f"{act['description']}\n\n"
        
    if not actions_md:
        actions_md = "No prepayment optimizations simulation run or no savings found yet. Try adjusting your simulation inputs in the main panel."
        
    # General Advice based on Health Score
    health_advice = ""
    if health_score >= 90:
        health_advice = "Your loan health is in a superb state. You have low interest rates and a manageable EMI burden. We recommend prioritizing low-cost investing over aggressive prepayments unless you want absolute debt freedom."
    elif health_score >= 75:
        health_advice = "Your loan metrics are good. You can allocate 10-15% of your annual income toward prepayments to clear this loan even faster."
    elif health_score >= 60:
        health_advice = "Your loan health is average. Your interest burden is moderate. Consider locking in an EMI increase of 10% to trim several years off your tenure."
    else:
        health_advice = "Your loan health is poor or dangerous. Your debt burden is very high. Focus on refinancing, cutting discretionary expenses to pay down principal, or consolidating this high-rate debt."
        
    # Moratorium / depreciation reminders
    specific_warning = ""
    if loan_type == "Home Loan":
        specific_warning = "💡 *Home Loan Tip:* You can claim tax deductions on principal (Sec 80C) and interest (Sec 24b) payments. Make sure you optimize to utilize these limit caps."
    elif loan_type == "Car Loan":
        specific_warning = f"💡 *Car Loan Warning:* Cars deprecate by roughly 15% yearly. At your current schedule, make sure your outstanding balance is not higher than the vehicle value."
        
    fallback_text = f"""
## Local Analysis (API Key not provided)
This analysis is generated using local rule-based models. Provide your Groq/OpenAI/HuggingFace API key in the sidebar to enable premium AI-powered financial advisory.

### Summary Analysis
* Your loan of **{currency}{loan_data['loan_amount']:,.2f}** at **{loan_data['interest_rate']}%** for **{loan_data['loan_tenure_months']} months** is classified as **{score_status}** (Health Score: **{health_score}/100**).
* Interest constitutes **{base_details['interest_percentage']}%** of your total payments.
* {health_advice}
* {specific_warning}

---

## 🏆 TOP 3 OPTIMIZATION ACTIONS

{actions_md}
"""
    return fallback_text

def get_ai_recommendations(loan_data, base_details, sim_emi, sim_annual, sim_lump, refinance, health_score, score_status, score_deductions, provider, api_key, model):
    """
    Sends calculations and details to the LLM to get a personalized recommendation report.
    Fails back to local recommendations if no key is provided or if an error occurs.
    """
    client = get_client(provider, api_key)
    
    if not client:
        return generate_local_fallback_advice(
            loan_data, base_details, sim_emi, sim_annual, sim_lump, refinance, health_score, score_status
        )
        
    currency = loan_data.get("currency", "₹")
    loan_type = loan_data.get("loan_type", "Custom Loan")
    
    # Build a context prompt containing all calculated values
    system_prompt = """You are a premium AI financial advisor and loan optimization coach named "EMI Sense AI".
Your tone is professional, encouraging, analytical, and highly structured.
You help users save money by optimizing their loans using the PRE-CALCULATED Python metrics provided.

CRITICAL RULES:
1. NEVER CALCULATE ANY EMI, TENURE, INTEREST, OR SAVINGS YOURSELF.
2. Rely strictly on the Python-calculated metrics provided below.
3. If the user's data indicates high risk, give clear but respectful warnings.
4. Structure your response in clean Markdown.
5. You MUST include a "TOP 3 ACTIONS" section, ranked by interest savings, formatted exactly as:
   ### 1. [Action Name]
   **Potential Savings:** [CurrencySymbol][Savings Amount]
   [1-2 sentences explanation]
   
   ### 2. [Action Name]
   **Potential Savings:** [CurrencySymbol][Savings Amount]
   [1-2 sentences explanation]
   
   ### 3. [Action Name]
   **Potential Savings:** [CurrencySymbol][Savings Amount]
   [1-2 sentences explanation]
"""

    user_prompt = f"""
Here is the loan data and Python-calculated metrics:

LOAN DETAILS:
- Loan Type: {loan_type}
- Principal Amount: {currency}{loan_data['loan_amount']:,.2f}
- Interest Rate: {loan_data['interest_rate']}% annual
- Original Tenure: {loan_data['loan_tenure_months']} months
- Monthly EMI: {currency}{base_details['emi']:,.2f}
- Total Interest: {currency}{base_details['total_interest']:,.2f}
- Total Payment: {currency}{base_details['total_payment']:,.2f}
- Interest % of Total Payment: {base_details['interest_percentage']}%

FINANCIAL STABILITY:
- Monthly Income: {currency}{loan_data['monthly_income']:,.2f}
- Monthly Expenses: {currency}{loan_data['monthly_expenses']:,.2f}
- EMI-to-Income Ratio: {loan_data['emi_ratio']}%
- Available Emergency Fund: {currency}{loan_data['emergency_savings']:,.2f}
- Available Prepayment Budget (Monthly): {currency}{loan_data['extra_monthly_budget']:,.2f}
- Loan Health Score: {health_score}/100 ({score_status})
- Score Deductions/Warnings: {", ".join(score_deductions) if score_deductions else "None"}

SIMULATIONS:
- EMI Increase (+{loan_data.get('emi_increase_pct', 10)}%): New EMI = {currency}{sim_emi['new_emi']:,.2f}, Interest Saved = {currency}{sim_emi['interest_saved']:,.2f}, Tenure Saved = {sim_emi['years_saved']} years
- Annual Prepayment ({currency}{loan_data.get('annual_prepayment', 0):,.2f}): Interest Saved = {currency}{sim_annual['interest_saved']:,.2f}, Tenure Saved = {sim_annual['years_saved']} years
- Lump Sum ({currency}{loan_data.get('lump_sum_amount', 0):,.2f}): Interest Saved = {currency}{sim_lump['interest_saved']:,.2f}, Tenure Saved = {sim_lump['years_saved']} years
- Refinancing (to {loan_data.get('refinance_rate', 0.0)}% at cost of {currency}{loan_data.get('refinance_cost', 0):,.2f}): Worth it? {refinance.get('worth_refinancing', False)}, Net Savings = {currency}{refinance.get('net_savings', 0):,.2f}, Break-even = {refinance.get('break_even_months', 'N/A')} months.

LOAN-SPECIFIC CONTEXT:
- Home Loan Specific (Extra 1 EMI/year Prepay): Interest Saved = {currency}{loan_data.get('home_loan_special_savings', 0.0):,.2f}, Tenure Saved = {loan_data.get('home_loan_special_years', 0.0)} years
- Depreciation/LTV: {loan_data.get('depreciation_text', 'N/A')}

Please write a comprehensive, executive loan optimization summary. Start with a 3-sentence diagnostic analysis of their current loan health, followed by the ranked TOP 3 ACTIONS by interest savings, and conclude with specific advice for a '{loan_type}' and their '{loan_data.get('risk_appetite', 'Moderate')}' risk appetite.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        # Traceback log for debugging, then return local fallback
        print(f"LLM API Call Error: {str(e)}")
        traceback.print_exc()
        return f"*(AI Connection Error - Falling back to local calculator model)*\n\n" + generate_local_fallback_advice(
            loan_data, base_details, sim_emi, sim_annual, sim_lump, refinance, health_score, score_status
        )

def chat_with_coach(chat_history, user_message, loan_data, base_details, health_score, score_status, sim_emi, sim_annual, sim_lump, provider, api_key, model):
    """
    Handles a chatbot turn with the user, maintaining conversation context and loan details.
    """
    client = get_client(provider, api_key)
    
    currency = loan_data.get("currency", "₹")
    loan_type = loan_data.get("loan_type", "Custom Loan")
    
    # If client is not available, return a polite rule-based assistant message
    if not client:
        # Basic parsing of the question to give a simple calculated response
        q = user_message.lower()
        if "increase" in q or "emi" in q:
            ans = f"Based on your simulation, increasing your EMI by {loan_data.get('emi_increase_pct', 10)}% will save you {currency}{sim_emi['interest_saved']:,.2f} in interest and make you debt-free {sim_emi['years_saved']} years faster. I recommend this as a very stable payoff strategy!"
        elif "invest" in q or "prepay" in q or "saving" in q:
            ans = f"Your interest rate is {loan_data['interest_rate']}%. Prepaying guarantees a tax-free return of {loan_data['interest_rate']}%. Since your risk profile is {loan_data.get('risk_appetite', 'Moderate')}, check if your investments can beat this rate. Otherwise, prepaying is the optimal path."
        elif "refinance" in q:
            ans = f"Refinancing rate simulation is set at {loan_data.get('refinance_rate', 0.0)}%. That rate would save you {currency}{loan_data.get('refinance_net_savings', 0.0):,.2f} net of fees. Focus on refinance if the interest rate differential is at least 0.5% - 1%."
        else:
            ans = f"I'd love to analyze this in detail! Please enter your OpenAI/Groq API key in the sidebar to enable the full AI Coach. Based on your current dashboard, your Loan Health Score is {health_score}/100 ({score_status}), and you have an extra monthly prepayment capacity of {currency}{loan_data['extra_monthly_budget']:,.2f}."
        
        return ans

    system_prompt = f"""You are the "EMI Sense AI Coach", a friendly, highly intelligent financial assistant.
You are helping the user optimize their {loan_type}.
Do not calculate EMIs, interest, or tenures yourself. Use the facts provided below.
Always be encouraging, precise, and refer directly to their financial numbers where relevant.
Keep answers concise (under 4 paragraphs) and formatting easy to read with bullet points.

USER FINANCIAL PROFILE & LOAN STATE:
- Loan Type: {loan_type}
- Principal: {currency}{loan_data['loan_amount']:,.2f}
- Interest Rate: {loan_data['interest_rate']}%
- Monthly EMI: {currency}{base_details['emi']:,.2f}
- Monthly Income: {currency}{loan_data['monthly_income']:,.2f}
- Emergency Fund: {currency}{loan_data['emergency_savings']:,.2f}
- Extra Prepayment Budget: {currency}{loan_data['extra_monthly_budget']:,.2f}
- Loan Health Score: {health_score}/100 ({score_status})

PRE-CALCULATED SIMULATION RESULTS:
- EMI Increase (+{loan_data.get('emi_increase_pct', 10)}%): Interest Saved = {currency}{sim_emi['interest_saved']:,.2f}, Years Saved = {sim_emi['years_saved']}
- Annual Prepayment ({currency}{loan_data.get('annual_prepayment', 0):,.2f}): Interest Saved = {currency}{sim_annual['interest_saved']:,.2f}, Years Saved = {sim_annual['years_saved']}
- Lump Sum ({currency}{loan_data.get('lump_sum_amount', 0):,.2f}): Interest Saved = {currency}{sim_lump['interest_saved']:,.2f}, Years Saved = {sim_lump['years_saved']}
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for item in chat_history:
        messages.append({"role": "user", "content": item[0]})
        messages.append({"role": "assistant", "content": item[1]})
        
    # Add the current message
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"*(AI Connection Error - I couldn't reach the AI model. Let me help you locally:)* \n\n" + f"Based on your loan details, your rate is {loan_data['interest_rate']}% and your health score is {health_score}/100. Let me know if you want details on your EMI increase or lump sum prepayments!"
