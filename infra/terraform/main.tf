terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "eduforge-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "ap-south-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ─── VPC ────────────────────────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "eduforge-vpc" }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  tags              = { Name = "eduforge-private-a" }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  tags              = { Name = "eduforge-private-b" }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.10.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags                    = { Name = "eduforge-public-a" }
}

# ─── RDS PostgreSQL 16 ──────────────────────────────────────────────
resource "aws_db_subnet_group" "main" {
  name       = "eduforge-db"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

resource "aws_db_instance" "postgres" {
  identifier             = "eduforge-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  max_allocated_storage  = 100
  db_name                = "eduforge"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = false
  backup_retention_period = 7
  multi_az               = false
  storage_encrypted      = true

  tags = { Name = "eduforge-postgres" }
}

resource "aws_security_group" "db" {
  name   = "eduforge-db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id, aws_security_group.ecs.id]
  }
}

# ─── ECR Repositories ───────────────────────────────────────────────
resource "aws_ecr_repository" "services" {
  for_each = toset(["identity", "portal", "exam", "notification", "billing", "ai", "analytics"])

  name                 = "eduforge-${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ─── Lambda Functions ────────────────────────────────────────────────
resource "aws_security_group" "lambda" {
  name   = "eduforge-lambda-sg"
  vpc_id = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "lambda" {
  name = "eduforge-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_sqs" {
  name = "eduforge-lambda-sqs"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
      Resource = "arn:aws:sqs:${var.aws_region}:*:eduforge-*"
    }]
  })
}

resource "aws_lambda_function" "services" {
  for_each = toset(["identity", "exam", "notification", "billing", "ai", "analytics"])

  function_name = "eduforge-${each.key}"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.services[each.key].repository_url}:latest"
  timeout       = 30
  memory_size   = 256

  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DATABASE_URL   = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/eduforge"
      JWT_SECRET_KEY = var.jwt_secret_key
    }
  }
}

# ─── ECS Fargate (Portal) ───────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "eduforge"
}

resource "aws_security_group" "ecs" {
  name   = "eduforge-ecs-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 8002
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "ecs_task" {
  name = "eduforge-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_ecs_task_definition" "portal" {
  family                   = "eduforge-portal"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "portal"
    image = "${aws_ecr_repository.services["portal"].repository_url}:latest"
    portMappings = [{ containerPort = 8002, protocol = "tcp" }]
    environment = [
      { name = "DATABASE_URL", value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/eduforge" },
      { name = "JWT_SECRET_KEY", value = var.jwt_secret_key },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/eduforge-portal"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "portal"
      }
    }
  }])
}

resource "aws_ecs_service" "portal" {
  name            = "eduforge-portal"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.portal.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
}

# ─── SQS Queues ─────────────────────────────────────────────────────
resource "aws_sqs_queue" "scoring" {
  name                       = "eduforge-scoring"
  message_retention_seconds  = 86400
  visibility_timeout_seconds = 300
}

resource "aws_sqs_queue" "notifications" {
  name                       = "eduforge-notifications"
  message_retention_seconds  = 86400
  visibility_timeout_seconds = 60
}

resource "aws_sqs_queue" "analytics" {
  name                       = "eduforge-analytics"
  message_retention_seconds  = 86400
  visibility_timeout_seconds = 120
}

# ─── API Gateway ─────────────────────────────────────────────────────
resource "aws_apigatewayv2_api" "main" {
  name          = "eduforge-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = true
}

# ─── EventBridge (Nightly Jobs) ──────────────────────────────────────
resource "aws_cloudwatch_event_rule" "nightly_cleanup" {
  name                = "eduforge-nightly-cleanup"
  description         = "Runs nightly at 2 AM IST (8:30 PM UTC)"
  schedule_expression = "cron(30 20 * * ? *)"
}

resource "aws_cloudwatch_event_rule" "nightly_ranks" {
  name                = "eduforge-nightly-ranks"
  description         = "Compute All India Ranks nightly at 3 AM IST"
  schedule_expression = "cron(30 21 * * ? *)"
}

resource "aws_cloudwatch_event_target" "nightly_cleanup_target" {
  rule      = aws_cloudwatch_event_rule.nightly_cleanup.name
  target_id = "eduforge-exam-cleanup"
  arn       = aws_lambda_function.services["exam"].arn
  input     = jsonencode({ action = "nightly_cleanup" })
}

resource "aws_lambda_permission" "allow_eventbridge_cleanup" {
  statement_id  = "AllowEventBridgeCleanup"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.services["exam"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.nightly_cleanup.arn
}

resource "aws_cloudwatch_event_target" "nightly_ranks_target" {
  rule      = aws_cloudwatch_event_rule.nightly_ranks.name
  target_id = "eduforge-analytics-ranks"
  arn       = aws_lambda_function.services["analytics"].arn
  input     = jsonencode({ action = "compute_ranks" })
}

resource "aws_lambda_permission" "allow_eventbridge_ranks" {
  statement_id  = "AllowEventBridgeRanks"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.services["analytics"].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.nightly_ranks.arn
}

# ─── API Gateway Integrations ──────────────────────────────────────
resource "aws_apigatewayv2_integration" "lambda" {
  for_each = aws_lambda_function.services

  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "lambda" {
  for_each = aws_lambda_function.services

  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /${each.key}/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_lambda_permission" "apigw" {
  for_each = aws_lambda_function.services

  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = each.value.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# ─── CloudWatch Log Groups ─────────────────────────────────────────
resource "aws_cloudwatch_log_group" "portal" {
  name              = "/ecs/eduforge-portal"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each = toset(["identity", "exam", "notification", "billing", "ai", "analytics"])

  name              = "/aws/lambda/eduforge-${each.key}"
  retention_in_days = 30
}
