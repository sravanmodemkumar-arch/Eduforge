output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value       = { for k, v in aws_ecr_repository.services : k => v.repository_url }
}

output "sqs_scoring_queue_url" {
  description = "SQS scoring queue URL"
  value       = aws_sqs_queue.scoring.url
}

output "sqs_notifications_queue_url" {
  description = "SQS notifications queue URL"
  value       = aws_sqs_queue.notifications.url
}

output "sqs_analytics_queue_url" {
  description = "SQS analytics queue URL"
  value       = aws_sqs_queue.analytics.url
}
