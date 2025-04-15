"""
nlp_parser.py - Natural Language Parser for financial inputs

Features:
- Parse multi-transaction inputs (e.g., "I paid 20 rupees for Panipuris and 50 rupees for a movie ticket")
- Integration with categories.py for category lookups
- Flexible rule-based parsing for actions, amounts, items, etc.
"""

import re
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
try:
    from core.database import DatabaseManager
except ImportError:
    from database import DatabaseManager
try:
    from core.categories import suggest_category, validate_category, get_category_hierarchy
except ImportError:
    from categories import suggest_category, validate_category, get_category_hierarchy

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NLPParser:
    def __init__(self):
        self.db = DatabaseManager()
        self.transaction_keywords = {
            'paid': 'expense',
            'bought': 'expense',
            'spent': 'expense',
            'received': 'income',
            'earned': 'income',
            'got': 'income'
        }
        self.time_keywords = {
            'today': timedelta(days=0),
            'yesterday': timedelta(days=-1),
            'tomorrow': timedelta(days=1),
            'last week': timedelta(days=-7),
            'next week': timedelta(days=7)
        }
        self.group_keywords = {
            'common': 2,
            'family': 3,
            'friends': 4
        }

    def parse(self, input_text: str) -> List[Dict]:
        logger.debug(f"Parsing input: {input_text}")
        input_text = input_text.lower().strip()
        transactions = []

        parts = re.split(r'\s+and\s+', input_text)
        current_action = None
        for part in parts:
            for keyword in self.transaction_keywords:
                if keyword in part:
                    current_action = keyword
                    break
            if current_action:
                transaction = self._parse_single_transaction(part, current_action)
                if transaction:
                    transactions.append(transaction)
            else:
                transactions.append({'type': 'error', 'message': f"No action found in part: {part}"})
        
        return transactions if transactions else [{'type': 'error', 'message': 'No valid transactions found'}]

    def _parse_single_transaction(self, text: str, action: str = None) -> Optional[Dict]:
        try:
            transaction = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'description': '',
                'amount': 0.0,
                'currency': 'INR',
                'main_category': 'Miscellaneous',
                'sub_category': 'unexpected',
                'type': 'expense',
                'person': None,
                'group': None,
                'split_ratio': 1
            }

            if action:
                transaction['type'] = self.transaction_keywords[action]
            else:
                for keyword, t_type in self.transaction_keywords.items():
                    if keyword in text:
                        action = keyword
                        transaction['type'] = t_type
                        break
                if not action:
                    raise ValueError("No valid action found")

            amount_match = re.search(r'(\d+\.?\d*)\s*(rupees)?', text)
            if amount_match:
                transaction['amount'] = float(amount_match.group(1))
            else:
                raise ValueError("No amount found")

            item_match = re.search(r'(?:for|on|from|of|worth of)\s+(.+?)(?:\s+(?:by|for|with|from|and|$))', text)
            if item_match:
                item = item_match.group(1).strip()
                main_cat, sub_cat = suggest_category(item, transaction['type'])
                transaction['main_category'] = main_cat
                transaction['sub_category'] = sub_cat
                transaction['description'] = item
            else:
                transaction['description'] = text.split(action)[-1].strip()

            person_match = re.search(r'(?:by|from)\s+([a-z]+)', text)
            if person_match:
                transaction['person'] = person_match.group(1).capitalize()
            elif 'i ' not in text.lower() and action not in text.split()[0]:
                person = text.split()[0]
                if person.isalpha() and person not in self.transaction_keywords:
                    transaction['person'] = person.capitalize()

            for keyword, delta in self.time_keywords.items():
                if keyword in text:
                    transaction['date'] = (datetime.now() + delta).strftime('%Y-%m-%d')
                    break

            for group_name, default_split in self.group_keywords.items():
                if group_name in text:
                    transaction['group'] = group_name
                    split_match = re.search(r'(\d+)\s*(?:people|persons|members)', text)
                    transaction['split_ratio'] = 1 / (int(split_match.group(1)) if split_match else default_split)
                    break

            logger.debug(f"Parsed transaction: {transaction}")
            return {'type': 'transaction', 'data': transaction}
        except Exception as e:
            logger.error(f"Transaction parsing error: {str(e)}")
            return None

    def process(self, input_text: str) -> Dict:
        results = self.parse(input_text)
        response = {'status': 'success', 'transactions': [], 'errors': []}
        
        for result in results:
            if result['type'] == 'transaction':
                self.db.add_transaction(result['data'])
                response['transactions'].append(result['data'])
            else:
                response['errors'].append(result['message'])
                response['status'] = 'partial' if response['transactions'] else 'error'
        
        response['message'] = 'Transactions processed' if response['transactions'] else 'No transactions processed'
        return response

if __name__ == "__main__":
    parser = NLPParser()
    test_inputs = [
        "I paid 20 rupees for Panipuris and 50 rupees for a movie ticket",
        "Deepak paid 100 rupees for sabji",
        "I bought 200 rupees worth of groceries",
        "I spent 100 rupees on clothes",
        "I received 200 from Deepak",
        "I received salary of 40000"
    ]
    
    for input_text in test_inputs:
        print(f"\nInput: {input_text}")
        result = parser.process(input_text)
        print(f"Result: {result}")