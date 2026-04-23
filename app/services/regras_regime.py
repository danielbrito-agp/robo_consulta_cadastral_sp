import logging
from app.repositories import cliente_repository

import logging

logger = logging.getLogger(__name__)
COD_SIMPLES_NACIONAL = 3


def extrair_status_e_regime(resultado):
    status = resultado
    status_simples = None

    if isinstance(resultado, str) and "|" in resultado:
        regime, situacao = resultado.split("|", 1)
        status_simples = regime
        status = situacao
    elif resultado in ("SIMPLES_NACIONAL", "NAO_SIMPLES_NACIONAL"):
        status_simples = resultado
        status = "SITUACAO_NAO_INFORMADA"

    return status, status_simples

def aplicar_regras_tributacao(status_simples, cod_reg_tributacao, seq_pessoa, cursor_op):
    """
    Implementa as 4 regras de tributação conforme definidas:
    1. SIMPLES_NACIONAL + COD_REG_TRIBUTACAO == 3: não faz nada
    2. NAO_SIMPLES_NACIONAL + COD_REG_TRIBUTACAO != 3: não faz nada
    3. NAO_SIMPLES_NACIONAL + COD_REG_TRIBUTACAO == 3: DELETE registro com SEQPESSOA
    4. SIMPLES_NACIONAL + COD_REG_TRIBUTACAO != 3: INSERT registro com NROREGTRIBCLIEEMP e SEQPESSOA
    """
    try:
        cod_reg_tributacao = int(cod_reg_tributacao)
    except (TypeError, ValueError):
        logger.warning(
            "COD_REG_TRIBUTACAO inválido para SEQPESSOA %s: %s. Pulando regra de tributação.",
            seq_pessoa,
            cod_reg_tributacao,
        )
        return False

    if status_simples == "SIMPLES_NACIONAL" and cod_reg_tributacao == COD_SIMPLES_NACIONAL:
        logger.info(f"Regra 1: SIMPLES_NACIONAL + COD_REG=3. Nenhuma ação.")
        return False
    
    if status_simples == "NAO_SIMPLES_NACIONAL" and cod_reg_tributacao != COD_SIMPLES_NACIONAL:
        logger.info(f"Regra 2: NAO_SIMPLES_NACIONAL + COD_REG!=3. Nenhuma ação.")
        return False
    
    if status_simples == "NAO_SIMPLES_NACIONAL" and cod_reg_tributacao == COD_SIMPLES_NACIONAL:
        logger.info(f"Regra 3: NAO_SIMPLES_NACIONAL + COD_REG=3. Deletando registro de tributação.")
        cliente_repository.deletar_registro_tributacao(cursor_op, COD_SIMPLES_NACIONAL, seq_pessoa)
        return True
    
    if status_simples == "SIMPLES_NACIONAL" and cod_reg_tributacao != COD_SIMPLES_NACIONAL:
        logger.info(f"Regra 4: SIMPLES_NACIONAL + COD_REG!=3. Inserindo registro de tributação.")
        #Deletar o registro antigo com  o nroregtribclieemp atual antes de subir com o novo.
        cliente_repository.deletar_registro_tributacao(cursor_op, cod_reg_tributacao, seq_pessoa)
        cliente_repository.inserir_registro_tributacao(cursor_op, COD_SIMPLES_NACIONAL, seq_pessoa)
        return True

    return False