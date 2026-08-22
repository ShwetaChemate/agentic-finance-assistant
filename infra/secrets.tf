# Holds the Gemini API key so it's injected into the running container at
# deploy time, never baked into the image or committed to the repo —
# the cloud equivalent of the local .env file.
resource "aws_secretsmanager_secret" "google_api_key" {
  name = "${var.app_name}/google-api-key"
}

resource "aws_secretsmanager_secret_version" "google_api_key" {
  secret_id     = aws_secretsmanager_secret.google_api_key.id
  secret_string = var.google_api_key
}
