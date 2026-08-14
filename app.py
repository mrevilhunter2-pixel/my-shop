import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, 'templates'),
    static_folder=os.path.join(base_dir, 'static')
)

app.secret_key = 'fashion_mart_secret_key_999'
ADMIN_USERNAME = "Rohankumarmeena"
ADMIN_PASSWORD = "Ganesh1234me@711451"

def init_db():
    db_path = os.path.join(base_dir, 'fashion_mart.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Products Table (Multiple images support ke liye JSON ya text)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            discount_price REAL NOT NULL,
            images_json TEXT NOT NULL,
            description TEXT
        )
    ''')

    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total_amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Order Placed'
        )
    ''')

    # Sample Clothing Products agar table khali hai
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            (
                "Men Stylish Casual Shirt", 
                "Men", 
                1499, 
                799, 
                json.dumps([
                    "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500",
                    "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500"
                ]),
                "100% Cotton premium quality casual shirt for men."
            ),
            (
                "Women Ethnic Kurti Set", 
                "Women", 
                2499, 
                999, 
                json.dumps([
                    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500",
                    "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=500"
                ]),
                "Beautiful designer kurti set with comfortable fabric."
            )
        ]
        cursor.executemany('''
            INSERT INTO products (name, category, price, discount_price, images_json, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_products)
        conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/orders-page')
def orders_page():
    return render_template('orders.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return render_template('index.html')
    return render_template('admin.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('is_admin', None)
    return jsonify({"status": "success"})

@app.route('/api/check-admin', methods=['GET'])
def check_admin():
    return jsonify({"is_admin": session.get('is_admin', False)})

@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category', 'All')
    search = request.args.get('search', '')
    
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    query = 'SELECT id, name, category, price, discount_price, images_json, description FROM products WHERE 1=1'
    params = []
    if category != 'All':
        query += ' AND category = ?'
        params.append(category)
    if search:
        query += ' AND name LIKE ?'
        params.append(f'%{search}%')
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    products_list = []
    for row in rows:
        products_list.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "price": row[3],
            "discountPrice": row[4],
            "images": json.loads(row[5]),
            "description": row[6]
        })
    return jsonify(products_list)

@app.route('/api/add-product', methods=['POST'])
def add_product():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, category, price, discount_price, images_json, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['name'], 
        data['category'], 
        float(data['price']), 
        float(data['discountPrice']), 
        json.dumps(data['images']), 
        data['description']
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(base_dir, 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/add-product', methods=['POST'])
def add_product():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    
    name = request.form.get('name')
    category = request.form.get('category')
    price = float(request.form.get('price'))
    discount_price = float(request.form.get('discountPrice'))
    description = request.form.get('description', '')
    
    images = []
    for key in ['img1', 'img2']:
        if key in request.files:
            file = request.files[key]
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                images.append(f"/static/uploads/{filename}")
    
    if not images:
        images.append("https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500")

    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, category, price, discount_price, images_json, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, category, price, discount_price, json.dumps(images), description))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})
    

@app.route('/api/customer/cancel-order/<int:order_id>', methods=['PUT'])
def cancel_order(order_id):
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = ? AND status = 'Order Placed'", (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer_name, customer_phone, customer_address, items_json, total_amount, order_date, status FROM orders ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    orders_list = []
    for row in rows:
        orders_list.append({
            "id": row[0],
            "name": row[1],
            "phone": row[2],
            "address": row[3],
            "items": json.loads(row[4]),
            "total": row[5],
            "date": row[6],
            "status": row[7]
        })
    return jsonify(orders_list)

@app.route('/api/admin/update-status', methods=['PUT'])
def update_status():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (data['status'], int(data['orderId'])))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

@app.route('/api/admin/delete-order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})
@app.route('/api/admin/delete-product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    conn = sqlite3.connect(os.path.join(base_dir, 'fashion_mart.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
