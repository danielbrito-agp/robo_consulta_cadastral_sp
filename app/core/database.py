import oracledb
from app.core.config import settings

'''
Este módulo centraliza as conexões com os bancos de dados, tanto operacional quanto DW.
A ideia é ter um único ponto de manutenção para as credenciais e configurações de conexão.
'''

# Função para obter conexão com o banco CONSINCO
def get_operacional_connection():
    conn = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_DSN
    )
    _set_session_timezone(conn)
    return conn


# Função para obter conexão com o banco Data Warehouse
def get_dw_connection():
    conn = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_DW_DSN
    )
    _set_session_timezone(conn)
    return conn


def _set_session_timezone(conn):
    with conn.cursor() as cursor:
        cursor.execute("ALTER SESSION SET TIME_ZONE = '-04:00'")