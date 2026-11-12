resource "aws_sns_topic_subscription" "lambda_sub" {
  topic_arn = aws_sns_topic.alertas.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.processador.arn
}

resource "aws_lambda_permission" "sns_invoke" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processador.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alertas.arn
}
