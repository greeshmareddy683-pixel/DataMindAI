import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("ecommerce.db")
c = conn.cursor()

c.executescript("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY, name TEXT, email TEXT, city TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, stock INTEGER);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER,
    quantity INTEGER, total REAL, status TEXT, order_date TEXT);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY, product_id INTEGER, restock_date TEXT, quantity_added INTEGER);
""")

cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"]
for i in range(1, 51):
    c.execute("INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?)",
        (i, f"Customer {i}", f"user{i}@email.com", random.choice(cities),
         (datetime.now() - timedelta(days=random.randint(10,500))).strftime("%Y-%m-%d")))

categories = {
    "Electronics": ["Laptop", "Phone", "Tablet", "Headphones", "Smartwatch"],
    "Clothing": ["T-Shirt", "Jeans", "Kurta", "Saree", "Jacket"],
    "Books": ["Fiction Novel", "Data Science Book", "History Book", "Python Guide", "Self Help"],
    "Home": ["Mixer", "Cooker", "Fan", "LED Bulb", "Water Bottle"]
}
pid = 1
for cat, items in categories.items():
    for item in items:
        c.execute("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)",
            (pid, item, cat, round(random.uniform(100, 50000), 2), random.randint(5, 200)))
        pid += 1

statuses = ["delivered", "shipped", "pending", "cancelled"]
for i in range(1, 201):
    pid = random.randint(1, 20)
    qty = random.randint(1, 5)
    c.execute("SELECT price FROM products WHERE id=?", (pid,))
    price = c.fetchone()[0]
    date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
    c.execute("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?)",
        (i, random.randint(1,50), pid, qty, round(price*qty,2), random.choice(statuses), date))

for i in range(1, 41):
    c.execute("INSERT OR IGNORE INTO inventory VALUES (?,?,?,?)",
        (i, random.randint(1,20),
         (datetime.now() - timedelta(days=random.randint(1,100))).strftime("%Y-%m-%d"),
         random.randint(10, 100)))

conn.commit()
conn.close()
print("✅ Database ready!")