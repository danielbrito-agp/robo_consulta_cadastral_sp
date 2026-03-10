import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from app.core.timezone import UTC_MINUS_4

'''
Este módulo é responsável por configurar o logging da aplicação. Ele define um logger global que pode ser importado e
utilizado em qualquer parte do código para registrar mensagens de log.
A configuração inclui:
- Log em arquivo com rotação (máximo de 5MB por arquivo, mantendo os 5 arquivos mais recentes)
- Log no console para facilitar a visualização em tempo real, especialmente útil quando rodando em Docker
- Formato de log padronizado com timestamp, nível de log, nome do logger e mensagem

O diretório de logs é criado automaticamente se não existir.

'''

LOG_DIR = "app\\logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    formatter.converter = lambda ts: datetime.fromtimestamp(ts, tz=UTC_MINUS_4).timetuple()

    # Log em arquivo com rotação
    file_handler = RotatingFileHandler(
        f"{LOG_DIR}/robo_consulta.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Log no console (Docker vai capturar)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger