# HTTP API (cheaper/simpler than REST API) sitting in front of the ALB.
# Since the ALB is already public, this uses a direct INTERNET connection
# rather than a VPC Link — API Gateway's value here is a stable public URL,
# request throttling, and a natural place to add auth/custom domains later.
resource "aws_apigatewayv2_api" "http_api" {
  name          = var.app_name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "alb" {
  api_id             = aws_apigatewayv2_api.http_api.id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = "http://${aws_lb.app.dns_name}"
  connection_type    = "INTERNET"
}

# Catches every path/method and forwards to the ALB unchanged — the FastAPI
# app's own routing (e.g. /analyze-portfolio, /docs) decides what to do with it.
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.alb.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}
