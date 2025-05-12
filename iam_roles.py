import json
import pulumi
import pulumi_aws as aws

def create_roles_and_policies():
    role_name = "validation-service-role"

    validator_role = aws.iam.Role(
        "validation-service-role",
        name=role_name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }),
        # opts=pulumi.ResourceOptions(protect=True)
    )

    # Política associada ao Role
    aws.iam.RolePolicy(
        "image-validation-service-policy",
        role=validator_role.id,
        policy={
            "Version": "2012-10-17",
            "Statement": [
                # Permissões gerais para Lambda e serviços utilizados
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:*",
                        "dynamodb:*",               
                        "s3:*",                  # Leitura de arquivos no S3
                        "cloudwatch:*",
                        "secretsmanager:GetSecretValue", # Acesso a segredos
                        "iam:PassRole",                 # Lambda assume o Role
                        "iam:GetRole",
                        "tag:GetResources",
                        "lambda:*",
                        "kinesis:*",
                        "ec2:DescribeVpcs",
                        "ec2:DescribeSubnets",
                        "ec2:DescribeSecurityGroups",
                        "ec2:CreateNetworkInterface",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:DeleteNetworkInterface"

                    ],
                    "Resource": "*"
                },
                # Permissão para criar grupos de logs no CloudWatch
                {
                    "Effect": "Allow",
                    "Action": "logs:CreateLogGroup",
                    "Resource": "arn:aws:logs:us-east-1:777825471459:*"
                },
                # Permissão para criar streams de log e enviar eventos
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:logs:us-east-1:777825471459:log-group:/aws/lambda/ValidationLambda:*"
                    ]
                },
                # Permissão explícita para a Lambda assumir o Role
                {
                    "Effect": "Allow",
                    "Action": "iam:PassRole",
                    "Resource": validator_role.arn
                }
            ]
        },
        # opts=pulumi.ResourceOptions(protect=True)
    )

    return validator_role

