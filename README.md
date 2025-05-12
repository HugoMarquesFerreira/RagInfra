# Projeto de Infraestrutura - RAG com Pulumi + AWS

Este projeto provisiona a infraestrutura necessária para executar uma API baseada em AWS Lambda com Docker (imageUri), exposta por API Gateway e integrada ao banco vetorial Qdrant.

---

## ✅ Pré-requisitos

- [Pulumi CLI](https://www.pulumi.com/docs/install/) instalado
- Conta AWS com credenciais configuradas (`aws configure`)
- Acesso ao repositório ECR com a imagem da Lambda
- Login no Pulumi:  
  ```bash
  pulumi login
  ```

---

## 📁 Estrutura do Projeto

- `main.py` → Código principal da stack Pulumi
- `pulumi.dev.yaml` → Arquivo de configuração da stack `dev` com parâmetros customizáveis

---

## 🚀 Como executar

1. Faça login no Pulumi:
   ```bash
   pulumi login
   ```

2. Instale as dependências (se aplicável):
   ```bash
   pip install -r requirements.txt
   ```

3. Configure a stack `dev`:
   ```bash
   pulumi stack select dev
   ```

4. Faça o deploy:
   ```bash
   pulumi up
   ```

---

## 🛠️ Personalização via `pulumi.dev.yaml`

Você pode alterar as configurações diretamente no `pulumi.dev.yaml`. Abaixo as principais chaves:

```yaml
aws:region: us-east-1                # Região da AWS
account_id:           # ID da conta AWS
indecx-infra:vpcId: "vpc-..."       # VPC onde a Lambda será criada
indecx-infra:subnetIds:             # Subnets privadas da VPC
  - "subnet-..."                    
indecx-infra:allowedSecurityGroupIds:  # SGs com permissão para chamar a Lambda
  - "sg-..."

indecx-infra:lambdaConfig:
  imageUri: "<URI da imagem no ECR>"   # Imagem da Lambda
  timeout: 900                         # Timeout (segundos)
  memorySize: 512                      # Memória (MB)

indecx-infra:qdrantConfig:
  host: "http://<host>:<porta>"        # Endpoint do Qdrant
  apiKey: "<sua-chave-de-api>"

indecx-infra:apiGatewayConfig:
  name: "rag-api"                      # Nome da API Gateway
  description: "RAG API Gateway"
  stageName: "prod"                    # Nome do stage (ex: prod/dev)
```

---

## 📦 Outputs

Após o deploy, os seguintes dados são exportados:

- `api_url`: URL pública da API Gateway
- `lambda_arn`: ARN da função Lambda
- `lambda_sg_id`: ID do Security Group da Lambda

---

## 🧹 Remover a infraestrutura

Caso queira destruir todos os recursos provisionados:
```bash
pulumi destroy
```

---

## 📬 Suporte

Dúvidas ou sugestões? Abra um issue ou fale com o responsável pelo projeto.