"""
models.py - Rule-based and statistical models for personal finance management

Features:
- Moving average budget forecasting
- Risk-profile-based investment allocation
- Debt payoff optimization (Avalanche and Snowball methods)
- Savings goal probability calculator
- Emergency fund advisor
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from scipy.stats import norm
import warnings
import logging

try:
    from core.database import DatabaseManager
except ImportError:
    from database import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

class BudgetForecaster:
    def __init__(self, window_size: int = 3, confidence_level: float = 0.95):
        self.window_size = window_size
        self.confidence_level = confidence_level
        self.z_score = norm.ppf(1 - (1 - confidence_level) / 2)
        
    def forecast(self, historical_data: pd.DataFrame) -> Dict:
        try:
            logger.debug(f"Forecasting with {len(historical_data)} transactions")
            if historical_data.empty or not all(col in historical_data for col in ['date', 'amount']):
                logger.warning("No valid historical data for forecasting")
                return {'error': 'No valid historical data available'}
            
            historical_data['date'] = pd.to_datetime(historical_data['date'])
            monthly = historical_data.resample('M', on='date').sum()
            if len(monthly) < self.window_size:
                prediction = float(round(monthly['amount'].mean(), 2)) if not monthly.empty else 0.0
                logger.debug(f"Insufficient data, using mean: {prediction}")
                return {
                    'prediction': prediction,
                    'confidence_interval': (None, None),
                    'method': f'{self.window_size}-month moving average (insufficient data)',
                    'confidence_level': self.confidence_level
                }
            
            rolling_mean = monthly['amount'].rolling(window=self.window_size).mean()
            rolling_std = monthly['amount'].rolling(window=self.window_size).std()
            
            last_mean = rolling_mean.iloc[-1]
            last_std = rolling_std.iloc[-1]
            
            result = {
                'prediction': float(round(last_mean, 2)),
                'confidence_interval': (
                    float(round(last_mean - self.z_score * last_std, 2)),
                    float(round(last_mean + self.z_score * last_std, 2))
                ),
                'method': f'{self.window_size}-month moving average',
                'confidence_level': self.confidence_level
            }
            logger.debug(f"Forecast result: {result}")
            return result
        except Exception as e:
            logger.error(f"Forecast error: {str(e)}")
            return {'error': str(e)}

class InvestmentAdvisor:
    def get_strategy(self, risk_profile: str, investment_horizon: int) -> Dict:
        try:
            if investment_horizon <= 0:
                raise ValueError("Investment horizon must be positive")
            if risk_profile.lower() not in ['conservative', 'moderate', 'aggressive']:
                raise ValueError("Risk profile must be 'conservative', 'moderate', or 'aggressive'")
                
            strategies = {
                'conservative': {'stocks': 30, 'bonds': 50, 'gold': 15, 'cash': 5, 'rules': ['Focus on capital preservation', 'Recommend: Index funds + government bonds']},
                'moderate': {'stocks': 50, 'bonds': 35, 'gold': 10, 'cash': 5, 'rules': ['Balance growth and stability', 'Recommend: Balanced mutual funds']},
                'aggressive': {'stocks': 70, 'bonds': 20, 'gold': 5, 'cash': 5, 'rules': ['Long-term growth focus', 'Recommend: Growth stocks + sector ETFs']}
            }
            
            base = strategies.get(risk_profile.lower(), strategies['moderate']).copy()
            if investment_horizon > 10:
                base['stocks'] = min(base['stocks'] + 10, 100)
                base['bonds'] = max(base['bonds'] - 10, 0)
            elif investment_horizon < 3:
                base['stocks'] = max(base['stocks'] - 20, 0)
                base['cash'] = min(base['cash'] + 20, 100)
                
            logger.debug(f"Investment strategy for {risk_profile}: {base}")
            return base
        except Exception as e:
            logger.error(f"Investment strategy error: {str(e)}")
            return {'error': str(e)}

class SavingsOptimizer:
    def calculate_plan(self, current_savings: float, goal_amount: float,
                      timeframe_months: int, monthly_income: float) -> Dict:
        try:
            if any(x < 0 for x in [current_savings, goal_amount, monthly_income]):
                raise ValueError("Savings, goal, and income must be non-negative")
            if timeframe_months <= 0:
                raise ValueError("Timeframe must be positive")
            
            months = max(timeframe_months, 1)
            required = (goal_amount - current_savings) / months
            affordable = min(required, monthly_income * 0.3)
            
            mean_return = 0.07 / 12
            std_dev = 0.15 / np.sqrt(12)
            simulations = 1000
            
            monthly_returns = np.random.normal(mean_return, std_dev, (simulations, months))
            growth_factors = np.prod(1 + monthly_returns, axis=1)
            final_values = current_savings * growth_factors + affordable * np.sum(
                growth_factors[:, None] / np.cumprod(1 + monthly_returns, axis=1), axis=1
            )
            
            success_rate = np.mean(final_values >= goal_amount)
            
            result = {
                'required_monthly': round(required, 2),
                'recommended_monthly': round(affordable, 2),
                'success_probability': float(round(success_rate, 2)),
                'investing_advice': bool(success_rate < 0.7)
            }
            logger.debug(f"Savings plan: {result}")
            return result
        except Exception as e:
            logger.error(f"Savings plan error: {str(e)}")
            return {'error': str(e)}

class DebtOptimizer:
    def optimize(self, debts: List[Dict], method: str = 'avalanche') -> Dict:
        try:
            if not debts:
                result = {
                    'total_months': 0,
                    'total_interest': 0,
                    'method': 'No debts provided'
                }
                logger.debug(f"Debt optimization: {result}")
                return result
            required_keys = {'balance', 'rate', 'min_payment'}
            for debt in debts:
                if not required_keys.issubset(debt.keys()):
                    raise ValueError("Each debt must have 'balance', 'rate', and 'min_payment'")
                if any(debt[k] < 0 for k in required_keys):
                    raise ValueError("Debt values must be non-negative")
            
            if method.lower() == 'snowball':
                sorted_debts = sorted(debts, key=lambda x: x['balance'])
                method_name = 'Snowball (Lowest Balance First)'
            else:
                sorted_debts = sorted(debts, key=lambda x: x['rate'], reverse=True)
                method_name = 'Avalanche (Highest Interest First)'
            
            remaining = [{**d} for d in sorted_debts]
            total_payment = sum(d['min_payment'] for d in sorted_debts)
            total_interest = 0
            months = 0
            
            while any(d['balance'] > 0 for d in remaining):
                months += 1
                month_interest = 0
                available = total_payment
                
                # Apply interest
                for debt in remaining:
                    if debt['balance'] > 0:
                        interest = debt['balance'] * debt['rate'] / 12
                        debt['balance'] += interest
                        month_interest += interest
                
                # Apply minimum payments
                for debt in remaining:
                    if debt['balance'] > 0:
                        payment = min(debt['min_payment'], available, debt['balance'])
                        debt['balance'] = max(0, debt['balance'] - payment)
                        available -= payment
                
                # Apply remaining to priority debt
                for debt in remaining:
                    if debt['balance'] > 0 and available > 0:
                        payment = min(debt['balance'], available)
                        debt['balance'] = max(0, debt['balance'] - payment)
                        available -= payment
                        break
                
                total_interest += month_interest
                if months > 1000:  # Safety break
                    raise ValueError("Debt payoff exceeds 1000 months")
            
            result = {
                'total_months': months,
                'total_interest': round(total_interest, 2),
                'method': method_name
            }
            logger.debug(f"Debt optimization result: {result}")
            return result
        except Exception as e:
            logger.error(f"Debt optimization error: {str(e)}")
            return {'error': str(e)}

class EmergencyFundAdvisor:
    def __init__(self, min_months: int = 3, max_months: int = 6):
        self.min_months = min_months
        self.max_months = max_months
    
    def recommend(self, expense_data: pd.DataFrame, income_stability: str = 'stable', 
                 dependents: int = 0) -> Dict:
        try:
            logger.debug(f"Emergency fund recommendation with {len(expense_data)} expense transactions")
            if expense_data.empty or not all(col in expense_data for col in ['date', 'amount']):
                logger.warning("No valid expense data for emergency fund")
                return {'error': 'No valid expense data available'}
            
            expense_data['date'] = pd.to_datetime(expense_data['date'])
            monthly_expenses = expense_data.resample('M', on='date').sum()['amount']
            avg_expense = monthly_expenses.mean()
            std_expense = monthly_expenses.std()
            
            # Handle single data point or no variation
            if pd.isna(std_expense) or std_expense == 0:
                std_expense = avg_expense * 0.1  # Assume 10% of mean as fallback
            
            base_min = avg_expense * self.min_months
            base_max = avg_expense * self.max_months
            
            adjustment_factor = 1.0
            if income_stability == 'variable':
                adjustment_factor += 0.2
            adjustment_factor += 0.1 * dependents
            
            recommended_min = base_min * adjustment_factor
            recommended_max = base_max * adjustment_factor
            
            buffer = avg_expense + 2 * std_expense
            prob_sufficient = norm.cdf(recommended_max, loc=buffer * 3, scale=std_expense * np.sqrt(3))
            
            result = {
                'recommended_range': (float(round(recommended_min, 2)), float(round(recommended_max, 2))),
                'avg_monthly_expense': float(round(avg_expense, 2)),
                'probability_sufficient': float(round(prob_sufficient, 2)) if not pd.isna(prob_sufficient) else 0.5,
                'factors': {'income_stability': income_stability, 'dependents': dependents}
            }
            logger.debug(f"Emergency fund result: {result}")
            return result
        except Exception as e:
            logger.error(f"Emergency fund error: {str(e)}")
            return {'error': str(e)}

if __name__ == "__main__":
    logger.debug("Starting models.py execution")
    db = DatabaseManager()
    transactions = db.get_transactions(days_back=365)
    expense_transactions = db.get_transactions(days_back=365, transaction_type='expense')
    
    print("Raw transactions:", transactions)
    print("Raw expense transactions:", expense_transactions)
    
    all_data = pd.DataFrame(transactions)
    expense_data = pd.DataFrame(expense_transactions)
    
    forecaster = BudgetForecaster()
    print("Budget Forecast:")
    print(forecaster.forecast(all_data))

    advisor = InvestmentAdvisor()
    print("\nInvestment Strategy:")
    print(advisor.get_strategy('moderate', 10))

    savings_calc = SavingsOptimizer()
    print("\nSavings Plan:")
    print(savings_calc.calculate_plan(
        current_savings=5000,
        goal_amount=30000,
        timeframe_months=24,
        monthly_income=5000
    ))

    debts = [
        {'balance': 10000, 'rate': 0.18, 'min_payment': 200},
        {'balance': 5000, 'rate': 0.06, 'min_payment': 100}
    ]
    debt_plan = DebtOptimizer().optimize(debts, method='avalanche')
    print("\nDebt Payoff Plan (Avalanche):")
    print(debt_plan)
    
    debt_plan_snowball = DebtOptimizer().optimize(debts, method='snowball')
    print("\nDebt Payoff Plan (Snowball):")
    print(debt_plan_snowball)
    
    emergency_advisor = EmergencyFundAdvisor()
    print("\nEmergency Fund Recommendation:")
    print(emergency_advisor.recommend(expense_data, income_stability='variable', dependents=2))
    logger.debug("Completed models.py execution")
