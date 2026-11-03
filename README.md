# Sales Tracker

A small practice project: a REST API built with FastAPI and SQLite, plus a web page that loads the data with JavaScript `fetch()`.

## Endpoints

| Method | URL | What it does |
|---|---|---|
| GET | `/sales` | List all sales |
| GET | `/sales/{id}` | One sale (404 if not found) |
| POST | `/sales` | Add a sale (returns 201) |

Example POST body:

```json
{ "product": "Pen", "city": "Pune", "amount": 50 }
```

## Run it

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

- API docs (try every endpoint): http://127.0.0.1:8000/docs
- Web page: open `index.html` in the browser and click **Load sales**

The database file `sales.db` is created automatically on first run, with 3 sample sales.
