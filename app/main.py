import time
from app.core.database import get_operacional_connection, get_dw_connection
from app.core.logger import setup_logger
from app.core.config import settings
from app.repositories import cliente_repository, status_repository
from app.services.sefaz_service import SefazService
from app.services.cancelamento_service import cancelar_pedido
from app.core.logger import setup_logger
import logging


# Configura o logger
setup_logger()
logger = logging.getLogger(__name__)


'''
Neste código, o worker é responsável por orquestrar todo o processo de consulta cadastral dos clientes na SEFAZ. 
Ele utiliza a classe `SefazService` para realizar as consultas, garantindo que o certificado digital seja carregado apenas
 uma vez e reutilizado para todas as consultas, otimizando o desempenho.

O worker também interage com os repositórios para buscar os clientes a serem processados, verificar se já foram consultados hoje e
 salvar os resultados no Data Warehouse. Em caso de clientes não habilitados, ele tem a lógica para cancelar os pedidos no sistema operacional.

'''

def worker():

    sefaz_service = SefazService()

    while True:
        try:
            with get_operacional_connection() as conn_op, \
                 get_dw_connection() as conn_dw:

                cursor_op = conn_op.cursor()
                cursor_dw = conn_dw.cursor()

                clientes = cliente_repository.buscar_clientes_para_processar(cursor_op)
                '''
                Se não houver clientes para processar, o worker registra essa informação no log e aguarda por um período definido
                  (5 minutos) antes de tentar novamente.
                Isso evita que o sistema fique em um loop constante consumindo recursos quando não há dados para processar.
                
                '''   
                if not clientes:
                    logger.info("Sem registros. Aguardando 5 minutos...")
                    time.sleep(settings.INTERVALO_SEM_DADOS)
                    continue

                for cnpj, uf, nro_pedido, nro_empresa in clientes:

                    logger.info(f"Processando {cnpj}")

                    # Consulta no DW
                    status_hoje = status_repository.consultar_status_hoje(cursor_dw, cnpj)

                    '''
                    Se o cliente já tiver sido consultado hoje, o worker registra essa informação e, se o status for "NÃO HABILITADO",
                      ele tem a lógica para cancelar o pedido no sistema operacional.
                    Em seguida, ele continua para o próximo cliente, evitando consultas desnecessárias à SEFAZ para clientes que já foram processados no dia.

                    '''

                    if status_hoje:
                        logger.info(f"Já consultado hoje: {status_hoje}")

                        # Se não habilitado → cancela no operacional
                        if status_hoje == "NÃO HABILITADO":
                            # print(f'Pedido: {nro_pedido} | Empresa: {nro_empresa}')
                            cancelar_pedido(cursor_op, nro_pedido, nro_empresa)
                            conn_op.commit()

                        continue

                    # Nova consulta SEFAZ
                    status = sefaz_service.consultar(cnpj, uf)

                    # Salva no DW
                    status_repository.inserir_status(cursor_dw, cnpj, status, uf)
                    conn_dw.commit()

                    # Se não habilitado → cancela no operacional
                    if status == "NÃO HABILITADO":
                        # print(f'Pedido: {nro_pedido} | Empresa: {nro_empresa}')
                        cancelar_pedido(cursor_op, nro_pedido, nro_empresa)
                        conn_op.commit()

                logger.info("Ciclo finalizado.")
                time.sleep(settings.INTERVALO_SEM_DADOS)

        except Exception as e:
            logger.error(f"Erro no worker: {e}")
            # Em caso de erro, o worker aguarda 30 segundos antes de tentar novamente, evitando loops rápidos em caso de falhas persistentes.
            time.sleep(30) 


if __name__ == "__main__":
    worker()