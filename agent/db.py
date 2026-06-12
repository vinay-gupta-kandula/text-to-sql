import sqlite3

def get_schema() -> str:
    """Returns the database schema as a string so the AI knows what tables exist."""
    return """
    Table: indicators
    Columns: country (TEXT), date (TEXT), gdp_current_usd (REAL), gdp_per_capita_usd (REAL), gdp_growth_pct (REAL), population (REAL), health_expenditure_pct_gdp (REAL), life_expectancy (REAL), education_expenditure_pct_gdp (REAL), co2_emissions_per_capita (REAL), unemployment_pct (REAL), gini_index (REAL)
    
    Table: country_metadata
    Columns: country_code (TEXT), country_name (TEXT), region (TEXT), income_group (TEXT), lending_type (TEXT)
    """

def execute_sql(query: str):
    """Executes a SQL query against our local database and returns results or an error."""
    conn = sqlite3.connect("worldbank.db")
    cur = conn.cursor()
    try:
        cur.execute(query)
        results = cur.fetchall()
        return results, None  # Return results, No error
    except Exception as e:
        return None, str(e)   # Return No results, Yes error
    finally:
        conn.close()