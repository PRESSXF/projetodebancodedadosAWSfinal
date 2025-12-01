import json
import os
import random
import string
import boto3
from urllib.parse import urlparse

# Conexão com DynamoDB
dynamodb = boto3.resource("dynamodb")
# Usar .get() para evitar erro se a variável de ambiente não estiver definida (embora deva estar no SAM)
NOME_TABELA = os.environ.get("NOME_TABELA")
tabela = dynamodb.Table(NOME_TABELA)

# Tamanho do código gerado
TAMANHO_CODIGO = 6
CARACTERES = string.ascii_letters + string.digits


def gerar_codigo(tamanho=TAMANHO_CODIGO):
    return "".join(random.choices(CARACTERES, k=tamanho))


def url_valida(url):
    try:
        p = urlparse(url)
        # Verifica se o esquema é HTTP(S) e se há um endereço de rede (netloc)
        return p.scheme in ("http", "https") and p.netloc != ""
    except:
        return False


def criar_encurtamento(evento):
    """Lida com o endpoint POST /encurtar para criar um novo registro."""
    try:
        corpo = json.loads(evento.get("body") or "{}")
        url_original = corpo.get("url")

        if not url_original or not url_valida(url_original):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "erro": "URL inválida. Envie no formato: {\"url\": \"https://site.com\"}"
                    }
                ),
            }

        # gera código até não repetir (máximo de 5 tentativas)
        for _ in range(5):
            codigo = gerar_codigo()
            try:
                tabela.put_item(
                    Item={"codigo": codigo, "url_original": url_original},
                    # Garante que o item só será inserido se o 'codigo' não existir
                    ConditionExpression="attribute_not_exists(codigo)",
                )
                break
            except boto3.exceptions.ClientError as e:
                # Verifica se a exceção é por falha na ConditionExpression
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    continue # Tenta gerar outro código
                raise # Lança qualquer outra exceção
        else:
            # Se o loop terminar sem 'break'
            return {
                "statusCode": 500,
                "body": json.dumps({"erro": "Falha ao gerar código único."}),
            }

        return {
            "statusCode": 201,
            "body": json.dumps(
                {
                    "mensagem": "URL encurtada com sucesso!",
                    "codigo": codigo,
                    # Retorna o path do recurso encurtado
                    "url_encurtada": f"/{codigo}", 
                }
            ),
        }

    except Exception as e:
        # Erro genérico (pode ser problema de permissão no DynamoDB, etc.)
        return {"statusCode": 500, "body": json.dumps({"erro": str(e)})}


def redirecionar(evento):
    """Lida com o endpoint GET /{codigo} para buscar a URL original e redirecionar."""
    try:
        # O código é extraído dos pathParameters (ex: /aB92k -> codigo: aB92k)
        codigo = evento["pathParameters"].get("codigo")
        
        # Este 'if not codigo' deve ser teoricamente coberto pela rota /encurtar
        # Mas é bom manter para robustez.
        if not codigo:
            # Não deve ocorrer se o API Gateway estiver mapeado para /{codigo}
            return {"statusCode": 400, "body": json.dumps({"erro": "Código não informado."})} 

        resposta = tabela.get_item(Key={"codigo": codigo})
        url_original = resposta.get("Item", {}).get("url_original")

        if not url_original:
            return {"statusCode": 404, "body": json.dumps({"erro": "Código não encontrado."})}

        # --- CORREÇÃO CHAVE AQUI ---
        # Alterado de 302 para 301. O 301 é mais apropriado para encurtadores,
        # pois informa o navegador/bot que o redirecionamento é PERMANENTE.
        # Isso otimiza o cache e o SEO (embora SEO não seja foco aqui, 301 é a prática padrão).
        
        # Certificamos de que a URL original tem o esquema para evitar erros de path relativo
        if not url_valida(url_original):
             # Isso deve ser coberto pela função criar_encurtamento, mas é uma segurança
             return {"statusCode": 500, "body": json.dumps({"erro": "URL original inválida no DB."})}
        
        return {
            "statusCode": 301,  # Redirecionamento Permanente
            "headers": {
                # O cabeçalho 'Location' é a chave para o redirecionamento
                "Location": url_original,
            },
            # O corpo deve ser uma string vazia para o API Gateway
            "body": "",
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"erro": str(e)})}


def handler(evento, contexto):
    """Função principal da Lambda que roteia o evento com base no método e caminho."""
    metodo = evento.get("httpMethod")
    caminho = evento.get("path", "")
    
    # 1. Rota de criação: POST /encurtar
    # Note que o 'path' do evento do API Gateway V2 é '/encurtar', enquanto V1 pode ser /prod/encurtar
    if metodo == "POST" and caminho.endswith("/encurtar"):
        return criar_encurtamento(evento)

    # 2. Rota de redirecionamento: GET /{codigo}
    # No API Gateway V2, a rota GET /{codigo} mapeia para pathParameters,
    # então só verificamos se é um método GET e deixamos a função redirecionar validar o código.
    # Se fosse 'GET /encurtar', isso seria um erro, mas o template.yaml deve garantir
    # que a única rota GET seja /{codigo}
    if metodo == "GET" and evento.get("pathParameters") and evento.get("pathParameters").get("codigo"):
        return redirecionar(evento)

    # Retorna erro para qualquer outra rota/método não mapeado
    return {"statusCode": 400, "body": json.dumps({"erro": "Requisição inválida ou rota não encontrada."})}