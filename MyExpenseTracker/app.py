from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
from transformers import pipeline
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
DATABASE = 'database.db'

# Pre-load the model
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# These are your "Master Categories" to keep things organized
DEFAULT_CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Health", "Education", "Utilities", "Groceries", "Gym"]

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS expenses 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         item TEXT, amount REAL, category TEXT, date TEXT)''')

def get_clean_categories():
    """Returns a unique, title-cased list of categories from the DB + Defaults"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # Get unique categories from DB
            cursor.execute("SELECT DISTINCT category FROM expenses")
            db_cats = [row[0].strip().title() for row in cursor.fetchall() if row[0]]
            
            # Combine with defaults and remove duplicates
            combined = list(set(db_cats + DEFAULT_CATEGORIES))
            return sorted(combined)
    except:
        return DEFAULT_CATEGORIES

def predict_category(item_name):
    try:
        # We tell the AI to ONLY choose from our existing clean list
        candidate_labels = get_clean_categories()
        
        # ML Prediction
        result = classifier(item_name, candidate_labels, multi_class=False)
        
        if result and result['labels']:
            return {
                "category": result['labels'][0], 
                "confidence": float(result['scores'][0])
            }
    except Exception as e:
        print(f"ML Error: {e}")
    return None

@app.route('/')
def index():
    cat_filter = request.args.get('category', 'All')
    sort_by = request.args.get('sort', 'newest')

    query = "SELECT * FROM expenses"
    params = []

    if cat_filter != 'All':
        query += " WHERE category = ?"
        params.append(cat_filter)

    if sort_by == 'high': query += " ORDER BY amount DESC"
    elif sort_by == 'low': query += " ORDER BY amount ASC"
    else: query += " ORDER BY date DESC"

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Use the helper to get the filter list
        categories = get_clean_categories()
        total = sum(row['amount'] for row in rows)

    return render_template('index.html', expenses=rows, total=total, categories=categories)

@app.route('/add', methods=['POST'])
def add():
    item = request.form['item'].strip()
    amount = float(request.form['amount'])
    # Force Category to Title Case to prevent "food" vs "Food"
    category = request.form['category'].strip().title()
    date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
    
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('INSERT INTO expenses (item, amount, category, date) VALUES (?, ?, ?, ?)', 
                     (item, amount, category, date))
    
    return redirect(url_for('index'))

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    item_name = data.get('item', '').strip()
    
    if not item_name or len(item_name) < 3:
        return jsonify({"category": None})
    
    result = predict_category(item_name)
    
    # Check if AI is confident enough
    if result and result['confidence'] > 0.35:
        return jsonify(result)
    
    return jsonify({"category": None})

@app.route('/delete/<int:id>')
def delete(id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)