output "bucket" {
  value = aws_s3_bucket.raw.bucket
}


output "funcao" {
  value = aws_lambda_function.processador.function_name
}

output "topico_arn" {
  value = aws_sns_topic.alertas.arn
}
