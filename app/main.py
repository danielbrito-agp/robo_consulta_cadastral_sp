import time
from app.core.database import get_operacional_connection, get_dw_connection
from app.core.logger import setup_logger
from app.core.config import settings
from app.repositories import cliente_repository, status_repository, consulta_xml_repository
from app.services.sefaz_service import SefazService
from app.services.cancelamento_service import cancelar_pedido
from app.core.logger import setup_logger
from app.services.regras_regime import extrair_status_e_regime, aplicar_regras_tributacao
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

                for cnpj, uf, ie, nro_pedido, nro_empresa, cod_reg_tributacao, _regime_tributacao, seq_pessoa in clientes:

                    logger.info(f"Processando {cnpj}")
                    
                    # Verifica se já existe consulta para o pedido, evitando processar o mesmo pedido mais de uma vez"
                    ja_existe_pedido = status_repository.existe_consulta_pedido(cursor_dw, cnpj, nro_pedido)

                    if ja_existe_pedido:
                        logger.info(
                            f"CNPJ {cnpj} já possui consulta para o pedido {nro_pedido}. Pulando processamento."
                        )
                        continue

                    # Consulta no DW
                    status_hoje = status_repository.consultar_status_hoje(cursor_dw, cnpj)

                    '''
                    Se o cliente já tiver sido consultado hoje, o worker registra essa informação e, se o status for "NÃO HABILITADO",
                      ele tem a lógica para cancelar o pedido no sistema operacional.
                    Em seguida, ele continua para o próximo cliente, evitando consultas desnecessárias à SEFAZ para clientes que já foram processados no dia.

                    '''

                    if status_hoje:
                        logger.info(f"Já consultado hoje: {status_hoje}")
                        
                        #Caso o retorno de status seja um erro ou tag não encontrada, tenta nova consulta    
                        if status_hoje.startswith("ERRO") or status_hoje == "TAG_NAO_ENCONTRADA":
                            logger.warning(f"Consulta anterior para {cnpj} retornou {status_hoje}. Tentando nova consulta.")

                        else:
                            logger.info(f"Status cadastral para {cnpj} já consultado hoje: {status_hoje}")

                            # Reaproveita o status já consultado no dia para registrar o pedido atual no DW.
                            status_simples_hoje = status_repository.consultar_status_simples(cursor_dw, cnpj)
                            status_c5_hoje = status_repository.consultar_status_c5_hoje(cursor_dw, cnpj) or "NAO_ALTERADO"
                            status_repository.inserir_status(
                                cursor_dw,
                                cnpj,
                                status_hoje,
                                uf,
                                nro_pedido,
                                status_simples_hoje,
                                status_c5_hoje
                            )
                            conn_dw.commit()

                            # Se não habilitado → cancela no operacional
                            if status_hoje == "NAO_HABILITADO":
                                #usar esse print para ver casos que poderiam ser cancelados (uso de teste)
                                print(f'Pedido: {nro_pedido} | Empresa: {nro_empresa}')
                                # cancelar_pedido(cursor_op, nro_pedido, nro_empresa)
                                # conn_op.commit()

                        continue

                    # Nova consulta SEFAZ
                    resultado_consulta = sefaz_service.consultar(cnpj, uf, ie)
                    status, status_simples = extrair_status_e_regime(resultado_consulta["resultado"])

                    if resultado_consulta["dados_xml"]:
                        consulta_xml_repository.inserir_consulta_xml(cursor_dw, resultado_consulta["dados_xml"])

                    status_c5 = "NAO_ALTERADO"

                    # Aplica regras de tributação (DELETE/INSERT na tabela de regiões tributárias)
                    if status_simples:
                        alterou_c5 = aplicar_regras_tributacao(
                            status_simples,
                            cod_reg_tributacao,
                            seq_pessoa,
                            cursor_op
                        )
                        if alterou_c5:
                            status_c5 = "ALTERADO"
                        conn_op.commit()

                    # Salva no DW
                    status_repository.inserir_status(
                        cursor_dw,
                        cnpj,
                        status,
                        uf,
                        nro_pedido,
                        status_simples,
                        status_c5
                    )
                    conn_dw.commit()

                    # Se não habilitado → cancela no operacional
                    if status == "NAO_HABILITADO":
                        #usar esse print para ver casos que poderiam ser cancelados (uso de teste)
                        print(f'Pedido: {nro_pedido} | Empresa: {nro_empresa}')
                        # cancelar_pedido(cursor_op, nro_pedido, nro_empresa)
                        # conn_op.commit()

                logger.info("Ciclo finalizado.")
                time.sleep(settings.INTERVALO_SEM_DADOS)

        except Exception as e:
            logger.error(f"Erro no worker: {e}")
            # Em caso de erro, o worker aguarda 30 segundos antes de tentar novamente, evitando loops rápidos em caso de falhas persistentes.
            time.sleep(30) 


if __name__ == "__main__":
    worker()
