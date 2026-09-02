provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "preflight" {
  name        = "${var.project_name}-sg"
  description = "Security Group for PO Preflight Web Gateway and SSH"

  ingress {
    description = "SSH administration"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  ingress {
    description = "HTTP API & Web Traffic"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  ingress {
    description = "Web Frontend Traffic"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-sg"
    Project = var.project_name
  }
}

# Private S3 Bucket for Uploads (Encrypted with SSE-S3)
resource "aws_s3_bucket" "uploads" {
  bucket        = "${var.project_name}-uploads-${var.aws_region}"
  force_destroy = false

  tags = {
    Name    = "${var.project_name}-uploads"
    Project = var.project_name
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Secrets Manager for Environment Secrets
resource "aws_secretsmanager_secret" "env_secret" {
  name                    = "${var.project_name}-env-secrets"
  recovery_window_in_days = 0

  tags = {
    Name    = "${var.project_name}-secrets"
    Project = var.project_name
  }
}

# Optional Managed RDS PostgreSQL Database
resource "aws_db_instance" "postgres" {
  count                  = var.enable_rds ? 1 : 0
  identifier             = "${var.project_name}-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.micro"
  db_name                = "preflight"
  username               = "preflight_admin"
  password               = "ChangeMeInProductionSecret123!"
  skip_final_snapshot    = true
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.preflight.id]

  tags = {
    Name    = "${var.project_name}-db"
    Project = var.project_name
  }
}

resource "aws_instance" "preflight" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.preflight.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io docker-compose-v2
              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu
              EOF

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = 30
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name    = var.project_name
    Project = var.project_name
  }
}
