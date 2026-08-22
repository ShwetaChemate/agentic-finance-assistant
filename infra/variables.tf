variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Name prefix used for all resources (cluster, service, secret, etc.)"
  type        = string
  default     = "agentic-finance-assistant"
}

variable "container_image" {
  description = "Docker image to run, e.g. <account-id>.dkr.ecr.us-east-1.amazonaws.com/agentic-finance-assistant:latest"
  type        = string
}

variable "container_port" {
  description = "Port the FastAPI app listens on inside the container (matches Dockerfile's EXPOSE)"
  type        = number
  default     = 8000
}

variable "google_api_key" {
  description = "Gemini API key, stored in Secrets Manager rather than baked into the image or task definition"
  type        = string
  sensitive   = true
}

variable "desired_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 1
}
