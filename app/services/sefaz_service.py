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
            if resultado.status_code == 200:
                root = ET.fromstring(resultado.text.encode("utf-8"))
                csit = root.find(".//{*}cSit")
                if csit is not None:
                    return "HABILITADO" if csit.text == "1" else "NÃO HABILITADO"
                return "TAG_NAO_ENCONTRADA"
            
            return f"ERRO_HTTP_{resultado.status_code}"
        
        '''Nessa etapa o robô tentará realizar novamente a consulta em caso de falhas,
          como erros de rede ou respostas inesperadas, aumentando a robustez do serviço.
           Mas caso ocorra falha novamente, o robô irá registrar a falha no log e encerrar o processo para evitar loops infinitos.'''
        try:
            logger.info(f"Iniciando consulta para CNPJ {cnpj}")
            resultado = _executar_consulta()

            if resultado.startswith("ERRO_HTTP_"):
                logger.warning(f"Primeira tentativa falhou para CNPJ {cnpj}: {resultado}. Aguardando 50s para nova tentativa...")
                time.sleep(50)
                logger.info(f"Realizando nova tentativa para CNPJ {cnpj}")
                resultado = _executar_consulta()
                if resultado.startswith("ERRO_HTTP_"):
                    logger.warning(f"Segunda tentativa também falhou para CNPJ {cnpj}: {resultado}. Encerrando.")

            return resultado

        except Exception as e:
            logger.error(f"Erro ao consultar CNPJ {cnpj}: {e}", exc_info=True)
            raise 