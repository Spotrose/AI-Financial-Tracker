"""
database.py - SQLite database operations for financial tracking

Features:
- Context-managed database connections
- CRUD operations for all tables
- Automatic budget updates
- Debt calculations
- Data validation
- Reporting utilities
- Bulk transaction insertion
- Indexed tables for performance
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Generator, Any
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the financial tracker"""
    
    def __init__(self, db_path: str = None):
        self.project_root = os.path.abspath(os.path.dirname(__file__))
        self.db_path = db_path or os.path.join(self.project_root, '..', 'financial_tracker.db')
        logger.debug(f"Initializing DatabaseManager with db_path: {self.db_path}")
        self._initialize_database()
        
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        logger.debug(f"Opening connection to {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
            logger.debug(f"Closed connection to {self.db_path}")

    def _initialize_database(self) -> None:
        logger.debug(f"Creating database schema at {self.db_path}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS persons (
                    person_id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    contact TEXT,
                    total_owed REAL DEFAULT 0,
                    relationship TEXT CHECK(relationship IN 
                        ('family', 'friend', 'colleague', 'business', 'other'))
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY,
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'INR',
                    main_category TEXT NOT NULL,
                    sub_category TEXT NOT NULL,
                    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
                    person_id INTEGER,
                    group_name TEXT,
                    split_ratio TEXT,
                    FOREIGN KEY(person_id) REFERENCES persons(person_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    monthly_limit REAL NOT NULL,
                    current_spending REAL DEFAULT 0,
                    reset_date DATE NOT NULL
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON transactions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON transactions(main_category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_person_id ON transactions(person_id)')
            conn.commit()
            logger.debug("Database schema initialized")

    def _validate_transaction(self, transaction: Dict[str, Any]) -> None:
        required_fields = ['date', 'description', 'amount', 'main_category', 'sub_category', 'type']
        for field in required_fields:
            if field not in transaction or transaction[field] is None:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(transaction['amount'], (int, float)) or transaction['amount'] <= 0:
            raise ValueError("Amount must be a positive number")
        if transaction['type'] not in ['income', 'expense']:
            raise ValueError("Type must be 'income' or 'expense'")

    def _get_person_id(self, person_name: Optional[str], conn: sqlite3.Connection) -> Optional[int]:
        if not person_name:
            return None
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO persons (name) VALUES (?)", (person_name,))
        cursor.execute("SELECT person_id FROM persons WHERE name = ?", (person_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def add_transaction(self, transaction: Dict[str, Any]) -> None:
        logger.debug(f"Adding transaction: {transaction}")
        self._validate_transaction(transaction)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                person_id = self._get_person_id(transaction.get('person'), conn)
                cursor.execute('''
                    INSERT INTO transactions 
                    (date, description, amount, currency, main_category, 
                     sub_category, type, person_id, group_name, split_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction['date'],
                    transaction['description'],
                    transaction['amount'],
                    transaction.get('currency', 'INR'),
                    transaction['main_category'],
                    transaction['sub_category'],
                    transaction['type'],
                    person_id,
                    transaction.get('group'),
                    json.dumps(transaction.get('split_ratio', 1))
                ))
                if transaction['type'] == 'expense':
                    self._update_budget(transaction['main_category'], transaction['amount'], conn)
                if transaction.get('person'):
                    self._update_person_balance(transaction['person'], transaction['amount'], transaction['type'], conn)
                conn.commit()
                logger.debug(f"Transaction added: {transaction['description']}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database error: {str(e)}")
                raise RuntimeError(f"Database error: {str(e)}")

    def bulk_add_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        logger.debug(f"Adding {len(transactions)} transactions")
        for t in transactions:
            self._validate_transaction(t)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Pre-insert all persons
                person_ids = {}
                for t in transactions:
                    if t.get('person'):
                        person_ids[t['person']] = self._get_person_id(t['person'], conn)
                
                # Check for existing transactions to avoid duplicates
                existing = set()
                cursor.execute("SELECT date, description, amount FROM transactions")
                for row in cursor.fetchall():
                    existing.add((row['date'], row['description'], row['amount']))
                
                # Filter out duplicates
                new_transactions = [
                    t for t in transactions
                    if (t['date'], t['description'], t['amount']) not in existing
                ]
                
                if not new_transactions:
                    logger.debug("No new transactions to add (all duplicates)")
                    conn.commit()
                    return
                
                # Insert new transactions
                cursor.executemany('''
                    INSERT INTO transactions 
                    (date, description, amount, currency, main_category, 
                    sub_category, type, person_id, group_name, split_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
                    (
                        t['date'],
                        t['description'],
                        t['amount'],
                        t.get('currency', 'INR'),
                        t['main_category'],
                        t['sub_category'],
                        t['type'],
                        person_ids.get(t.get('person')),
                        t.get('group'),
                        json.dumps(t.get('split_ratio', 1))
                    ) for t in new_transactions
                ])
                for t in new_transactions:
                    if t['type'] == 'expense':
                        self._update_budget(t['main_category'], t['amount'], conn)
                    if t.get('person'):
                        self._update_person_balance(t['person'], t['amount'], t['type'], conn)
                conn.commit()
                logger.debug("Bulk transactions added successfully")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database error: {str(e)}")
                raise RuntimeError(f"Database error: {str(e)}")

    def _update_budget(self, category: str, amount: float, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO budgets 
            (category, monthly_limit, reset_date)
            VALUES (?, 0, ?)
        ''', (category, datetime.now().date()))
        cursor.execute('''
            UPDATE budgets 
            SET current_spending = current_spending + ? 
            WHERE category = ?
        ''', (amount, category))
        cursor.execute('''
            UPDATE budgets
            SET current_spending = 0,
                reset_date = DATE(reset_date, '+1 month')
            WHERE reset_date < DATE('now')
        ''')

    def _update_person_balance(self, person_name: str, amount: float, transaction_type: str, conn: sqlite3.Connection) -> None:
        modifier = 1 if transaction_type == 'expense' else -1
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE persons
            SET total_owed = total_owed + ?
            WHERE name = ?
        ''', (amount * modifier, person_name))

    def get_transactions(self, days_back: int = 30, transaction_type: Optional[str] = None) -> List[Dict]:
        logger.debug(f"Fetching transactions (days_back={days_back}, type={transaction_type})")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT t.*, p.name 
                FROM transactions t
                LEFT JOIN persons p ON t.person_id = p.person_id
                WHERE 1=1
            '''
            params = []
            if transaction_type:
                query += ' AND type = ?'
                params.append(transaction_type)
            if days_back is not None:
                query += ' AND date >= DATE("now", ?)'
                params.append(f'-{days_back} days')
            query += ' ORDER BY date DESC'
            cursor.execute(query, params)
            transactions = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"Fetched {len(transactions)} transactions")
            return transactions

    def get_budgets(self) -> Dict[str, Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM budgets')
            return {row[0]: {
                'monthly_limit': row[1],
                'current_spending': row[2],
                'reset_date': row[3]
            } for row in cursor.fetchall()}

    def get_persons(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM persons')
            return [dict(row) for row in cursor.fetchall()]

    def get_spending_summary(self) -> Dict[str, float]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT main_category, SUM(amount)
                FROM transactions
                WHERE type = 'expense'
                AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                GROUP BY main_category
            ''')
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_financial_overview(self, days_back: int = 30) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, p.name 
                FROM transactions t
                LEFT JOIN persons p ON t.person_id = t.person_id
                WHERE date >= DATE('now', ?)
                ORDER BY date DESC
                LIMIT 5
            ''', (f'-{days_back} days',))
            transactions = [dict(row) for row in cursor.fetchall()]
            cursor.execute('''
                SELECT main_category, SUM(amount)
                FROM transactions
                WHERE type = 'expense'
                AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                GROUP BY main_category
            ''')
            summary = {row[0]: row[1] for row in cursor.fetchall()}
            return {'transactions': transactions, 'summary': summary}

if __name__ == "__main__":
    db = DatabaseManager()
    
    test_transactions = [
        {
            'date': '2025-04-10',
            'description': 'Grocery shopping',
            'amount': 1500.0,
            'main_category': 'Food',
            'sub_category': 'groceries',
            'type': 'expense',
            'person': 'Alice'
        },
        {
            'date': '2025-04-11',
            'description': 'Salary received',
            'amount': 50000.0,
            'main_category': 'Employment',
            'sub_category': 'salary',
            'type': 'income',
            'person': 'Bob'
        }
    ]
    print("Adding transactions...")
    db.bulk_add_transactions(test_transactions)
    print("Transactions added successfully")
    
    print("\nAll Transactions in Database:")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, description, amount FROM transactions ORDER BY date DESC")
        for row in cursor.fetchall():
            print(f"{row[0]} - {row[1]}: ₹{row[2]}")
    
    print("\nRecent Transactions (last 30 days):")
    for txn in db.get_transactions():
        print(f"{txn['date']} - {txn['description']}: ₹{txn['amount']}")
    
    print("\nCurrent Budgets:")
    budgets = db.get_budgets()
    for cat, data in budgets.items():
        print(f"{cat}: ₹{data['current_spending']}/₹{data['monthly_limit']}")
    
    print("\nMonthly Spending Summary:")
    summary = db.get_spending_summary()
    for cat, amount in summary.items():
        print(f"{cat}: ₹{amount}")
