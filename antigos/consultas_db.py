import os
import oracledb
import time
import random
import xml.etree.ElementTree as ET
from datetime import datetime, date
from dotenv import load_dotenv
from app.integrations.extrair_token import obter_token, baixa_segredo_pelo_titulo
from app.integrations.realizar_consulta import RealizarConsulta as realizar


load_dotenv()

INTERVALO_SEM_DADOS = 300  # 5 minutos


def cancelar_pedido(cursor, nro_pedido, nro_empresa):
    """
    Executa procedure de cancelamento
    """
    sql_proc = """
    begin
      consinco.sp_cancela_pedvenda(
        pnnropedvenda => :1,
        pnnroempresa => :2,
        psusucancelamento => :3,
        psmotcancelamento => :4,
        psobspedido => :5
      );
    end;
    """

    cursor.execute(
        sql_proc,
        [
            nro_pedido,
            nro_empresa,
            "ROBO_SEFAZ",
            "CNPJ NÃO HABILITADO NA SEFAZ",
            "Cancelamento automático"
        ]
    )

def consultar_status_hoje(cursor_dw, cnpj):
    sql = """
        SELECT STATUS
        FROM SITUACAO_CADASTRAL_CNPJ
        WHERE CNPJ = :1
          AND TRUNC(DATA_CONSULTADA) = TRUNC(SYSDATE)
        ORDER BY DATA_CONSULTADA DESC
    """

    cursor_dw.execute(sql, [cnpj])
    row = cursor_dw.fetchone()

    return row[0] if row else None

def consultar_sefaz(cert, key, cnpj, uf):
    time.sleep(random.randint(4, 8))

    resultado = realizar.realizar_consulta_cadastral(
        cert,
        key,
        cnpj,
        uf
    )

    if resultado.status_code == 200:
        root = ET.fromstring(resultado.text.encode("utf-8"))
        csit = root.find(".//{*}cSit")

        if csit is not None:
            return "HABILITADO" if csit.text == "1" else "NÃO HABILITADO"

        return "TAG_NAO_ENCONTRADA"

    return f"ERRO_HTTP_{resultado.status_code}"
