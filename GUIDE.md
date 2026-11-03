# Sales Tracker: how the whole flow works

```
 index.html (JavaScript)  ──HTTP + JSON──▶  main.py (FastAPI, Python)  ──SQL──▶  sales.db (SQLite)
                          ◀──── JSON ─────                             ◀── rows ──
```

| Layer | File | What it does |
|---|---|---|
| Frontend | `index.html` | Form to add a sale (POST) + button to load all sales (GET) |
| Backend | `main.py` | Endpoints, data validation, SQL |
| Database | `sales.db` | Table `sales (id, product, city, amount)`, created on first run with 3 sample rows |

## Endpoints
| Method | URL | Result |
|---|---|---|
| GET | `/` | `{"message": "Sales Tracker is running"}` |
| GET | `/sales` | All sales, 200 |
| GET | `/sales/{sale_id}` | One sale, 200; 404 if it doesn't exist; 422 if the id isn't a number |
| POST | `/sales` | Add a sale, 201; 422 if a field is missing or the wrong type |

---

## Concepts, in the order the code uses them

### Backend (`main.py`)
| Line(s) | Concept | Meaning |
|---|---|---|
| `import sqlite3` | Database driver | Built into Python; talks to the `sales.db` file |
| `app = FastAPI()` | The app | The web application object |
| `app.add_middleware(CORSMiddleware, ...)` | **CORS** | The page and the API are on different origins, so the browser blocks reading responses unless the server sends `Access-Control-Allow-Origin`. This middleware adds it |
| `class Sale(BaseModel)` | **Pydantic model** | The shape a POST body must have: product (text), city (text), amount (number). Wrong/missing field → automatic **422** |
| `get_db()` | **Connection** | Opens `sales.db`; `row_factory = sqlite3.Row` lets rows be turned into dicts |
| `CREATE TABLE IF NOT EXISTS` | Table setup | Creates the table only the first time |
| `id INTEGER PRIMARY KEY AUTOINCREMENT` | **Primary key** | Unique id the database assigns: 1, 2, 3… |
| `COUNT(*)` + `executemany` | Seed data | Inserts 3 sample sales only if the table is empty |
| `conn.commit()` | **Commit** | Makes changes permanent on disk |
| `@app.get("/sales")` | **Route** | Connects `GET /sales` to the function below it |
| `sale_id: int` | **Path parameter + type hint** | FastAPI converts `"2"` → `2`; `"abc"` → 422 |
| `WHERE id = ?`, `(sale_id,)` | **Parameterised query** | Value sent separately from the SQL, preventing **SQL injection** |
| `fetchall()` / `fetchone()` | Read results | All rows / one row (or `None`) |
| `[dict(row) for row in rows]` | Convert | Rows → dicts → FastAPI sends them as JSON |
| `raise HTTPException(404)` | Error response | "Sale not found" |
| `status_code=201` | Created | Correct status for a POST that made something |
| `cursor.lastrowid` | New id | The id SQLite just gave the inserted row |
| `**sale.model_dump()` | Unpack | Turns the Sale into a dict and merges it with the id |

### Frontend (`index.html`)
| Code | Concept | Meaning |
|---|---|---|
| `<form id="saleForm">` with `required` | HTML form | Inputs for product, city, amount; browser won't submit empty ones |
| `addEventListener("submit", addSale)` | **Event listener** | Run `addSale` when the form is submitted |
| `event.preventDefault()` | Stop reload | A form normally reloads the page; JavaScript handles it instead |
| `document.getElementById(...).value` | **DOM** | Read what the user typed |
| `Number(...)` | Type conversion | Input values are text; amount must be a number |
| `async` / `await` | Asynchronous | Wait for the server without freezing the page |
| `fetch(url, {method: "POST", headers, body})` | **fetch** | Send an HTTP request from the browser |
| `"Content-Type": "application/json"` | Header | Tells FastAPI the body is JSON |
| `JSON.stringify(sale)` | Serialise | JS object → JSON text |
| `res.status === 201` | Status check | Success or error |
| `await res.json()` | Parse | JSON text → JS object |
| `createElement("li")`, `appendChild` | Change the page | Add one list item per sale |

---

## Dry run 1: click "Load sales" (GET)

