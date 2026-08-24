import urllib.request
import urllib.error
import time
import os
import boto3

cloudwatch = boto3.client("cloudwatch")

TARGETS = {
    "google": {
        "name": "Google",
        "url": "https://www.google.com"
    },
    "api": {
        "name": "AWS Pulse Test API",
        "url": os.environ.get("TEST_API_URL")
    }
}


def enviar_metricas(nome, disponibilidade, latencia):
    cloudwatch.put_metric_data(
        Namespace="AWS-Pulse",
        MetricData=[
            {
                "MetricName": "Availability",
                "Dimensions": [
                    {"Name": "ServiceName", "Value": nome}
                ],
                "Value": disponibilidade,
                "Unit": "Count"
            },
            {
                "MetricName": "LatencyMs",
                "Dimensions": [
                    {"Name": "ServiceName", "Value": nome}
                ],
                "Value": latencia,
                "Unit": "Milliseconds"
            }
        ]
    )


def lambda_handler(event, context):
    target = event.get("target")

    if target not in TARGETS:
        return {
            "status": "CONFIG_ERROR",
            "erro": "Target inválido. Utilize 'google' ou 'api'."
        }

    nome = TARGETS[target]["name"]
    url = TARGETS[target]["url"]

    if not url:
        return {
            "status": "CONFIG_ERROR",
            "erro": f"URL do serviço {nome} não configurada."
        }

    inicio = time.perf_counter()

    try:
        requisicao = urllib.request.Request(
            url,
            headers={"User-Agent": "AWS-Pulse-Monitor/1.0"}
        )

        resposta = urllib.request.urlopen(
            requisicao,
            timeout=5
        )

        status_code = resposta.getcode()
        latencia = round((time.perf_counter() - inicio) * 1000, 2)

        if 200 <= status_code < 300:
            status = "ONLINE"
            disponibilidade = 1
        elif 300 <= status_code < 400:
            status = "REDIRECT"
            disponibilidade = 1
        else:
            status = "UNKNOWN"
            disponibilidade = 0

        resultado = {
            "service": nome,
            "target": target,
            "status": status,
            "availability": disponibilidade,
            "http_status": status_code,
            "latencia_ms": latencia,
            "url": url
        }

        print(resultado)
        enviar_metricas(nome, disponibilidade, latencia)
        return resultado

    except urllib.error.HTTPError as erro:
        latencia = round((time.perf_counter() - inicio) * 1000, 2)

        if 400 <= erro.code < 500:
            status = "ERROR"
        elif 500 <= erro.code < 600:
            status = "OFFLINE"
        else:
            status = "UNKNOWN"

        disponibilidade = 0

        resultado = {
            "service": nome,
            "target": target,
            "status": status,
            "availability": disponibilidade,
            "http_status": erro.code,
            "latencia_ms": latencia,
            "url": url
        }

        print(resultado)
        enviar_metricas(nome, disponibilidade, latencia)
        return resultado

    except Exception as erro:
        latencia = round((time.perf_counter() - inicio) * 1000, 2)
        disponibilidade = 0

        resultado = {
            "service": nome,
            "target": target,
            "status": "OFFLINE",
            "availability": disponibilidade,
            "http_status": 0,
            "latencia_ms": latencia,
            "erro": str(erro),
            "url": url
        }

        print(resultado)
        enviar_metricas(nome, disponibilidade, latencia)
        return resultado
