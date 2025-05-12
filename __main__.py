import json
import pulumi
import pulumi_aws as aws
import pulumi_aws_apigateway as apigateway
from iam_roles import create_roles_and_policies
import uuid

# =======================
# Configurações do Pulumi
# =======================
config = pulumi.Config('indecx-infra')

# Configurações de Rede
VPC_ID = config.require('vpcId')
SUBNET_IDS = config.require_object('subnetIds')
ALLOWED_SG_IDS = config.require_object('allowedSecurityGroupIds')

# Configurações da Lambda
lambda_config = config.require_object('lambdaConfig')
LAMBDA_IMAGE_URI = lambda_config['imageUri']
LAMBDA_TIMEOUT = lambda_config['timeout']
LAMBDA_MEMORY_SIZE = lambda_config['memorySize']

# Configurações do Qdrant
qdrant_config = config.require_object('qdrantConfig')
QDRANT_HOST = qdrant_config['host']
QDRANT_API_KEY = qdrant_config['apiKey']

# Configurações do API Gateway
api_gw_config = config.require_object('apiGatewayConfig')
API_NAME = api_gw_config['name']
API_DESCRIPTION = api_gw_config['description']
API_STAGE_NAME = api_gw_config['stageName']

# -----------------------
# IAM: Papéis e Políticas
# -----------------------
validator_role = create_roles_and_policies()

aws.iam.RolePolicyAttachment(
    "lambda_basic_execution_job_scheduler",
    role=validator_role.name,
    policy_arn=aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE,
)

lambda_sg = aws.ec2.SecurityGroup(
    "lambdaSecurityGroup",
    description="Temporary marker to retain",
    vpc_id=VPC_ID,
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
)


# =======================
# Função Lambda
# =======================
lambda_rag = aws.lambda_.Function(
    "ragFastApiLambda",
    package_type="Image",
    image_uri=LAMBDA_IMAGE_URI,
    role=validator_role.arn,
    timeout=LAMBDA_TIMEOUT,
    memory_size=LAMBDA_MEMORY_SIZE,
    environment={
        "variables": {
            "QDRANT_HOST": QDRANT_HOST,
            "QDRANT_API_KEY": QDRANT_API_KEY,
            "QDRANT_COLLECTION": ""
        }
    },
    vpc_config={
        "subnet_ids": SUBNET_IDS,
        "security_group_ids": ALLOWED_SG_IDS
    },
)

# =======================
# Permissões para API Gateway
# =======================
lambda_permission_api_gateway = aws.lambda_.Permission(
    "allow_apigateway_to_invoke_lambda",
    action="lambda:InvokeFunction",
    function=lambda_rag.arn,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.format("arn:aws:execute-api:{0}:{1}:*/*/*/*", 
                                  aws.get_region().name,
                                  aws.get_caller_identity().account_id)
)

# =======================
# API Gateway
# =======================
api = aws.apigateway.RestApi(
    "ragApi",
    name=API_NAME,
    description=API_DESCRIPTION,
    endpoint_configuration={"types": "REGIONAL"}
)

proxy_resource = aws.apigateway.Resource(
    "ProxyResource",
    rest_api=api.id,
    parent_id=api.root_resource_id,
    path_part="{proxy+}"
)

proxy_method = aws.apigateway.Method(
    "ProxyMethod",
    rest_api=api.id,
    resource_id=proxy_resource.id,
    http_method="ANY",
    authorization="NONE"
)

proxy_integration = aws.apigateway.Integration(
    "LambdaProxyIntegration",
    rest_api=api.id,
    resource_id=proxy_resource.id,
    http_method=proxy_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=lambda_rag.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[proxy_method])
)

root_method = aws.apigateway.Method(
    "RootMethod",
    rest_api=api.id,
    resource_id=api.root_resource_id,
    http_method="ANY",
    authorization="NONE"
)

root_integration = aws.apigateway.Integration(
    "RootLambdaIntegration",
    rest_api=api.id,
    resource_id=api.root_resource_id,
    http_method=root_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=lambda_rag.invoke_arn,
    opts=pulumi.ResourceOptions(depends_on=[root_method])
)

deployment = aws.apigateway.Deployment(
    "ApiDeployment",
    rest_api=api.id,
    opts=pulumi.ResourceOptions(depends_on=[proxy_integration, root_integration])
)

stage = aws.apigateway.Stage(
    "ProdStage",
    rest_api=api.id,
    deployment=deployment.id,
    stage_name=API_STAGE_NAME
)

# =======================
# Outputs
# =======================
pulumi.export("api_url", stage.invoke_url.apply(lambda url: f"{url}"))
pulumi.export("lambda_arn", lambda_rag.arn)
pulumi.export("lambda_sg_id", "N/A - using existing SGs")
