import oracledb
from app.core.config import settings

'''
Este módulo centraliza as conexões com os bancos de dados, tanto operacional quanto DW.
A ideia é ter um único ponto de manutenção para as credenciais e configurações de conexão.
'''

def get_operacional_connection():
    return oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_DSN
    )


def get_dw_connection():
    return oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_DW_DSN
    )