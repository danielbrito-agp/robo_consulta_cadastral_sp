import os
import tempfile
from dotenv import load_dotenv
from pynfe.processamento.comunicacao import ComunicacaoSefaz
import xml.etree.ElementTree as ET
# Novas bibliotecas para segurança criptográfica
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12


'''
Este módulo é responsável por realizar consultas cadastrais na SEFAZ utilizando certificados digitais.
Ele é utilizado pelo worker principal para obter o status cadastral dos CNPJs, como por exemplo 'Habilitado' ou 'Não Habilitado'.
A classe RealizarConsulta encapsula a lógica de comunicação com a SEFAZ, incluindo o carregamento seguro dos certificados e a execução da consulta.

Referências:
[1] Documentação PyNFe: https://pynfe.readthedocs.io/en/latest/
[2] Exemplo de uso do PyNFe para consulta cadastral:
    from pynfe.processamento.comunicacao import ComunicacaoSefaz

    uf = "SP"
    path_pfx = "caminho/para/certificado.pfx"
    senha_pfx = "senha_do_certificado"
    homologacao = False

    con = ComunicacaoSefaz(uf, path_pfx, senha_pfx, homologacao)
    response = con.consulta_cadastro("nfe", "12345678000195", "CNPJ")
    print(response.text)

[3] Gerar PFX em memória: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/serialization/#pkcs12-serialization

'''

class RealizarConsulta:
    @classmethod
    def realizar_consulta_cadastral(cls, cert_pem, key_pem, cnpj_consulta, regional):
        senha_pfx = 'pynfe_temp_pass'
        
        # Carregamento seguro em memória
        private_key = serialization.load_pem_private_key(key_pem.encode(), password=None)
        certificate = x509.load_pem_x509_certificate(cert_pem.encode())
        
        # Geração do PFX temporário compatível com PyNFe [3]
        pfx_data = pkcs12.serialize_key_and_certificates(
            name=b"pynfe_cert",
            key=private_key,
            cert=certificate,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(senha_pfx.encode())
        )

        with tempfile.NamedTemporaryFile(suffix=".pfx", delete=False) as tmp_pfx:
            tmp_pfx.write(pfx_data)
            path_pfx = tmp_pfx.name

        try:
            uf = regional
            homologacao = False
            con = ComunicacaoSefaz(uf,path_pfx, senha_pfx, homologacao)
            
            print(f"Consultando SEFAZ/{uf} para o CNPJ: {cnpj_consulta}...")
            
            # A consulta retorna um objeto Response 
            response = con.consulta_cadastro("nfe", cnpj_consulta, "CNPJ")
            return response
        finally:
            if os.path.exists(path_pfx):
                os.remove(path_pfx)

