from app.core.config import settings

def buscar_clientes_para_processar(cursor):

    sql = f"""
        SELECT CNPJ, UF, IE, NROPEDVENDA, NROEMPRESA, COD_REG_TRIBUTACAO, REGIME_TRIBUTACAO, SEQPESSOA
        FROM consinco.gpv_clientesefaz
        WHERE UF = 'SP'
    """

    cursor.execute(sql)
    return cursor.fetchall()

def deletar_registro_tributacao(cursor, nro_reg_trib, seq_pessoa):
    """
    Deleta registro de tributação para o CNPJ (identified by seq_pessoa) 
    com código de regime tributário = nro_reg_trib (3 = Simples Nacional).
    """
    cursor.execute("""
        DELETE FROM consinco.MRL_CLIENTEREGTRIBUTACAO
        WHERE nroregtribclieemp = :1 AND seqpessoa = :2
    """, [nro_reg_trib, seq_pessoa])

def inserir_registro_tributacao(cursor, nro_reg_trib, seq_pessoa):
    """
    Insere novo registro de tributação para o CNPJ (identified by seq_pessoa)
    com código de regime tributário = nro_reg_trib (3 = Simples Nacional).
    Cria registros para as filiais padrão: 713 e 733.
    """
    filiais = [713, 733]
    
    for nro_empresa in filiais:
        cursor.execute("""
            INSERT INTO consinco.MRL_CLIENTEREGTRIBUTACAO 
                (nroregtribclieemp, seqpessoa, NROEMPRESA, DTAALTERACAO, USUALTERACAO)
            VALUES (:1, :2, :3, SYSDATE, 'ROBORPA')
        """, [nro_reg_trib, seq_pessoa, nro_empresa])

# Essa def não será utilizado, pois a marcação de "processando" poderá afetar o banco em produção da C5. No qual devemos usarmos somente para leitura, sem realizar updates ou inserts.

# def marcar_como_processando(cursor, cnpj):
#     cursor.execute("""
#         UPDATE consinco.gpv_clientesefaz
#         SET PROCESSANDO = 'S'
#         WHERE CNPJ = :1
#     """, [cnpj])