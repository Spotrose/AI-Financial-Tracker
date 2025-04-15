# AI Financial Tracker 🧠💰

**An intelligent and personalized financial management web application built with Flask and Python, tailored for Indian users.**

---

## 📌 Project Overview


**AI Financial Tracker** is a Flask-based web application that helps users manage their finances through:
- Natural language transaction input
- Automated expense categorization
- Transaction tracking and analysis
- SQLite-based data persistence

---

It is a personalized financial assistant built using Python and Flask. It lets users:
- Input transactions manually or using **natural language**
- Automatically **categorize** expenses and income using fuzzy keyword matching
- Track and analyze **budgets, debts, savings**, and **goals**
- Generate **data-driven insights** using rule-based and statistical models



---
This repository includes the foundational logic for transaction categorization, which plays a central role in organizing user data for budgeting, analysis, and intelligent recommendations.

---

## 🛠️ Core Features

### 1. Natural Language Processing
- Process text inputs like "Paid ₹1500 for groceries yesterday"
- Extract transaction details (amount, category, date)
- Support for Indian context and terminology

### 2. Transaction Management
- Add and track expenses/income
- Automatic categorization
- Transaction history viewing

### 3. Database Management
- SQLite-based storage
- CRUD operations for transactions
- Efficient data retrieval and management

### 4. Web Interface
- Clean, responsive design
- Real-time transaction processing
- Transaction history display

### Financial Intelligence
---
- 📈 Budget forecasting with confidence intervals
- 💼 Investment portfolio recommendations
- 🎯 Savings goal probability calculator
- 🏦 Debt payoff optimization (Avalanche/Snowball methods)
- 🚨 Emergency fund advisor

## 🔧 Technical Stack

- **Backend**: Python/Flask
- **Database**: SQLite
- **Frontend**: HTML/Templates
- **Testing**: Python unittest


### Project Dependencies
- Flask
- SQLite3
- Python 3.x


## 📂 Folder Structure (Planned)

```
AI_Financial_Tracker/
├── app.py # Flask application (33 lines)
├── main.py # Main application logic (206 lines)
├── financial_tracker.db # SQLite database
├── config.ini # Configuration settings
│
├── core/
│ ├── models.py # Financial models (304 lines)
│ ├── database.py # Database operations (355 lines)
│ ├── categories.py # Category management (146 lines)
│ ├── nlp_parser.py # NLP processing (168 lines)
│ └── init.py
│
├── templates/
│ └── index.html # Web interface (92 lines)
│
└── tests/
├── test_parser.py # NLP tests (140 lines)
├── test_models.py # Model tests (183 lines)
└── init.py

```



## Key Modules 🔍

### `nlp_parser.py`
- Parses natural language transactions
- Extracts: amount, description, category, person, date
- Handles complex inputs with multiple transactions

### `categories.py`
- 50+ Indian-specific categories
- Fuzzy matching for descriptions
- Hierarchical category structure

### `models.py`
- Budget forecasting with moving averages
- Investment strategy generator
- Debt payoff optimizer
- Emergency fund calculator

## Installation 🛠️

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AI_Financial_Tracker.git
   cd AI_Financial_Tracker
   ```

2. Set up virtual environment:
   ```
   python -m venv myenv
   source myenv/bin/activate  # Linux/Mac
   myenv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```


### Web Interface
```
Access at `http://localhost:5000`
```



## 🧠 Sample Categories

### Expense Categories:
- **Food**: groceries, snacks, dhaba, kirana, sabji, panipuris, sweets
- **Transportation**: auto rickshaw, metro, fuel, car payment
- **Personal**: movie ticket, clothing, beauty
- **Healthcare**: doctor, pharmacy, ayurveda
- **Debt**: EMI, credit card
- **Education**: tuition, coaching
- **Miscellaneous**: festivals, legal fees, pet care

### Income Categories:
- **Employment**: salary, stipend, bonus
- **Business**: freelance, shop income
- **Investments**: mutual funds, dividends
- **Government**: pension, refund
- **Other**: gifts, reimbursements, wedding gift

---

## 🔮 Planned Smart Features (In Development)

- NLP parsing of free-text transaction inputs (e.g., "Bought samosas for ₹50")
- Statistical budget forecasting
- Personalized financial insights & advice
- Savings goal probability estimation
- Emergency fund recommendation engine
- Group spending & shared finance tracking

---

## 📦 Requirements

To install all dependencies:

```
pip install -r requirements.txt
```

Main Python packages used:
- `fuzzywuzzy` - for approximate string matching
- `Flask` - for web framework
- `sqlite3` - for local database (via `database.py`)
- `pandas`, `numpy`, `matplotlib` - for analysis and visualization (in backend)


## 👤 Author

**Anshuman Baghamare** – Final-year B.Tech (CSE - AI & DS) student passionate about AI-powered productivity tools and intelligent assistants.

---

## 💡 Future Enhancements

- UI for manual and voice inputs
- Auto-detect and parse SMS/email financial notifications
- Integration with UPI and banking APIs (mock or real)
- Multi-user support
- PDF export for tax or sharing

---

## 📜 License

This project is under open development by Anshu ji for academic and personal use. Licensing terms may be added post completion.

---

## 🙏 Acknowledgements

- Guide by **Prof. Uma Vishwakarma**
- `fuzzywuzzy` for smart matching
- Indian financial norms and real-world needs as inspiration
- OpenAI’s ChatGPT for co-piloting the logic and documentation

---