| Step | Where | What happens | Values |
|---|---|---|---|
| 1 | JS | Button's `onclick` calls `loadSales()` | — |
| 2 | JS → network | `fetch("http://127.0.0.1:8000/sales")` sends `GET /sales` | — |
| 3 | Python | FastAPI matches `@app.get("/sales")`, runs `get_sales()` | — |
| 4 | Python → DB | `SELECT * FROM sales` | 3 rows |
| 5 | Python | `[dict(row) ...]` → JSON, status 200 | `[{"id":1,"product":"Pen","city":"Pune","amount":50.0}, ...]` |
| 6 | Browser | Different origin → checks CORS header `*` → allowed | — |
| 7 | JS | `sales = await res.json()` → array of 3 objects | — |
| 8 | JS | `list.innerHTML = ""` clears old items, loop adds `<li>` per sale | `Pen - Pune - Rs 50`, `Notebook - Mumbai - Rs 120`, `Bag - Bangalore - Rs 800` |

## Dry run 2: add "Laptop, Hyderabad, 45000" (POST → stored in the DB)

| Step | Where | What happens | Values |
|---|---|---|---|
| 1 | JS | Click **Add sale** → `submit` event → `addSale(event)` | — |
| 2 | JS | `preventDefault()` stops the reload | — |
| 3 | JS | Reads the inputs, `Number("45000")` → 45000 | `sale = {product:"Laptop", city:"Hyderabad", amount:45000}` |
| 4 | JS | `JSON.stringify(sale)` | `'{"product":"Laptop","city":"Hyderabad","amount":45000}'` |
| 5 | JS → network | `fetch` sends `POST /sales` with header `Content-Type: application/json` | — |
| 6 | Browser | POST with a JSON header from another origin → **preflight** `OPTIONS` request first; CORS middleware answers "allowed" | then the real POST goes |
| 7 | Python | FastAPI matches `@app.post("/sales")`, builds `Sale` from the JSON and validates it | `sale.product="Laptop"`, `sale.amount=45000.0` ✔ |
| 8 | Python → DB | `INSERT INTO sales (product, city, amount) VALUES (?, ?, ?)` with `("Laptop","Hyderabad",45000.0)` | — |
| 9 | DB | AUTOINCREMENT gives the next id | `id = 4` |
| 10 | Python | `conn.commit()` saves to disk; `new_id = cursor.lastrowid` | `new_id = 4` |
| 11 | Python | Returns status **201** | `{"id":4,"product":"Laptop","city":"Hyderabad","amount":45000.0}` |
| 12 | JS | `res.status === 201` → `saved = await res.json()` | — |
| 13 | JS | Shows message, resets the form, calls `loadSales()` | "Saved Laptop with id 4"; list now has 4 sales |

**Proof it's stored:** stop the server (Ctrl+C), start it again, click Load sales → Laptop is still there, because it's in `sales.db` on disk.

## Dry run 3: GET /sales/2 and /sales/99

| Request | Steps | Response |
|---|---|---|
| `GET /sales/2` | `"2"` → int 2 → `SELECT * FROM sales WHERE id = ?` with `(2,)` → one row | 200 `{"id":2,"product":"Notebook","city":"Mumbai","amount":120.0}` |
| `GET /sales/99` | `fetchone()` returns `None` → `raise HTTPException(404)` | 404 `{"detail":"Sale not found"}` |
| `GET /sales/abc` | `"abc"` can't become int → FastAPI rejects before the function runs | 422 |

## Dry run 4: bad POST

| Body | What happens | Response |
|---|---|---|
| `{"product":"Pen","city":"Pune"}` (no amount) | Pydantic: `amount` is required | 422, `"Field required"` |
| `{"product":"Pen","city":"Pune","amount":"abc"}` | Pydantic: can't turn "abc" into a float | 422 |

---

## Say it in 30 seconds

> "The frontend is HTML and JavaScript. When I submit the form, JavaScript stops the page reload, builds the sale as an object, converts it to JSON and sends a POST with fetch. FastAPI validates it with a Pydantic model, so bad data gets a 422, then inserts it into SQLite with a parameterised query, commits, and returns 201 with the new id. The page then calls GET /sales and redraws the list. CORS middleware lets the browser accept responses from the API on a different origin."

## SQLite → MySQL (if they ask)

Only the database part changes:
- `import pymysql` and `pymysql.connect(host="localhost", user="root", password=..., database="sales_db", cursorclass=pymysql.cursors.DictCursor)` instead of `sqlite3.connect("sales.db")`
- `?` placeholders become `%s`
- `INTEGER PRIMARY KEY AUTOINCREMENT` becomes `INT AUTO_INCREMENT PRIMARY KEY`
- MySQL is a separate server (many users at once, logins); SQLite is a single file, good for small apps.

The endpoints and the JavaScript stay the same.
