import os
import csv
import oracledb
from app.integrations.extrair_token import obter_token, baixa_segredo_pelo_titulo
from app.integrations.realizar_consulta import RealizarConsulta as realizar
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import random
import time

# 1. Carregar variáveis de ambiente
load_dotenv()

def processar_clientes_sefaz():
    # --- Configurações de Conexão ---
    db_user = os.getenv("DB_USER") or "USE"      
    db_pass = os.getenv("DB_PASSWORD") or "SENHA"    
    db_dsn = os.getenv("DB_DSN") or "DSN_LINK"   

    # Tabela interna para armazenar os resultados temporariamente
    lista_resultados = []

    try:
        # 2. Carregar Identidade Digital (UMA ÚNICA VEZ) 
        print("Conectando à BeyondTrust Cloud...")
        token = obter_token()
        key_content = baixa_segredo_pelo_titulo(token, "pertech_ecnpj_key")
        cert_content = baixa_segredo_pelo_titulo(token, "pertech_ecnpj_cert")
        print("✅ Certificado carregado com sucesso.\n")

        # 3. Conectar ao Banco Consinco 
        print(f"Conectando ao banco de dados como {db_user}...")
        with oracledb.connect(user=db_user, password=db_pass, dsn=db_dsn) as connection:
            with connection.cursor() as cursor:
                # Query para buscar os clientes

                '''
                    SELECT CNPJ, UF 
                    FROM consinco.gpv_clientesefaz t 
                    WHERE t.uf = 'MS'
                '''
                sql = """
                    SELECT DISTINCT CNPJ, UF
                    FROM consinco.gpv_clientesefaz t
                    WHERE t.uf = 'MS'
                """
                cursor.execute(sql)
                
                print("Iniciando loop de processamento...")
                print("-" * 60)

                # 4. Loop para cada linha da tabela
                for (cnpj, uf_cliente) in cursor:
                    uf_consulta = str(uf_cliente).strip().upper()
                    
                    try:
                        print(f"Consultando: {cnpj}...")
                        numero = random.randint(5, 15)
                        time.sleep(numero)  # Simula tempo de resposta da SEFAZ
                        # Executa a consulta SEFAZ via PyNFe [1, 2]
                        resultado = realizar.realizar_consulta_cadastral(
                            cert_content, 
                            key_content, 
                            cnpj, 
                            uf_consulta
                        )

                        status_final = "ERRO_CONSULTA" # Valor padrão caso algo falhe

                        if resultado.status_code == 200:
                            xml_data = resultado.text.encode('utf-8')
                            root = ET.fromstring(xml_data)

                            # Localiza a tag cSit ignorando o namespace {*} [1]
                            csit_element = root.find(".//{*}cSit")
                            
                            if csit_element is not None:
                                # Regra de negócio: 1 = HABILITADO, Outros = NÃO HABILITADO
                                status_final = "HABILITADO" if csit_element.text == '1' else "NÃO HABILITADO"
                            else:
                                status_final = "TAG_NAO_ENCONTRADA"
                        else:
                            status_final = f"ERRO_HTTP_{resultado.status_code}"

                        # Arquiva na tabela interna (lista de dicionários)
                        lista_resultados.append({
                            'CNPJ': cnpj,
                            'STATUS': status_final
                        })

                    except Exception as e_row:
                        print(f"🚨 Falha no CNPJ {cnpj}: {e_row}")
                        lista_resultados.append({
                            'CNPJ': cnpj,
                            'STATUS': "ERRO_SISTEMA"
                        })
                    
                print("-" * 60)

        # 5. Salvar em arquivo CSV após o loop 
        if lista_resultados:
            arquivo_csv = "resultado_situacao_cadastral.csv"
            with open(arquivo_csv, mode='w', newline='', encoding='utf-8') as f:
                # Definindo as colunas
                colunas = ['CNPJ', 'STATUS']
                # Usando ';' como delimitador para facilitar abertura direta no Excel brasileiro
                writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
                
                writer.writeheader()
                writer.writerows(lista_resultados)
            
            print(f"✅ Processamento concluído! Arquivo salvo em: {os.path.abspath(arquivo_csv)}")
        else:
            print("⚠️ Nenhum resultado foi processado.")

    except Exception as e:
        print(f"🔥 Erro crítico na execução geral: {e}")

if __name__ == "__main__":
    processar_clientes_sefaz()