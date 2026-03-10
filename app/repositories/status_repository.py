from app.core.timezone import now_utc_minus_4_naive

'''
Este módulo é responsável por interagir com a tabela SITUACAO_CADASTRAL_CNPJ, onde armazenamos o status cadastral consultado na SEFAZ.
Funções:
- consultar_status_hoje: Verifica se já temos um status cadastral para o CNPJ consultado hoje.
- inserir_status: Insere um novo registro de status cadastral para um CNPJ.

Na função consultar_status_hoje, onde se lê WHERE CNPJ = :1 significa que o valor do CNPJ será passado como no qual está sendo lido [cnpj]. 
O mesmo vale para a função inserir_status, onde os valores são passados como parâmetros na execução do cursor.

'''

def consultar_status_hoje(cursor, cnpj):
    data_referencia = now_utc_minus_4_naive()

    cursor.execute("""
        SELECT STATUS
        FROM SITUACAO_CADASTRAL_CNPJ
        WHERE CNPJ = :1 
          AND TRUNC(DATA_CONSULTADA) = TRUNC(:2)
        ORDER BY DATA_CONSULTADA DESC
    """, [cnpj, data_referencia])

    row = cursor.fetchone()
    return row[0] if row else None


def inserir_status(cursor, cnpj, status, uf, nro_ped_ven):
    data_consultada = now_utc_minus_4_naive()

    cursor.execute("""
        INSERT INTO SITUACAO_CADASTRAL_CNPJ
        (CNPJ, STATUS, UF, DATA_CONSULTADA, NROPEDVENDA)
        VALUES (:1, :2, :3, :4, :5)
    """, [cnpj, status, uf, data_consultada, nro_ped_ven])
