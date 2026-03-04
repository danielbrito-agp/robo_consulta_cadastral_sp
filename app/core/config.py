import os
from dotenv import load_dotenv

load_dotenv()

'''
    Configurações do sistema
    - Variáveis de ambiente
    - Parâmetros globais

    Detalhamento das variáveis de ambiente:
    - DB_USER: Usuário do banco de dados Oracle
    - DB_PASSWORD: Senha do banco de dados Oracle
    - DB_DSN: Data Source Name para conexão com o banco Consinco
    - DB_DW_DSN: Data Source Name para conexão com o Data Warehouse (DW)
    '''


class Settings:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    DB_DSN = os.getenv("DB_DSN")
    DB_DW_DSN = os.getenv("DB_DW_DSN")

    INTERVALO_SEM_DADOS = 300  # 5 minutos
    LOTE_BUSCA = 20 # Quantidade de clientes a buscar por vez do banco operacional

settings = Settings()