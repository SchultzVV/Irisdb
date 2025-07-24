import sqlite3
import pandas as pd
import seaborn as sns

def create_mock_iris_db(db_path=":memory:") -> sqlite3.Connection:
    df = sns.load_dataset("iris")
    conn = sqlite3.connect(db_path)
    df.to_sql("iris", conn, index=False, if_exists="replace")
    return conn
