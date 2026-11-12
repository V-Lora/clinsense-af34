output "bucket" {
  value = aws_s3_bucket.raw.bucket
}

output "tabela" {
  value = aws_dynamodb_table.leituras.name
}

output "funcao" {
  value = aws_lambda_function.processador.function_name
}

output "topico_arn" {
  value = aws_sns_topic.alertas.arn
}
