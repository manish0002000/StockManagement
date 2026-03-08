# Stock Management System

A Python + SQLite stock management system with:

- Product photo upload
- Quantity tracking
- Price management
- Low stock alerts
- Dashboard with key inventory metrics

## Tech stack

- Python
- Flask
- SQLite

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

## Main features

1. **Add products** with name, quantity, price, low-stock threshold, and optional photo.
2. **Track inventory quantities** and update stock levels from the dashboard.
3. **Low stock alerts** automatically flag products when `quantity <= threshold`.
4. **Dashboard metrics** include total products, total units, inventory value, and low-stock count.

Uploaded photos are stored in `uploads/`, and data is persisted in `inventory.db`.
