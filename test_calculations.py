import unittest
from calculations import (
    calculate_emi,
    simulate_amortization,
    calculate_base_loan_details,
    simulate_emi_increase,
    simulate_annual_prepayment,
    simulate_lump_sum,
    calculate_refinancing,
    calculate_emi_to_income,
    calculate_emergency_fund,
    calculate_health_score
)

class TestFinancialCalculations(unittest.TestCase):
    
    def test_emi_calculation(self):
        # Test case: Principal=100000, 10% rate, 12 months
        # Monthly r = 10 / 12 / 100 = 0.008333333333333333
        # EMI = 100000 * r * (1+r)^12 / ((1+r)^12 - 1) = 8791.59
        emi = calculate_emi(100000, 10.0, 12)
        self.assertAlmostEqual(emi, 8791.59, places=1)
        
        # Test case with 0 rate
        emi_zero_rate = calculate_emi(120000, 0.0, 12)
        self.assertEqual(emi_zero_rate, 10000.0)

    def test_amortization(self):
        # Verify base amortization ends with 0 balance
        schedule = simulate_amortization(100000, 10.0, 12)
        self.assertEqual(len(schedule), 12)
        self.assertLessEqual(schedule[-1]["remaining_balance"], 0.05)
        
    def test_emi_increase(self):
        # 10% increase in EMI should reduce tenure and save interest
        result = simulate_emi_increase(100000, 10.0, 12, 10.0)
        self.assertLess(result["new_tenure_months"], 12)
        self.assertGreater(result["interest_saved"], 0)
        
    def test_annual_prepayment(self):
        # Prepay 5000 every year on a 100000 loan for 36 months (3 years)
        result = simulate_annual_prepayment(100000, 10.0, 36, 10000.0)
        self.assertLess(result["new_tenure_months"], 36)
        self.assertGreater(result["interest_saved"], 0)
        
    def test_lump_sum(self):
        # Keep EMI, reduce tenure
        result_tenure = simulate_lump_sum(100000, 10.0, 36, 10000.0, mode="reduce_tenure")
        self.assertLess(result_tenure["new_tenure_months"], 36)
        self.assertEqual(result_tenure["new_emi"], calculate_emi(100000, 10.0, 36))
        
        # Keep tenure, reduce EMI
        result_emi = simulate_lump_sum(100000, 10.0, 36, 10000.0, mode="reduce_emi")
        self.assertEqual(result_emi["new_tenure_months"], 36)
        self.assertLess(result_emi["new_emi"], calculate_emi(100000, 10.0, 36))

    def test_refinancing(self):
        # Test refinance from 12% to 8% with 1000 cost
        res = calculate_refinancing(100000, 12.0, 24, 8.0, 1000.0)
        self.assertTrue(res["worth_refinancing"])
        self.assertGreater(res["net_savings"], 0)
        
    def test_health_score(self):
        # High income, low rate, good emergency reserve should yield a high score
        score, status, deductions = calculate_health_score(
            principal=100000,
            annual_rate=8.0,
            tenure_months=60,
            emi=2000,
            income=20000,
            expenses=5000,
            current_reserve=50000,
            extra_monthly=2000,
            loan_type="Home Loan"
        )
        self.assertGreaterEqual(score, 80)
        self.assertEqual(status, "Excellent")

if __name__ == '__main__':
    unittest.main()
