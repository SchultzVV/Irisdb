import pandas as pd
from tests.mock_db import create_mock_iris_db

def test_iris_table_exists():
    conn = create_mock_iris_db()
    df = pd.read_sql_query("SELECT * FROM iris", conn)
    assert not df.empty
    assert set(["sepal_length", "sepal_width", "species"]).issubset(df.columns)
