# 🔗 Encurtador de URL Serverless

Sistema serverless de encurtamento de URLs desenvolvido com AWS Lambda, API Gateway e DynamoDB. Projeto acadêmico da disciplina de Cloud Computing.

## 📋 Sobre o Projeto

Aplicação 100% serverless que transforma URLs longas em links curtos, utilizando arquitetura moderna e serviços gerenciados da AWS. Demonstra na prática conceitos de:

- ✅ Computação em nuvem
- ✅ Arquitetura serverless
- ✅ Infraestrutura como código
- ✅ Integração de serviços AWS
- ✅ Deploy automatizado

## 🚀 Funcionalidades

- **Encurtamento de URLs**: Gera códigos únicos de 6 caracteres
- **Armazenamento persistente**: Banco NoSQL DynamoDB
- **Redirecionamento automático**: HTTP 301 para URL original
- **API REST**: Endpoints para integração
- **Escalabilidade automática**: Suporta milhares de requisições

## 🏗️ Arquitetura

```
┌──────────┐
│ Usuário  │
└────┬─────┘
     │
     ▼
┌─────────────────┐
│  API Gateway    │
│  - POST /encurtar
│  - GET /{codigo}
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  Lambda         │
│  Python 3.13    │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  DynamoDB       │
│  Tabela: URLs   │
└─────────────────┘
```

## 🛠️ Tecnologias

| Serviço | Função |
|---------|--------|
| **AWS Lambda** | Execução serverless (Python 3.13) |
| **API Gateway** | Endpoints HTTP REST |
| **DynamoDB** | Banco NoSQL gerenciado |
| **CloudFormation** | Infraestrutura como código |
| **AWS SAM** | Build e deploy automatizado |

## 📦 Estrutura do Projeto

```
encurtador-url-serverless/
├── app.py                 # Função Lambda
├── template.yaml          # Template SAM/CloudFormation
├── requirements.txt       # Dependências Python
├── samconfig.toml         # Configurações de deploy
└── README.md             # Documentação
```

## ⚙️ Pré-requisitos

- Conta AWS ativa
- AWS CLI instalado
- AWS SAM CLI instalado
- Python 3.13 ou superior
- Git

## 🚀 Como Executar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/encurtador-url-serverless.git
cd encurtador-url-serverless
```

### 2. Configure suas credenciais AWS

```bash
aws configure
# AWS Access Key ID: [sua-chave]
# AWS Secret Access Key: [sua-secret]
# Default region name: us-east-2
# Default output format: json
```

### 3. Build da aplicação

```bash
sam build
```

### 4. Deploy na AWS

```bash
sam deploy --guided
```

**Configurações do deploy:**
- Stack name: `encurtador-url-serverless`
- Region: `us-east-2`
- Confirm changes: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

### 5. Anote a URL da API

Após o deploy, o SAM exibirá a URL da API:
```
https://xxxxxxxxxx.execute-api.us-east-2.amazonaws.com/Prod/
```

## 📡 Endpoints da API

### POST /encurtar
Encurta uma URL longa

**Request:**
```bash
curl -X POST https://sua-api.amazonaws.com/Prod/encurtar \
  -H "Content-Type: application/json" \
  -d '{"url": "https://exemplo.com/pagina-muito-longa"}'
```

**Response:**
```json
{
  "url_curta": "https://sua-api.amazonaws.com/Prod/aB92k"
}
```

### GET /{codigo}
Redireciona para a URL original

**Request:**
```bash
curl -L https://sua-api.amazonaws.com/Prod/aB92k
```

**Response:**
```
HTTP/1.1 301 Moved Permanently
Location: https://exemplo.com/pagina-muito-longa
```

## 🧪 Testes

### Teste Local (SAM Local)

```bash
# Iniciar API localmente
sam local start-api

# Testar endpoint em outro terminal
curl -X POST http://localhost:3000/encurtar \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Teste na AWS

```bash
# Definir URL da API
API_URL="https://xxxxxxxxxx.execute-api.us-east-2.amazonaws.com/Prod"

# Encurtar URL
curl -X POST $API_URL/encurtar \
  -H "Content-Type: application/json" \
  -d '{"url": "https://aws.amazon.com"}'

# Testar redirecionamento
curl -L $API_URL/codigo-retornado
```

## 📊 Código da Função Lambda

```python
import json
import boto3
import string
import random

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('URLs')

def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def lambda_handler(event, context):
    method = event['httpMethod']
    
    if method == 'POST':
        body = json.loads(event['body'])
        url_longa = body['url']
        codigo = generate_code()
        
        table.put_item(Item={
            'codigo': codigo,
            'url_original': url_longa
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'url_curta': f"https://api.url/{codigo}"
            })
        }
    
    elif method == 'GET':
        codigo = event['pathParameters']['codigo']
        response = table.get_item(Key={'codigo': codigo})
        
        if 'Item' in response:
            return {
                'statusCode': 301,
                'headers': {
                    'Location': response['Item']['url_original']
                }
            }
        
        return {
            'statusCode': 404,
            'body': 'URL não encontrada'
        }
```

## 💰 Custos Estimados

| Serviço | Free Tier | Custo após Free Tier |
|---------|-----------|---------------------|
| Lambda | 1M requisições/mês | $0.20 por 1M requisições |
| API Gateway | 1M requisições/mês | $3.50 por milhão |
| DynamoDB | 25 GB armazenamento | $0.25 por GB/mês |

**Estimativa para 10.000 requisições/mês:** Grátis (dentro do Free Tier)

## 🗑️ Remover a Aplicação

```bash
# Deletar a stack do CloudFormation
sam delete --stack-name encurtador-url-serverless

# Ou via AWS CLI
aws cloudformation delete-stack --stack-name encurtador-url-serverless
```

## 📈 Melhorias Futuras

- [ ] Interface web para encurtar URLs
- [ ] Autenticação de usuários
- [ ] Estatísticas de acessos
- [ ] URLs customizadas
- [ ] Expiração de links
- [ ] Cache com CloudFront
- [ ] Validação de URLs

## 👥 Equipe

Desenvolvido por:

- João Guilherme Gomes de Araújo (01710062)
- Ian Alves Pena (01704415)
- João Gabriel de Araújo Melo (01703004)
- Matheus Brayner Nascimento Canuto (01529738)
- Júlia Valença Florêncio (01758054)
- Matheus Santos de Oliveira (01712121)
- Marcos Adriano Da Silva Tavares (01708092)
- Luiz Henrique de Lima Bezerra (01705356)

## 📄 Licença

Projeto desenvolvido para fins acadêmicos - Disciplina de Cloud Computing

## 🔗 Links Úteis

- [Documentação AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [Documentação API Gateway](https://docs.aws.amazon.com/apigateway/)
- [Documentação DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)

---

⭐ **Se este projeto foi útil, deixe uma estrela!**
