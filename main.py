"""
main.py - Financial Tracker Application

Features:
- Unified interface for all financial operations
- Menu-driven interaction
- Integration of all core modules
- Error handling and user feedback
"""
# Improvement Function: Enables loading settings from a config file for flexibility
import configparser
import sys
import pandas as pd
from datetime import datetime
from core.nlp_parser import FinancialTextParser
from core.database import DatabaseManager
from core.models import (
    BudgetForecaster,
    InvestmentAdvisor,
    SavingsOptimizer,
    DebtOptimizer
)

class FinancialTracker:
    def __init__(self):
        """Initialize application components with configurable settings"""
        # Load configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        db_path = config.get('Database', 'path', fallback='financial_tracker.db')
        
        # Initialize components with config values
        self.parser = FinancialTextParser()
        self.db = DatabaseManager(db_path=db_path)  # Pass configurable path
        self.budget_forecaster = BudgetForecaster()
        self.investment_advisor = InvestmentAdvisor()
        self.savings_optimizer = SavingsOptimizer()
        self.debt_optimizer = DebtOptimizer()

    def parse_transaction_input(self):
        """Process natural language transaction input"""
        print("\nEnter transaction (e.g. 'Paid ₹1500 for groceries yesterday'):")
        print("Type 'back' to return to menu")
        
        while True:
            text = input("\n> ").strip()
            if text.lower() == 'back':
                return
            
            if not text:
                print("Please enter a transaction or 'back'")
                continue
                
            result = self.parser.parse(text)
            
            if not result['metadata']['parse_success']:
                print("Couldn't parse that transaction. Try formats like:")
                print("- Paid ₹1000 for rent on 15-11-2023")
                print("- Received 5000 from Alice")
                continue
                
            for txn in result['transactions']:
                self.db.add_transaction(txn)
                print(f"Added: {txn['date']} - {txn['description']}: ₹{txn['amount']}")

    def show_financial_overview(self):
        # Display summary of financial status
        print("\nFinancial Overview")
        print("-----------------")
        overview_data = self.db.get_financial_overview(days_back=30)
        
        # Recent transactions
        print("\nRecent Transactions:")
        transactions = self.db.get_transactions(days_back=30)
        for txn in transactions[:5]:  # Show last 5
            print(f"{txn['date']} - {txn['description']}: ₹{txn['amount']}")
        
        # Budget Summary
        print("\nMonthly Spending Summary:")
        summary = self.db.get_spending_summary()
        for category, amount in summary.items():
            print(f"{category}: ₹{amount}")
        
        # Budget Forecast
        if len(transactions) >= 3:  # Need minimum data
            forecast = self.budget_forecaster.forecast(
                pd.DataFrame(overview_data['transactions']).assign(date=lambda x: pd.to_datetime(x['date']))
            )
            print(f"\nNext Month Forecast: ₹{forecast['prediction']}")
            print(f"Expected Range: ₹{forecast['confidence_95'][0]} to ₹{forecast['confidence_95'][1]}")

    def show_investment_advice(self):
        """Provide investment recommendations"""
        print("\nInvestment Advisor")
        print("-----------------")
        
        # Get user profile
        print("\nYour Investment Profile:")
        age = int(input("Your age: "))
        risk_tolerance = input("Risk tolerance (conservative/moderate/aggressive): ")
        horizon = int(input("Investment horizon (years): "))
        income = float(input("Annual income: "))
        net_worth = float(input("Current net worth: "))
        
        # Get strategy
        strategy = self.investment_advisor.get_strategy(risk_tolerance, horizon)
        
        # Display results
        print("\nRecommended Portfolio Allocation:")
        for asset, allocation in strategy.items():
            if isinstance(allocation, int):
                print(f"{asset}: {allocation}%")
        
        print("\nRecommendations:")
        for advice in strategy.get('rules', []):
            print(f"- {advice}")

    def show_savings_plan(self):
        """Generate savings goal plan"""
        print("\nSavings Goal Planner")
        print("-------------------")
        
        goal = float(input("Target amount: ₹"))
        timeframe = int(input("Months to achieve goal: "))
        current = float(input("Current savings: ₹"))
        income = float(input("Monthly after-tax income: ₹"))
        
        plan = self.savings_optimizer.calculate_plan(
            current_savings=current,
            goal_amount=goal,
            timeframe_months=timeframe,
            monthly_income=income
        )
        
        print("\nSavings Plan:")
        print(f"Required monthly: ₹{plan['recommended_monthly']}")
        print(f"Success probability: {plan['success_probability']*100:.0f}%")
        if plan['investing_advice']:
            print("\nNote: Consider adjusting timeline or increasing income")

    def show_debt_plan(self):
        """Generate debt payoff strategy"""
        print("\nDebt Payoff Planner")
        print("------------------")
        
        debts = []
        while True:
            print("\nAdd Debt (leave balance blank when done)")
            balance = input("Current balance: ₹")
            if not balance:
                break
                
            rate = float(input("Annual interest rate (%): ")) / 100
            min_pay = float(input("Minimum monthly payment: ₹"))
            
            debts.append({
                'balance': float(balance),
                'rate': rate,
                'min_payment': min_pay
            })
        
        if debts:
            plan = self.debt_optimizer.optimize(debts)
            print(f"\nPayoff Plan ({plan['method']}):")
            print(f"Total months: {plan['total_months']}")
            print(f"Total interest: ₹{plan['total_interest']:.2f}")
        else:
            print("No debts added")

    def run(self):
        """Main application loop"""
        while True:
            print("\nAI Financial Tracker")
            print("===================")
            print("1. Add Transaction")
            print("2. Financial Overview")
            print("3. Investment Advice")
            print("4. Savings Plan")
            print("5. Debt Payoff Plan")
            print("6. Exit")
            
            choice = input("\nSelect an option (1-6): ")
            
            try:
                if choice == '1':
                    self.parse_transaction_input()
                elif choice == '2':
                    self.show_financial_overview()
                elif choice == '3':
                    self.show_investment_advice()
                elif choice == '4':
                    self.show_savings_plan()
                elif choice == '5':
                    self.show_debt_plan()
                elif choice == '6':
                    print("\nExiting application...")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please enter 1-6")
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try again or contact support")

if __name__ == "__main__":
    app = FinancialTracker()
    app.run()