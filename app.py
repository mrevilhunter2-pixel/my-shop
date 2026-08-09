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

app.secret_key = 'super_secret_admin_key_123'
ADMIN_USERNAME = "Rohankumarmeena"
ADMIN_PASSWORD = "Ganesh1234me@711451"

def init_db():
    db_path = os.path.join(base_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Others',
            original_price REAL NOT NULL,
            discount_percent REAL NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')
    
    # Category Column Check
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'category' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT NOT NULL DEFAULT 'Others'")
        conn.commit()

    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            payment_mode TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total_amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Placed'
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("Wireless Headphones", "Audio", 2999, 40, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"),
            ("Smart Watch Ultra", "Wearables", 4999, 50, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"),
            ("RGB Gaming Mouse", "Gaming", 1500, 20, "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=400")
        ]
        cursor.executemany('''
            INSERT INTO products (name, category, original_price, discount_percent, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_products)
        conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/success')
def success():
    return render_template('success.html')

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
    
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    query = 'SELECT id, name, category, original_price, discount_percent, image_url FROM products WHERE 1=1'
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
        orig_price = row[3]
        disc_pct = row[4]
        final_price = round(orig_price - ((orig_price * disc_pct) / 100))
        products_list.append({
            "id": row[0], "name": row[1], "category": row[2],
            "originalPrice": orig_price, "discountPercent": disc_pct,
            "finalPrice": final_price, "image": row[5]
        })
    return jsonify(products_list)

@app.route('/api/add-product', methods=['POST'])
def add_product():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, category, original_price, discount_percent, image_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], data.get('category', 'Others'), float(data['originalPrice']), float(data['discountPercent']), data['image']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/update-product', methods=['PUT'])
def update_product():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE products 
        SET name = ?, category = ?, original_price = ?, discount_percent = ?, image_url = ?
        WHERE id = ?
    ''', (data['name'], data.get('category', 'Others'), float(data['originalPrice']), float(data['discountPercent']), data['image'], int(data['id'])))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

@app.route('/api/delete-product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (customer_name, customer_phone, customer_address, payment_mode, items_json, total_amount, order_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['phone'], data['address'], data['payMode'], json.dumps(data['items']), float(data['total']), now))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer_name, customer_phone, customer_address, payment_mode, items_json, total_amount, order_date, status FROM orders ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    orders_list = []
    for row in rows:
        orders_list.append({
            "id": row[0], "name": row[1], "phone": row[2], "address": row[3],
            "payMode": row[4], "items": json.loads(row[5]), "total": row[6],
            "date": row[7], "status": row[8]
        })
    return jsonify(orders_list)

@app.route('/api/admin/update-order-status', methods=['PUT'])
def update_order_status():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (data['status'], int(data['orderId'])))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})
    
@app.route('/api/admin/delete-order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/customer/orders', methods=['GET'])
def get_customer_orders():
    phone = request.args.get('phone', '')
    if not phone:
        return jsonify([])
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer_name, payment_mode, items_json, total_amount, order_date, status FROM orders WHERE customer_phone = ? ORDER BY id DESC', (phone,))
    rows = cursor.fetchall()
    conn.close()
    orders_list = []
    for row in rows:
        orders_list.append({
            "id": row[0], "name": row[1], "payMode": row[2],
            "items": json.loads(row[3]), "total": row[4], "date": row[5], "status": row[6]
        })
    return jsonify(orders_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
