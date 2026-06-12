import pandas as pd
import sqlite3
import requests
import time

print("Fetching indicator data directly from the World Bank API... (This will take a minute)")

indicators = {
    "NY.GDP.MKTP.CD":       "gdp_current_usd",
    "NY.GDP.PCAP.CD":       "gdp_per_capita_usd",
    "NY.GDP.MKTP.KD.ZG":    "gdp_growth_pct",
    "SP.POP.TOTL":          "population",
    "SH.XPD.CHEX.GD.ZS":    "health_expenditure_pct_gdp",
    "SP.DYN.LE00.IN":       "life_expectancy",
    "SE.XPD.TOTL.GD.ZS":    "education_expenditure_pct_gdp",
    "EN.ATM.CO2E.PC":       "co2_emissions_per_capita",
    "SL.UEM.TOTL.ZS":       "unemployment_pct",
    "SI.POV.GINI":          "gini_index",
}

all_data = []

# 1. Fetch Indicators Safely
for ind_code, ind_name in indicators.items():
    print(f"Downloading {ind_name}...")
    url = f"https://api.worldbank.org/v2/country/all/indicator/{ind_code}?format=json&per_page=20000"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check if valid data was returned
        if len(data) == 2 and isinstance(data[1], list):
            for row in data[1]:
                if row['country']['value'] != 'Not classified':
                    all_data.append({
                        "country": row['country']['value'],
                        "date": row['date'],
                        "indicator": ind_name,
                        "value": row['value']
                    })
    except Exception as e:
        print(f"Error fetching {ind_name}: {e}")
        
    time.sleep(0.5) # Pause briefly to respect API limits

# Convert to DataFrame and Pivot to get indicators as columns
print("Formatting data...")
df_raw = pd.DataFrame(all_data)
df = df_raw.pivot_table(index=['country', 'date'], columns='indicator', values='value').reset_index()

# Save to SQLite
print("Saving to database...")
conn = sqlite3.connect("worldbank.db")
df.to_sql("indicators", conn, if_exists="replace", index=False)
print(f"✅ Loaded {len(df):,} rows into worldbank.db (indicators table)")

# 2. Fetch Country Metadata
print("Fetching country metadata...")
meta_url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
meta_response = requests.get(meta_url).json()
countries = meta_response[1]

meta = [
    {
        "country_code":  c["id"],
        "country_name":  c["name"],
        "region":        c["region"]["value"],
        "income_group":  c["incomeLevel"]["value"],
        "lending_type":  c["lendingType"]["value"],
    }
    for c in countries if c["region"]["id"] != "NA"
]

meta_df = pd.DataFrame(meta)
meta_df.to_sql("country_metadata", conn, if_exists="replace", index=False)
print(f"✅ Loaded {len(meta_df)} countries into country_metadata table")

conn.close()
print("Database setup complete!")