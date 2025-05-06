import pandas as pd
import pathlib
import datetime as dt
import sys

RAW = "data/master/product_master_raw.csv"
OUT = "data/master/product_master_clean.csv"

# The original is ISO-8859-1 encoded and has weird spaces
df = pd.read_csv(RAW, encoding="latin1")

# Strip whitespace from column names
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Keep & rename the essentials
df = df.rename(columns={
    "product_id": "sku",
    "product_name": "name",
    "current_price": "current_price_eur",
    "unit_cost": "unit_cost_eur"
})

# Drop rows without a product_id
df = df.dropna(subset=["sku"])

# Remove currency symbols, convert to float
for col in ["current_price_eur", "unit_cost_eur"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(r"[^\d\.]", "", regex=True)
        .astype(float)
    )

# Add timestamp for traceability
df["ingested_at"] = dt.datetime.utcnow()

# Save the cleaned version
pathlib.Path(OUT).parent.mkdir(exist_ok=True, parents=True)
df.to_csv(OUT, index=False)

print("✅ Cleaned product master written to", OUT) 