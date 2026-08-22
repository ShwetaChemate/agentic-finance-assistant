output "api_gateway_url" {
  description = "Public URL for the API — e.g. <this>/analyze-portfolio"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "alb_dns_name" {
  description = "ALB's own DNS name, useful for debugging directly (bypassing API Gateway)"
  value       = aws_lb.app.dns_name
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "ecr_repository_url" {
  description = "Push the built image here, e.g. docker push <this>:latest"
  value       = aws_ecr_repository.app.repository_url
}
