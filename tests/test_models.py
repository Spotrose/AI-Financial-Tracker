"""
test_models.py - Unit tests for financial models

Tests cover:
- Budget forecasting
- Investment strategies
- Savings optimization
- Debt payoff calculations
- Edge cases and error handling
"""

import unittest
import pandas as pd
from datetime import datetime, timedelta
from core.models import (
    BudgetForecaster,
    InvestmentAdvisor,
    SavingsOptimizer,
    DebtOptimizer
)

class TestBudgetForecaster(unittest.TestCase):
    def setUp(self):
        self.model = BudgetForecaster(window_size=3)
        self.test_data = pd.DataFrame({
            'date': pd.date_range(end='2023-11-01', periods=6, freq='M'),
            'amount': [3500, 4200, 3800, 4100, 3900, 4000]
        })

    def test_forecast_output_structure(self):
        """Test forecast returns proper structure"""
        result = self.model.forecast(self.test_data)
        self.assertIn('prediction', result)
        self.assertIn('confidence_95', result)
        self.assertIsInstance(result['confidence_95'], tuple)
        self.assertEqual(len(result['confidence_95']), 2)

    def test_forecast_values(self):
        """Test forecast values are reasonable"""
        result = self.model.forecast(self.test_data)
        self.assertTrue(3500 <= result['prediction'] <= 4200)
        lower, upper = result['confidence_95']
        self.assertLess(lower, upper)

    def test_insufficient_data(self):
        """Test handling of insufficient data"""
        with self.assertRaises(ValueError):
            self.model.forecast(pd.DataFrame({
                'date': pd.date_range(end='2023-11-01', periods=2, freq='M'),
                'amount': [1000, 2000]
            }))

class TestInvestmentAdvisor(unittest.TestCase):
    def setUp(self):
        self.advisor = InvestmentAdvisor()

    def test_strategy_types(self):
        """Test all risk profile strategies"""
        profiles = ['conservative', 'moderate', 'aggressive']
        for profile in profiles:
            with self.subTest(profile=profile):
                strategy = self.advisor.get_strategy(profile, 5)
                self.assertIn('stocks', strategy)
                self.assertIn('bonds', strategy)
                self.assertGreaterEqual(strategy['stocks'], 0)
                self.assertLessEqual(strategy['stocks'], 100)

    def test_horizon_adjustments(self):
        """Test investment horizon affects allocation"""
        short_term = self.advisor.get_strategy('moderate', 2)
        long_term = self.advisor.get_strategy('moderate', 15)
        self.assertGreater(long_term['stocks'], short_term['stocks'])

    def test_invalid_profile(self):
        """Test handling of invalid risk profile"""
        strategy = self.advisor.get_strategy('invalid', 10)
        self.assertEqual(strategy['stocks'], 50)  # Defaults to moderate

class TestSavingsOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = SavingsOptimizer()

    def test_savings_calculation(self):
        """Test basic savings calculation"""
        result = self.optimizer.calculate_plan(
            current_savings=5000,
            goal_amount=30000,
            timeframe_months=24,
            monthly_income=5000
        )
        self.assertIn('recommended_monthly', result)
        self.assertIn('success_probability', result)
        self.assertTrue(0 <= result['success_probability'] <= 1)

    def test_goal_already_met(self):
        """Test when current savings exceed goal"""
        result = self.optimizer.calculate_plan(
            current_savings=40000,
            goal_amount=30000,
            timeframe_months=12,
            monthly_income=5000
        )
        self.assertEqual(result['recommended_monthly'], 0)
        self.assertEqual(result['success_probability'], 1.0)

    def test_impossible_goal(self):
        """Test unrealistic goals"""
        result = self.optimizer.calculate_plan(
            current_savings=1000,
            goal_amount=100000,
            timeframe_months=12,
            monthly_income=2000
        )
        self.assertTrue(result['investing_advice'])  # Should flag adjustment needed

class TestDebtOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = DebtOptimizer()
        self.sample_debts = [
            {'balance': 10000, 'rate': 0.18, 'min_payment': 200},
            {'balance': 5000, 'rate': 0.06, 'min_payment': 100}
        ]

    def test_debt_plan_structure(self):
        """Test output structure"""
        plan = self.optimizer.optimize(self.sample_debts)
        self.assertIn('total_months', plan)
        self.assertIn('total_interest', plan)
        self.assertGreater(plan['total_months'], 0)

    def test_avalanche_method(self):
        """Test highest interest debt is prioritized"""
        plan = self.optimizer.optimize(self.sample_debts)
        self.assertIn('Avalanche', plan['method'])

    def test_no_debts(self):
        """Test empty debt list handling"""
        plan = self.optimizer.optimize([])
        self.assertEqual(plan['total_months'], 0)
        self.assertEqual(plan['total_interest'], 0)

    def test_debt_free_case(self):
        """Test already debt-free case"""
        plan = self.optimizer.optimize([
            {'balance': 0, 'rate': 0.18, 'min_payment': 200}
        ])
        self.assertEqual(plan['total_months'], 0)

class TestModelIntegration(unittest.TestCase):
    """Test models work together"""
    def test_end_to_end(self):
        """Test models can be used sequentially"""
        # Create sample data
        budget_data = pd.DataFrame({
            'date': pd.date_range(end='2023-11-01', periods=4, freq='M'),
            'amount': [4000, 4100, 3900, 4200]
        })

        # Budget forecast
        forecast = BudgetForecaster().forecast(budget_data)
        self.assertIsInstance(forecast, dict)

        # Investment strategy
        strategy = InvestmentAdvisor().get_strategy('moderate', 10)
        self.assertIsInstance(strategy, dict)

        # Savings plan
        savings_plan = SavingsOptimizer().calculate_plan(
            current_savings=10000,
            goal_amount=50000,
            timeframe_months=36,
            monthly_income=8000
        )
        self.assertIsInstance(savings_plan, dict)

        # Debt plan
        debt_plan = DebtOptimizer().optimize([
            {'balance': 15000, 'rate': 0.15, 'min_payment': 300}
        ])
        self.assertIsInstance(debt_plan, dict)

if __name__ == '__main__':
    unittest.main(verbosity=2)
