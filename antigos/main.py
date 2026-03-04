import os
import oracledb
import time
import random
import xml.etree.ElementTree as ET
from datetime import datetime, date
from dotenv import load_dotenv
from app.integrations.extrair_token import obter_token, baixa_segredo_pelo_titulo
from consultas_db import consultar_status_hoje, cancelar_pedido, consultar_sefaz

INTERVALO_SEM_DADOS = 300  # 5 minutos

load_dotenv()

def worker_sefaz():

    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_dsn = os.getenv("DB_DSN")
    db_dsn_dw = os.getenv("DB_DSN_DW")

    print("🔐 Carregando certificado...")
    token = obter_token()
    key_content = baixa_segredo_pelo_titulo(token, "pertech_ecnpj_key")
    cert_content = baixa_segredo_pelo_titulo(token, "pertech_ecnpj_cert")
    print("✅ Certificado carregado")

    while True:
        try:

            with oracledb.connect(user=db_user, password=db_pass, dsn=db_dsn) as c5 , oracledb.connect(user=db_user, password=db_pass, dsn=db_dsn_dw) as dw:
                cursor = c5.cursor()
                cursor_dw = dw.cursor()

                sql_busca = """
                    SELECT CNPJ, UF, NROPEDVENDA, NROEMPRESA
                    FROM consinco.gpv_clientesefaz
                    WHERE UF = 'MS'
                """

                cursor.execute(sql_busca)
                registros = cursor.fetchall()

                if not registros:
                    print("⏳ Nenhum registro encontrado. Aguardando 5 minutos...")
                    time.sleep(INTERVALO_SEM_DADOS)
                    continue

                for cnpj, uf, nro_pedido, nro_empresa in registros:

                    print(f"\n🔎 Processando CNPJ: {cnpj}")

                    status_hoje = consultar_status_hoje(cursor_dw, cnpj)


                    # CASO JÁ TENHA SIDO CONSULTADO HOJE

                    if status_hoje:

                        print(f"ℹ Já consultado hoje. Status: {status_hoje}")

                        if status_hoje == "NÃO HABILITADO":
                            print("🚨 Cancelando pedido...")
                            print(f'Pedido: {nro_pedido} | Empresa: {nro_empresa}')
                            # cancelar_pedido(cursor, nro_pedido, nro_empresa)
                            # c5.commit()

                        continue


                    # NOVA CONSULTA
                    status = consultar_sefaz(cert_content, key_content, cnpj, uf)

                    print(f"Resultado consulta: {status}")

                    cursor.execute("""
                        INSERT INTO SITUACAO_CADASTRAL_CNPJ
                        (CNPJ, STATUS, UF, DATA_CONSULTADA)
                        VALUES (:1, :2, :3, :4)
                    """, [cnpj, status, uf, datetime.now()])

                    c5.commit()

                    if status == "NÃO HABILITADO":
                        print("🚨 Cancelando pedido...")
                        print(f'Pedido: {nro_pedido} | Empresa: {nro_empresa}')
                        # cancelar_pedido(cursor, nro_pedido, nro_empresa)
                        # c5.commit()

                print("✅ Ciclo finalizado. Aguardando 5 minutos...\n")
                time.sleep(INTERVALO_SEM_DADOS)

        except Exception as e:
            print(f"🔥 Erro no loop principal: {e}")
            time.sleep(30)

if __name__ == "__main__":
    worker_sefaz()