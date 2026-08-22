# Use the account's default VPC/subnets rather than provisioning a new network —
# keeps this skeleton focused on the app's own infrastructure (ECS, secrets,
# API Gateway) instead of reimplementing basic networking.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
