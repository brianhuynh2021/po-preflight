variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Resource name prefix"
  type        = string
  default     = "po-preflight"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "Existing EC2 key pair name"
  type        = string
  default     = "po-preflight-key"
}

variable "admin_cidr" {
  description = "CIDR allowed to use SSH and Web, for example 0.0.0.0/0 or specific IP"
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_rds" {
  description = "Flag to optionally provision managed RDS PostgreSQL database"
  type        = bool
  default     = false
}
