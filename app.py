# app.py
from flask import Flask, request, jsonify, render_template
from core.database import DatabaseManager
from core.nlp_parser import NLPParser
from core.categories import get_category_hierarchy

app = Flask(__name__)
db = DatabaseManager()
nlp = NLPParser()

@app.route('/')
def index():
    categories = get_category_hierarchy()  # Returns full hierarchy: {"Food": ["panipuris", ...], ...}
    print(f"Rendering with categories: {categories}")  # Debug print
    return render_template('index.html', categories=categories)

@app.route('/transactions', methods=['POST'])
def add_transaction():
    if request.content_type == 'application/json':
        data = request.json
        db.add_transaction(data)
        return jsonify({'message': 'Transaction added'}), 201
    elif request.content_type == 'text/plain':
        text = request.data.decode('utf-8')
        result = nlp.process(text)
        return jsonify(result), 200 if result['status'] == 'success' else 400

@app.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = db.get_transactions(days_back=365)
    return jsonify(transactions)

if __name__ == '__main__':
    app.run(debug=True)
