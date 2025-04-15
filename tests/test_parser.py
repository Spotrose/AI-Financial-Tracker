"""
test_parser.py - Unit tests for the FinancialTextParser class

Tests cover:
- Basic transaction parsing
- Amount extraction
- Date parsing (absolute/relative)
- Person/group detection
- Error handling
- Edge cases
"""

import unittest
from datetime import datetime, timedelta
from core.nlp_parser import FinancialTextParser

class TestFinancialTextParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = FinancialTextParser()
        cls.today = datetime.now().date()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)

    def test_basic_expense(self):
        """Test simple expense parsing"""
        text = "Paid ₹1500 for groceries"
        result = self.parser.parse(text)
        
        self.assertTrue(result['metadata']['parse_success'])
        self.assertEqual(len(result['transactions']), 1)
        
        txn = result['transactions'][0]
        self.assertEqual(txn['amount'], 1500.0)
        self.assertEqual(txn['description'], 'groceries')
        self.assertEqual(txn['type'], 'expense')
        self.assertEqual(txn['date'], str(self.today))

    def test_income_parsing(self):
        """Test income transaction detection"""
        text = "Received 5000 from Alice as salary"
        result = self.parser.parse(text)
        
        txn = result['transactions'][0]
        self.assertEqual(txn['type'], 'income')
        self.assertEqual(txn['person'], 'Alice')
        self.assertEqual(txn['description'], 'salary')

    def test_multiple_amounts(self):
        """Test parsing multiple amounts in one sentence"""
        text = "Spent 200 on food and 300 on transport"
        result = self.parser.parse(text)
        
        self.assertEqual(len(result['transactions']), 2)
        self.assertEqual(result['transactions'][0]['amount'], 200.0)
        self.assertEqual(result['transactions'][1]['amount'], 300.0)

    def test_date_parsing(self):
        """Test various date formats"""
        test_cases = [
            ("Paid 100 on 15-11-2023", "2023-11-15"),
            ("Paid 100 on 11/15/23", "2023-11-15"),
            ("Paid 100 yesterday", str(self.yesterday)),
            ("Paid 100 tomorrow", str(self.tomorrow))
        ]
        
        for text, expected_date in test_cases:
            with self.subTest(text=text):
                result = self.parser.parse(text)
                self.assertEqual(result['transactions'][0]['date'], expected_date)

    def test_person_detection(self):
        """Test extraction of involved persons"""
        test_cases = [
            ("Paid 100 to Alice", "Alice"),
            ("Received 200 from Bob", "Bob"),
            ("Spent 300 with Charlie", "Charlie"),
            ("Paid 400", None)  # No person
        ]
        
        for text, expected_person in test_cases:
            with self.subTest(text=text):
                result = self.parser.parse(text)
                self.assertEqual(result['transactions'][0]['person'], expected_person)

    def test_group_expenses(self):
        """Test group expense detection"""
        text = "Paid 1000 for dinner with friends divided by 4"
        result = self.parser.parse(text)
        
        txn = result['transactions'][0]
        self.assertEqual(txn['group'], 'friends')
        self.assertEqual(txn['split_ratio'], 4)

    def test_currency_detection(self):
        """Test different currency notations"""
        test_cases = [
            ("Paid ₹100", "INR"),
            ("Paid 100 rupees", "INR"),
            ("Paid 100 rs", "INR"),
            ("Paid $100", "USD")
        ]
        
        for text, expected_currency in test_cases:
            with self.subTest(text=text):
                result = self.parser.parse(text)
                self.assertEqual(result['transactions'][0]['currency'], expected_currency)

    def test_error_handling(self):
        """Test malformed inputs"""
        test_cases = [
            "Paid for groceries",  # No amount
            "Received from Alice",  # No amount
            "Random text",  # No transaction
            ""  # Empty string
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = self.parser.parse(text)
                self.assertFalse(result['metadata']['parse_success'])
                self.assertEqual(len(result['transactions']), 0)

    def test_edge_cases(self):
        """Test unusual but valid inputs"""
        test_cases = [
            ("Paid 1.50 for candy", 1.5),  # Decimal amounts
            ("Paid 1000000 for car", 1000000.0),  # Large numbers
            ("Received 1 as gift", 1.0),  # Small amounts
            ("Paid 100 for A B C D E", "A B C D E")  # Long descriptions
        ]
        
        for text, expected_value in test_cases:
            with self.subTest(text=text):
                result = self.parser.parse(text)
                key = 'amount' if isinstance(expected_value, float) else 'description'
                self.assertEqual(result['transactions'][0][key], expected_value)

if __name__ == '__main__':
    unittest.main()