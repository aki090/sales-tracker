import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Sale(BaseModel):
    product: str
    city: str
    amount: float

# ---------- database setup ----------
def get_db():
    conn = sqlite3.connect("sales.db")
    conn.row_factory = sqlite3.Row
    return conn

def setup():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            city TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO sales (product, city, amount) VALUES (?, ?, ?)",
            [("Pen", "Pune", 50), ("Notebook", "Mumbai", 120), ("Bag", "Bangalore", 800)],
        )
    conn.commit()
    conn.close()

setup()

# ---------- endpoints ----------
@app.get("/")
def home():
    return {"message": "Sales Tracker is running"}

@app.get("/sales")
def get_sales():
    conn = get_db()
    rows = conn.execute("SELECT * FROM sales").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/sales/{sale_id}")
def get_sale(sale_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    return dict(row)

@app.post("/sales", status_code=201)
def create_sale(sale: Sale):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO sales (product, city, amount) VALUES (?, ?, ?)",
        (sale.product, sale.city, sale.amount),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, **sale.model_dump()}