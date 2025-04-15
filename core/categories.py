"""
categories.py - Optimized category definitions for financial transactions

Features:
- Predefined expenditure and income categories with Indian context
- Fast keyword-based and fuzzy category suggestion
- Efficient subcategory-to-main-category lookup
- Validation and hierarchy utilities
- Integration-ready for NLP and manual inputs
"""

from fuzzywuzzy import process
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Core Category Definitions with Indian context
EXPENDITURE_CATEGORIES = {
    "Housing": ["rent", "mortgage", "property tax", "home insurance", "maintenance", "repairs", "utilities", "maid"],
    "Transportation": ["car payment", "fuel", "public transit", "maintenance", "insurance", "parking", "tolls", "auto rickshaw", "metro"],
    "Food": ["groceries", "dining out", "takeout", "coffee", "alcohol", "snacks", "panipuris", "sabji", "dhaba", "sweets", "kirana"],
    "Healthcare": ["insurance", "doctor", "dentist", "pharmacy", "hospital", "optical", "fitness", "ayurveda"],
    "Personal": ["clothing", "entertainment", "hobbies", "subscriptions", "gifts", "beauty", "electronics", "movie ticket", "jewelry"],
    "Debt": ["credit card", "student loan", "personal loan", "payday loan", "debt consolidation", "EMI"],
    "Savings": ["emergency fund", "retirement", "investments", "education fund", "vacation fund", "FD", "RD"],
    "Education": ["tuition", "books", "supplies", "courses", "software", "conferences", "coaching"],
    "Charity": ["donations", "gifts", "religious", "political", "community support", "temple", "pooja"],
    "Miscellaneous": ["pet care", "child care", "legal fees", "taxes", "fines", "unexpected", "festivals"]
}

INCOME_CATEGORIES = {
    "Employment": ["salary", "wages", "bonus", "commission", "tips", "overtime", "stipend"],
    "Business": ["self-employment", "freelance", "consulting", "sales", "royalties", "shop income"],
    "Investments": ["dividends", "interest", "capital gains", "rental income", "retirement", "MF returns"],
    "Government": ["social security", "unemployment", "disability", "stimulus", "tax refund", "pension"],
    "Other": ["gifts", "inheritance", "lottery", "alimony", "crowdfunding", "reimbursement", "wedding gift"]
}

ALL_CATEGORIES = {**EXPENDITURE_CATEGORIES, **INCOME_CATEGORIES}

KEYWORD_MAPPINGS = {
    "panipuris": ("Food", "panipuris"),
    "movie": ("Personal", "movie ticket"),
    "ticket": ("Personal", "movie ticket"),
    "sabji": ("Food", "sabji"),
    "groceries": ("Food", "groceries"),
    "clothes": ("Personal", "clothing"),
    "clothing": ("Personal", "clothing"),
    "salary": ("Employment", "salary"),
    "kirana": ("Food", "kirana"),
    "dhaba": ("Food", "dhaba"),
    "sweets": ("Food", "sweets"),
    "auto": ("Transportation", "auto rickshaw"),
    "rickshaw": ("Transportation", "auto rickshaw"),
    "emi": ("Debt", "EMI"),
    "gift": ("Other", "gifts")
}

class CategoryManager:
    def __init__(self):
        self.sub_to_main = {}
        for main_cat, sub_cats in ALL_CATEGORIES.items():
            for sub_cat in sub_cats:
                self.sub_to_main[sub_cat.lower()] = main_cat

    def get_main_category(self, sub_category: str) -> Optional[str]:
        return self.sub_to_main.get(sub_category.lower())

category_mgr = CategoryManager()

def validate_category(category_type: str, main_category: str, sub_category: str) -> bool:
    category_map = INCOME_CATEGORIES if category_type == 'income' else EXPENDITURE_CATEGORIES
    main_category = main_category.lower()
    sub_category = sub_category.lower()
    valid_main = any(main_cat.lower() == main_category for main_cat in category_map.keys())
    valid_sub = any(sub_cat.lower() == sub_category for sub_cats in category_map.values() for sub_cat in sub_cats)
    logger.debug(f"Validating {category_type}: {main_category}/{sub_category} -> Main: {valid_main}, Sub: {valid_sub}")
    return valid_main and valid_sub

def get_main_category(sub_category: str) -> Optional[str]:
    return category_mgr.get_main_category(sub_category)

def get_all_subcategories(category_type: str = None) -> List[str]:
    if category_type == 'income':
        return [sc for subs in INCOME_CATEGORIES.values() for sc in subs]
    elif category_type == 'expense':
        return [sc for subs in EXPENDITURE_CATEGORIES.values() for sc in subs]
    return [sc for subs in ALL_CATEGORIES.values() for sc in subs]

def suggest_category(description: str, transaction_type: str = 'expense') -> Tuple[Optional[str], Optional[str]]:
    description = description.lower()
    logger.debug(f"Suggesting category for: '{description}', type: {transaction_type}")
    
    # Step 1: Direct keyword match
    for keyword, (main_cat, sub_cat) in KEYWORD_MAPPINGS.items():
        if keyword in description:
            logger.debug(f"Keyword match: {keyword} -> ({main_cat}, {sub_cat})")
            if validate_category(transaction_type, main_cat, sub_cat):
                return (main_cat, sub_cat)
    
    # Step 2: Fuzzy match
    all_subs = get_all_subcategories(transaction_type)
    logger.debug(f"Subcategories for {transaction_type}: {all_subs}")
    best_match, score = process.extractOne(description, all_subs) if all_subs else (None, 0)
    logger.debug(f"Fuzzy match: {best_match}, score: {score}")
    if best_match and score >= 80:
        main_cat = get_main_category(best_match)
        if main_cat and validate_category(transaction_type, main_cat, best_match):
            return (main_cat, best_match)

    # Step 3: Word-level fuzzy match
    words = description.split()
    for word in words:
        match, score = process.extractOne(word, all_subs) if all_subs else (None, 0)
        logger.debug(f"Word-level match: {word} -> {match}, score: {score}")
        if match and score >= 85:
            main_cat = get_main_category(match)
            if main_cat and validate_category(transaction_type, main_cat, match):
                return (main_cat, match)
    
    # Default fallback
    default = ("Miscellaneous" if transaction_type == 'expense' else "Other", 
               "unexpected" if transaction_type == 'expense' else "reimbursement")
    logger.debug(f"Fallback to default: {default}")
    return default

def get_category_hierarchy(category_type: str = None) -> Dict[str, List[str]]:
    if category_type == 'income':
        return INCOME_CATEGORIES
    elif category_type == 'expense':
        return EXPENDITURE_CATEGORIES
    return ALL_CATEGORIES

if __name__ == "__main__":
    print("Validation Tests:")
    print(validate_category('expense', 'Food', 'panipuris'))
    print(validate_category('income', 'Employment', 'salary'))
    
    print("\nSuggestion Tests:")
    print(suggest_category("panipuris"))
    print(suggest_category("movie ticket"))
    print(suggest_category("sabji"))
    print(suggest_category("random text"))
    print(suggest_category("salary received", 'income'))
