from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
from transformers import pipeline
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
DATABASE = 'database.db'

# Initialize the zero-shot classifier (works immediately without training)
# This is a pre-trained model that can classify text into any categories
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS expenses 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         item TEXT, amount REAL, category TEXT, date TEXT)''')

def get_common_categories():
    """Get categories from recent expenses or default ones"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM expenses ORDER BY category LIMIT 15")
            categories = [row[0] for row in cursor.fetchall()]
        
        if len(categories) >= 5:
            return categories
    except:
        pass
    
    # Default expense categories for zero-shot classification
    return ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Health", "Education", "Utilities", "Groceries", "Gym"]

def predict_category(item_name):
    """Use zero-shot classification to predict category immediately"""
    try:
        categories = get_common_categories()
        
        # Use the pre-trained model to classify
        result = classifier(item_name, categories, multi_class=False)
        
        if result and result['labels']:
            top_category = result['labels'][0]
            confidence = result['scores'][0]
            
            return {"category": top_category, "confidence": float(confidence)}
    except Exception as e:
        print(f"Prediction Error: {e}")
    
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

    # Sorting Logic
    if sort_by == 'high':
        query += " ORDER BY amount DESC"
    elif sort_by == 'low':
        query += " ORDER BY amount ASC"
    else:
        query += " ORDER BY date DESC"

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT category FROM expenses")
        categories = [r['category'] for r in cursor.fetchall()]
        total = sum(row['amount'] for row in rows)

    return render_template('index.html', expenses=rows, total=total, categories=categories)

@app.route('/add', methods=['POST'])
def add():
    item = request.form['item']
    amount = float(request.form['amount'])
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
    
    if not item_name:
        return jsonify({"category": None})
    
    result = predict_category(item_name)
    # Zero-shot classifier works even with lower confidence
    if result and result['confidence'] > 0.3:
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