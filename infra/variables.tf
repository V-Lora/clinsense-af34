variable "aws_region" {
  default = "us-east-1"
}

variable "localstack_endpoint" {
  default = "http://localhost:4566"
}

variable "project" {
  default = "clinsense"
}

variable "bucket_name" {
  default = "clinsense-raw"
}


variable "topic_name" {
  default = "clinsense-alertas"
}
