# EMI Sense AI

> **"Don't just calculate your loan. Optimize it."**

EMI Sense AI is a premium, AI-powered loan optimization dashboard designed to act like a personal financial advisor. Rather than just computing standard monthly payments and interest costs, it evaluates your complete financial profile, models dynamic prepayment/refinancing optimizations, computes a Loan Health Index score, and provides structured strategic recommendations using LLM engines.

---

## 🌟 Key Features

1. **📊 Advisor Diagnostics & Health Index:**
   * Computes a weighted Loan Health Score (0-100) analyzing debt levels, income ratio, rates, and cash buffers.
   * Compiles smart risk alerts for high-interest rates, low reserves, or heavy payment ratios.
2. **⚡ Real-time Prepayment Simulators:**
   * **EMI Increase Simulator:** Model the visual impact of increasing your monthly payment.
   * **One-time Lump Sum Simulator:** Run tenure-reduction calculations.
   * **Annual Prepayment Simulator:** Evaluate regular extra yearly prepayments.
   * **Refinance/Balance Transfer Analyzer:** Check break-even milestones and net savings.
3. **🔍 Risk & Strategic Analyses:**
   * Debt-to-Income runway calculators.
   * Payoff milestones mapped against your demographic retirement goals.
   * Advanced What-If Scenario Matrix (income shocks, salary hikes, or rate shifts).
   * Prepay vs. Investment Growth trade-off profiles.
   * Side-by-side comparative calculators.
4. **📈 Interactive Charts:**
   * 6 dynamic Plotly schedules including Outstanding Principal timelines, Cumulative Interest, EMI Composition, and Debt-Free milestone charts.
5. **📄 PDF Executive Reports:**
   * Generate and export high-fidelity PDF reports detailing key diagnostic insights, prepay guidelines, and AI suggestions.
6. **💬 AI Loan Coach Chat Room:**
   * Chat in real-time with an AI Financial Coach regarding loan strategies (supports Groq, HuggingFace, and OpenAI).

---

## 🛠️ Tech Stack

* **Frontend:** Gradio
* **Backend Calculations:** Python Financial Formulas
* **Charts:** Plotly / Matplotlib
* **PDF Exporter:** ReportLab
* **LLM Engine:** OpenAI Client (supporting Groq, OpenAI, and HuggingFace API endpoints)

---

## 📁 Repository Structure

* `app.py`: Main Gradio dashboard entry point, interface layouts, and UI callbacks.
* `calculations.py`: Core mathematical engines (amortization schedules, what-if simulators, loan health score, runway budgets).
* `charts.py`: Generation functions for Plotly interactive plots.
* `ai_engine.py`: Structured prompt formatting, fallback rule-based models, and LLM integrations.
* `pdf_generator.py`: PDF report styling, document flows, and export rendering.
* `style.css`: Premium dark mode CSS stylesheet.
* `test_calculations.py`: Suite of math correctness unit tests.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* Install dependencies:
  ```bash
  pip install gradio pandas plotly matplotlib reportlab openai
  ```

### Setting API Keys (Optional)
To activate the AI advisor recommendation panels and the chat room, set your API key as an environment variable before running:
```bash
export GROQ_API_KEY="your_groq_api_key"
# or
export OPENAI_API_KEY="your_openai_api_key"
```

### Running the App
Start the Gradio server:
```bash
python3 app.py
```
Open your browser and navigate to:
👉 **http://127.0.0.1:7860**

### Running Unit Tests
Validate calculation formulas:
```bash
python3 test_calculations.py
```
