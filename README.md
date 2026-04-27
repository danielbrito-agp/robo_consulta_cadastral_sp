# Robô de Consulta Cadastral SEFAZ - SP

Automação em Python para consulta cadastral de CNPJ do estado de SP na SEFAZ, com integração entre banco operacional (Consinco/C5), Data Warehouse (DW) e gestão segura de certificado digital via BeyondTrust.

## Visão geral

Este projeto executa um **worker contínuo** que:

1. Busca clientes pendentes no banco operacional.
2. Verifica no DW se o CNPJ já foi consultado no dia.
3. Quando necessário, consulta o status cadastral na SEFAZ.
4. Persiste o resultado no DW.
5. Salva os dados completos do XML de retorno na tabela `SEFAZ_CONSULTA_XML`.
6. Para status **"NÃO HABILITADO"**, possui suporte à lógica de cancelamento no operacional (atualmente comentada no fluxo principal).

## Arquitetura

- **Orquestração:** `app/main.py`
- **Configurações e variáveis de ambiente:** `app/core/config.py`
- **Conexão Oracle (operacional e DW):** `app/core/database.py`
- **Logging com rotação de arquivo + console:** `app/core/logger.py`
- **Consulta de clientes no operacional:** `app/repositories/cliente_repository.py`
- **Persistência/consulta de status no DW:** `app/repositories/status_repository.py`
- **Persistência dos dados completos do XML SEFAZ:** `app/repositories/consulta_xml_repository.py`
- **Consulta SEFAZ com retry:** `app/services/sefaz_service.py`
- **Cancelamento de pedido (procedure):** `app/services/cancelamento_service.py`
- **Integrações de segredo/certificado:** `app/integrations/extrair_token.py`
- **Chamada da consulta cadastral via PyNFe:** `app/integrations/realizar_consulta.py`
- **Utilitário de retentativa (backoff exponencial + jitter):** `app/utils/retry.py`

## Pré-requisitos

- Python **3.11+**
- Acesso aos bancos Oracle (operacional e DW)
- Credenciais BeyondTrust para obtenção dos segredos do certificado
- Docker (opcional)

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com:

```env
DB_USER=seu_usuario_oracle
DB_PASSWORD=sua_senha_oracle
DB_DSN=host:porta/servico_operacional
DB_DW_DSN=host:porta/servico_dw

BT_CLIENT_ID=seu_client_id_beyondtrust
BT_CLIENT_SECRET=seu_client_secret_beyondtrust
PATH_CLIENT=caminho/do/safe/no/beyondtrust
```

### Observações

- `DB_DSN` aponta para o banco operacional (Consinco/C5).
- `DB_DW_DSN` aponta para o Data Warehouse.
- O worker usa o mesmo usuário/senha para ambas conexões, variando apenas o DSN.

## Instalação local

```bash
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> O código utiliza também bibliotecas como `cryptography` e `pynfe`. Caso não estejam disponíveis no ambiente, instale-as manualmente ou atualize `requirements.txt`.

## Execução local

```bash
python -m app.main
```

## Execução com Docker

Build da imagem:

```bash
docker build -t robo-consulta-cadastral .
```

Execução do container:

```bash
docker run --rm --env-file .env robo-consulta-cadastral
```

O `Dockerfile` já está preparado para iniciar com:

```bash
python -m app.main
```

## Fluxo funcional

1. O worker inicializa logger e `SefazService` (carrega certificado e chave uma única vez).
2. Abre conexão com operacional e DW.
3. Busca clientes na tabela `consinco.gpv_clientesefaz` (filtro atual por `UF = 'SP'`).
4. Para cada cliente:
   - Verifica se há status de hoje em `SITUACAO_CADASTRAL_CNPJ`.
   - Se não houver, consulta SEFAZ, salva os campos do XML em `SEFAZ_CONSULTA_XML` e grava status no DW.
5. Aguarda `INTERVALO_SEM_DADOS` (padrão: 300s) e repete o ciclo.
6. Em exceções no loop principal, aguarda 30s antes de retomar.

## Persistência do XML da SEFAZ

Além do status consolidado em `SITUACAO_CADASTRAL_CNPJ`, o worker também persiste o XML completo retornado pela consulta na tabela `SEFAZ_CONSULTA_XML`.

- O XML bruto é armazenado em `XML_BRUTO` (CLOB).
- Também são salvos campos extraídos para consulta analítica:
  - identificação: `CNPJ`, `IE`, `UF`, `CSIT`
  - crédito/documento: `IND_CRED_NFE`, `IND_CRED_CTE`
  - cadastro: `XNOME`, `XFANT`, `XREG_APUR`, `CNAE`
  - datas: `DHI_CONSULTA`, `D_INI_ATIV`, `D_ULT_SIT`
  - endereço: `XLGR`, `NRO`, `XBAIRRO`, `CMUN`, `XMUN`, `CEP`

Essa gravação ocorre no mesmo ciclo da consulta nova na SEFAZ, antes do `commit` no DW.

## Logging e observabilidade

- Logs em arquivo rotativo: `app/logs/robo_consulta.log`
- Logs também enviados para stdout (útil para Docker/Kubernetes).
- Formato padrão:
  - timestamp
  - nível
  - logger
  - mensagem

## Estratégia de resiliência

- Método de consulta SEFAZ usa decorator de retry com:
  - até 4 tentativas (padrão)
  - backoff exponencial
  - jitter aleatório

Possíveis retornos de status no fluxo:

- `HABILITADO`
- `NÃO HABILITADO`
- `TAG_NAO_ENCONTRADA`
- `ERRO_HTTP_<status_code>`

## Estrutura de pastas

```text
.
├── app/
│   ├── core/
│   ├── integrations/
│   ├── repositories/
│   ├── services/
│   ├── utils/
│   ├── logs/
│   └── main.py
├── antigos/
├── Dockerfile
└── requirements.txt
```

## Segurança

- Certificado/chave são obtidos dinamicamente via BeyondTrust.
- O PFX é gerado em arquivo temporário somente durante a chamada e removido ao final.
- Não versionar `.env` nem credenciais em repositório.

## Backlog recomendado

- Incluir todas as dependências efetivas no `requirements.txt`.
- Parametrizar filtros de busca (ex.: UF) via variável de ambiente.
- Reativar fluxo de cancelamento no operacional quando homologado.
- Adicionar testes automatizados para camadas de serviço e repositório.
