from app.core.config import settings

def buscar_clientes_para_processar(cursor):

    sql = f"""
        SELECT CNPJ, UF, NROPEDVENDA, NROEMPRESA
        FROM consinco.gpv_clientesefaz
        WHERE UF = 'MS' 
    """

    cursor.execute(sql)
    return cursor.fetchall()


# Essa def não será utilizado, pois a marcação de "processando" poderá afetar o banco em produção da C5. No qual devemos usarmos somente para leitura, sem realizar updates ou inserts.

# def marcar_como_processando(cursor, cnpj):
#     cursor.execute("""
#         UPDATE consinco.gpv_clientesefaz
#         SET PROCESSANDO = 'S'
#         WHERE CNPJ = :1
#     """, [cnpj])