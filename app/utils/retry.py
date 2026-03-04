import time
import random

'''
Este módulo fornece um decorador `retry` que pode ser usado para tentar novamente a execução de uma função em caso de falhas.
O decorador aceita dois parâmetros opcionais:
- `max_tentativas`: O número máximo de tentativas antes de desistir (padrão: 4).
- `base_delay`: O tempo base de espera entre as tentativas, que é multiplicado exponencialmente (padrão: 2 segundos).

A função decorada será executada e, se lançar uma exceção, o decorador irá aguardar um tempo calculado (com backoff exponencial e jitter) antes de tentar novamente.
Se o número máximo de tentativas for atingido, a última exceção será lançada.

'''


def retry(max_tentativas=4, base_delay=2):

    def decorator(func):

        def wrapper(*args, **kwargs):

            for tentativa in range(1, max_tentativas + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    if tentativa == max_tentativas:
                        raise e # Se for a última tentativa, lança a exceção.

                    # Calcula o tempo de espera com backoff exponencial e jitter, para evitar sobrecarregar o serviço em caso de falhas temporárias.
                    # O tempo de espera é calculado como: base_delay * (2 ** tentativa) + um valor aleatório entre 0 e 1 segundo.
                    delay = base_delay * (2 ** tentativa)
                    delay += random.uniform(0, 1)

                    time.sleep(delay)

        return wrapper

    return decorator