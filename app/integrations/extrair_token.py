import os
import requests
import tempfile
import urllib3
from dotenv import load_dotenv
from pynfe.processamento.comunicacao import ComunicacaoSefaz
import xml.etree.ElementTree as ET

# Novas bibliotecas para segurança criptográfica
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

# Silenciar avisos de HTTPS não verificado 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
Este módulo é responsável por extrair tokens de autenticação e segredos do BeyondTrust.
Ele utiliza a API do BeyondTrust para obter tokens de acesso e baixar segredos específicos.

Funções:
- obter_token(): Obtém um token de acesso usando as credenciais do cliente.
- baixa_segredo_pelo_titulo(access_token, titulo): Baixa o conteúdo de um segredo específico usando o token de acesso e o título do segredo.

'''
def obter_token():
    url = "https://grupopereira.ps.beyondtrustcloud.com/BeyondTrust/api/public/v3/Auth/Connect/Token"
    payload = f'grant_type=client_credentials&client_id={os.getenv("BT_CLIENT_ID")}&client_secret={os.getenv("BT_CLIENT_SECRET")}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    print("Token obtido com sucesso.")
    return response.json()["access_token"]

def baixa_segredo_pelo_titulo(access_token, titulo):
    url_sign = "https://grupopereira.ps.beyondtrustcloud.com/BeyondTrust/api/public/v3/Auth/SignAppIn"
    headers_auth = {'Authorization': f'Bearer {access_token}'}
    requests.post(url_sign, headers=headers_auth).raise_for_status()

    print("Autenticação realizada com sucesso.")

    url_find = f'https://grupopereira.ps.beyondtrustcloud.com/BeyondTrust/api/public/v3/secrets-safe/secrets?path={os.getenv("PATH_CLIENT")}&separator=/&title={titulo}&version=3.1'
    resp = requests.get(url_find, headers=headers_auth)
    resp.raise_for_status()
    
    dados_busca = resp.json()
    if not dados_busca:
        raise Exception(f"Segredo com título '{titulo}' não encontrado.")
    
    # Acessando o primeiro item da lista de resultados 
    secret_id = dados_busca[0]["Id"]

    url_dl = f"https://grupopereira.ps.beyondtrustcloud.com/BeyondTrust/api/public/v3/secrets-safe/secrets/{secret_id}/file/download"
    content_resp = requests.get(url_dl, headers=headers_auth)
    content_resp.raise_for_status()
    print("Segredo baixado com sucesso.")
    
    return content_resp.text

