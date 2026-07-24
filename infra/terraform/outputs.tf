output "public_ip" {
  description = "EC2 public IP for initial SSH setup"
  value       = aws_instance.orderflow.public_ip
}

output "ssh_command" {
  description = "Initial SSH command"
  value       = "ssh ubuntu@${aws_instance.orderflow.public_ip}"
}
