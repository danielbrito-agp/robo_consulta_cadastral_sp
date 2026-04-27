import time
import random
import xml.etree.ElementTree as ET
from app.integrations.extrair_token import obter_token, baixa_segredo_pelo_titulo
from app.integrations.realizar_consulta import RealizarConsulta as realizar
from app.utils.retry import retry
import logging

logger = logging.getLogger(__name__)


class SefazService:
    '''
    Esta classe é responsável por interagir com a SEFAZ para consultar o status cadastral de um CNPJ.
    Ela carrega o certificado digital uma única vez e reutiliza para todas as consultas, otimizando o desempenho.

    O método `consultar` é decorado com `@retry()`, o que significa que em caso de falhas (como erros de rede ou respostas inesperadas),
     ele tentará novamente a consulta automaticamente, aumentando a robustez do serviço.

    
    '''
    def __init__(self):
        token = obter_token()
        self.key = baixa_segredo_pelo_titulo(token, "key_sdb_09477652011716")
        self.cert = baixa_segredo_pelo_titulo(token, "cert_sdb_09477652011716")

    @staticmethod
    def _get_text(root, path):
        value = root.findtext(path)
        if value is None:
            return None
        text = value.strip()
        return text or None

    def _extrair_dados_xml(self, xml_text):
        root = ET.fromstring(xml_text)
        dados_xml = {
            "cnpj": self._get_text(root, ".//{*}infCad/{*}CNPJ"),
            "ie": self._get_text(root, ".//{*}infCad/{*}IE"),
            "uf": self._get_text(root, ".//{*}infCad/{*}UF"),
            "csit": self._get_text(root, ".//{*}infCad/{*}cSit"),
            "ind_cred_nfe": self._get_text(root, ".//{*}infCad/{*}indCredNFe"),
            "ind_cred_cte": self._get_text(root, ".//{*}infCad/{*}indCredCTe"),
            "xnome": self._get_text(root, ".//{*}infCad/{*}xNome"),
            "xfant": self._get_text(root, ".//{*}infCad/{*}xFant"),
            "xreg_apur": self._get_text(root, ".//{*}infCad/{*}xRegApur"),
            "cnae": self._get_text(root, ".//{*}infCad/{*}CNAE"),
            "dh_consulta": self._get_text(root, ".//{*}infCons/{*}dhCons"),
            "d_ini_ativ": self._get_text(root, ".//{*}infCad/{*}dIniAtiv"),
            "d_ult_sit": self._get_text(root, ".//{*}infCad/{*}dUltSit"),
            "xlgr": self._get_text(root, ".//{*}infCad/{*}ender/{*}xLgr"),
            "nro": self._get_text(root, ".//{*}infCad/{*}ender/{*}nro"),
            "xbairro": self._get_text(root, ".//{*}infCad/{*}ender/{*}xBairro"),
            "cmun": self._get_text(root, ".//{*}infCad/{*}ender/{*}cMun"),
            "xmun": self._get_text(root, ".//{*}infCad/{*}ender/{*}xMun"),
            "cep": self._get_text(root, ".//{*}infCad/{*}ender/{*}CEP"),
            "xml_bruto": xml_text,
        }

        regime = None
        situacao = None

        if dados_xml["xreg_apur"]:
            regime_txt = dados_xml["xreg_apur"].upper()
            regime = "SIMPLES_NACIONAL" if regime_txt in {"SIMPLES NACIONAL", "SIMPLES NACIONAL - MEI"} else "NAO_SIMPLES_NACIONAL"

        if dados_xml["csit"]:
            situacao = "HABILITADO" if dados_xml["csit"] == "1" else "NAO_HABILITADO"

        return dados_xml, regime, situacao

    @retry()
    def consultar(self, cnpj, uf):
        def _executar_consulta():
            time.sleep(random.randint(4, 16))
            resultado = realizar.realizar_consulta_cadastral(
                self.cert,
                self.key,
                cnpj,
                uf
            )
            '''
            Nessa etapa, o robô processará a resposta da SEFAZ, extraindo as informações relevantes do XML retornado.
             Ele verificará se a resposta foi bem-sucedida (código HTTP 200) e, em caso afirmativo, tentará extrair as tags <xRegApur> e <cSit>.
              Com base no conteúdo dessas tags, o robô determinará o regime tributário e a situação cadastral do CNPJ consultado.
               Se as tags não forem encontradas ou estiverem vazias, o robô registrará essa informação para análise posterior.
                Caso a resposta da SEFAZ não seja bem-sucedida, o robô registrará o código de erro HTTP para diagnóstico.
            '''
            if resultado.status_code == 200:
                dados_xml, regime, situacao = self._extrair_dados_xml(resultado.text)
                resultado_status = "TAG_NAO_ENCONTRADA"

                if regime and situacao:
                    resultado_status = f"{regime}|{situacao}"
                elif regime:
                    resultado_status = regime
                elif situacao:
                    resultado_status = situacao

                return {"resultado": resultado_status, "dados_xml": dados_xml}

            return {"resultado": f"ERRO_HTTP_{resultado.status_code}", "dados_xml": None}
            # ...existing code...
        
        '''Nessa etapa o robô tentará realizar novamente a consulta em caso de falhas,
          como erros de rede ou respostas inesperadas, aumentando a robustez do serviço.
           Mas caso ocorra falha novamente, o robô irá registrar a falha no log e encerrar o processo para evitar loops infinitos.'''
        try:
            logger.info(f"Iniciando consulta para CNPJ {cnpj}")
            resultado = _executar_consulta()

            if resultado["resultado"].startswith("ERRO_HTTP_"):
                logger.warning(f"Primeira tentativa falhou para CNPJ {cnpj}: {resultado['resultado']}. Aguardando 50s para nova tentativa...")
                time.sleep(120)
                logger.info(f"Realizando nova tentativa para CNPJ {cnpj}")
                resultado = _executar_consulta()
                if resultado["resultado"].startswith("ERRO_HTTP_"):
                    logger.warning(f"Segunda tentativa também falhou para CNPJ {cnpj}: {resultado['resultado']}. Encerrando.")

            return resultado

        except Exception as e:
            logger.error(f"Erro ao consultar CNPJ {cnpj}: {e}", exc_info=True)
            raise 
