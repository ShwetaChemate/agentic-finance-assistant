# Hosts the Docker image ECS pulls from. Created separately from pushing the
# image itself — Terraform manages the repository, but `docker push` is a
# manual step outside Terraform (Terraform doesn't build/push images).
resource "aws_ecr_repository" "app" {
  name                 = var.app_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
