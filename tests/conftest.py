import pytest
import sqlite3
import pandas as pd
from unittest.mock import MagicMock
import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mock_db import create_mock_iris_db


@pytest.fixture
def mock_spark():
    """
    Mock do Spark Session para testes locais
    """
    mock_spark = MagicMock()
    
    # Mock do DataFrame com dados de exemplo
    mock_df = MagicMock()
    mock_df.columns = ['sepal_length_cm', 'sepal_width_cm', 'petal_length_cm', 'petal_width_cm', 'species']
    mock_df.count.return_value = 150
    
    # Mock do select com funções de agregação (simulando sem nulls)
    mock_select = MagicMock()
    mock_row = MagicMock()
    # Simular que não há nulls (retorna 0 para todas as colunas)
    mock_row.__getitem__ = lambda self, key: 0
    mock_select.collect.return_value = [mock_row]
    mock_df.select.return_value = mock_select
    
    # Mock do read.format
    mock_read = MagicMock()
    mock_read.format.return_value.load.return_value = mock_df
    mock_spark.read = mock_read
    
    return mock_spark


@pytest.fixture
def spark(mock_spark):
    """
    Fixture spark que usa o mock para testes locais
    """
    return mock_spark


@pytest.fixture
def sample_iris_data():
    """
    Dados de exemplo do Iris para testes
    """
    return {
        'sepal_length_cm': [5.1, 4.9, 4.7, 4.6, 5.0],
        'sepal_width_cm': [3.5, 3.0, 3.2, 3.1, 3.6],
        'petal_length_cm': [1.4, 1.4, 1.3, 1.5, 1.4],
        'petal_width_cm': [0.2, 0.2, 0.2, 0.2, 0.2],
        'species': ['setosa', 'setosa', 'setosa', 'setosa', 'setosa']
    }


@pytest.fixture
def mock_iris_db():
    """
    Fixture que cria um banco de dados mock do Iris
    """
    conn = create_mock_iris_db()
    yield conn
    conn.close()
