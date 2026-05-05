from datetime import date, datetime

# Funções auxiliares para converter strings ISO 8601 em objetos datetime e date
def _parse_iso_datetime_tz(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None

# A função _parse_iso_date tenta converter uma string ISO 8601 em um objeto date. Se a string for inválida ou None, retorna None.
def _parse_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None

'''
Função inserir_consulta_xml recebe um cursor de banco de dados e um dicionário contendo os dados XML da consulta SEFAZ.
 Ela extrai os campos relevantes do dicionário, converte as datas usando as funções auxiliares e insere os dados
   na tabela SEFAZ_CONSULTA_XML usando uma instrução SQL parametrizada.
'''
def inserir_consulta_xml(cursor, dados_xml):
    dh_consulta = _parse_iso_datetime_tz(dados_xml.get("dh_consulta"))
    d_ini_ativ = _parse_iso_date(dados_xml.get("d_ini_ativ"))
    d_ult_sit = _parse_iso_date(dados_xml.get("d_ult_sit"))

    cursor.execute("""
        INSERT INTO SEFAZ_CONSULTA_XML
        (CNPJ, IE, UF, CSIT, IND_CRED_NFE, IND_CRED_CTE, XNOME, XFANT, XREG_APUR, CNAE,
         DHI_CONSULTA, D_INI_ATIV, D_ULT_SIT, XLGR, NRO, XBAIRRO, CMUN, XMUN, CEP, XML_BRUTO)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10,
                :11, :12, :13, :14, :15, :16, :17, :18, :19, :20)
    """, [
        dados_xml.get("cnpj"),
        dados_xml.get("ie"),
        dados_xml.get("uf"),
        dados_xml.get("csit"),
        dados_xml.get("ind_cred_nfe"),
        dados_xml.get("ind_cred_cte"),
        dados_xml.get("xnome"),
        dados_xml.get("xfant"),
        dados_xml.get("xreg_apur"),
        dados_xml.get("cnae"),
        dh_consulta,
        d_ini_ativ,
        d_ult_sit,
        dados_xml.get("xlgr"),
        dados_xml.get("nro"),
        dados_xml.get("xbairro"),
        dados_xml.get("cmun"),
        dados_xml.get("xmun"),
        dados_xml.get("cep"),
        dados_xml.get("xml_bruto"),
    ])
