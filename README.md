# AWS Pulse

**Serverless Availability & Performance Monitoring on AWS**

AWS Pulse é um projeto pessoal de monitoramento serverless desenvolvido na AWS para acompanhar a disponibilidade e a latência de aplicações e endpoints HTTP.

A solução executa verificações automáticas a cada 5 minutos, publica métricas customizadas no Amazon CloudWatch, exibe os resultados em dashboard e dispara alertas via Amazon SNS quando uma indisponibilidade é detectada.

> AWS Pulse é o nome deste projeto e não representa um serviço oficial da Amazon Web Services.

---

## Objetivo

Construir uma solução simples de observabilidade usando serviços gerenciados da AWS, sem depender de servidores dedicados para executar o monitoramento.

O projeto permite:

- Monitorar endpoints HTTP automaticamente
- Medir disponibilidade e latência
- Interpretar respostas HTTP e falhas de rede
- Registrar execuções em logs
- Publicar métricas customizadas
- Visualizar os dados em um dashboard
- Detectar indisponibilidade por meio de alarmes
- Enviar notificações por e-mail
- Simular falhas controladas para validar o fluxo completo

---

## Arquitetura

<!-- Adicione a imagem em: architecture/aws-pulse-architecture.png -->

<img width="892" height="508" alt="Projeto de monitoramento AWS drawio" src="https://github.com/user-attachments/assets/8391fabc-6569-44cc-9a68-e51a11fd757d" />

Região utilizada:

`us-east-2 - US East (Ohio)`

Fluxo principal:

```text
Amazon EventBridge Scheduler
            |
            v
    Lambda monitor-function
       /              \
      /                \
Google.com          Test API
                        |
                        v
                Lambda Function URL
            AWS Pulse Test API

            |
            v
     Amazon CloudWatch
    Metrics / Logs / Alarm
            |
            v
       Amazon SNS
            |
            v
          Email
```

---

## Como funciona

O Amazon EventBridge Scheduler executa automaticamente a função de monitoramento a cada 5 minutos.

Foram criados dois cronogramas independentes, ambos apontando para a mesma função Lambda `monitor-function`.

Google:

```json
{
  "target": "google"
}
```

AWS Pulse Test API:

```json
{
  "target": "api"
}
```

A Lambda identifica o valor de `target` e escolhe qual endpoint deve ser monitorado naquela execução.

---

## EventBridge Scheduler

Cronogramas configurados:

```text
aws-pulse-google-monitor
aws-pulse-api
```

Ambos executam:

```text
rate(5 minutes)
```

Assim, o monitoramento acontece automaticamente sem necessidade de executar a Lambda manualmente.

<!-- Adicione a imagem em: images/eventbridge.png -->

<img width="1917" height="787" alt="EventBridge" src="https://github.com/user-attachments/assets/4aa6b8c1-2e75-4be6-bf38-a2330bb105bd" />

---

## Lambda - monitor-function

Arquivo: [`src/monitor_function.py`](src/monitor_function.py)

A `monitor-function` é o componente principal do projeto. Ela é responsável por:

- Receber o target enviado pelo EventBridge
- Realizar uma requisição HTTP GET
- Medir o tempo de resposta
- Interpretar o código HTTP
- Classificar o serviço como disponível ou indisponível
- Registrar o resultado no CloudWatch Logs
- Publicar métricas customizadas no CloudWatch

O monitor utiliza `urllib`, `time`, `os` e `boto3`, evitando dependências externas para a requisição HTTP.

### Classificação das respostas

| Código / falha | Interpretação | Availability |
|---|---|---:|
| 2xx | ONLINE | 1 |
| 3xx | REDIRECT / disponível | 1 |
| 4xx | ERROR | 0 |
| 5xx | OFFLINE | 0 |
| Timeout / DNS / Network | OFFLINE | 0 |

A disponibilidade é representada numericamente:

```text
1 = Serviço disponível
0 = Serviço indisponível
```

---

## AWS Pulse Test API

Arquivo: [`src/test_api.py`](src/test_api.py)

Para realizar testes controlados de indisponibilidade, foi criada uma segunda função Lambda que atua como uma aplicação HTTP simples.

Ela possui uma Lambda Function URL e é utilizada exclusivamente como endpoint de testes do projeto.

<!-- Adicione a imagem em: images/test-api.png -->

<img width="906" height="238" alt="API - DOWN" src="https://github.com/user-attachments/assets/42b9c878-1e62-454f-9694-448c320f2802" />
<img width="906" height="238" alt="API - UP" src="https://github.com/user-attachments/assets/0fdcbc26-0da7-483b-810a-d80be48020ca" />
O comportamento é controlado pela variável de ambiente:

```text
API_STATUS
```

Quando:

```text
API_STATUS = UP
```

ela responde:

```text
HTTP 200
```

Quando:

```text
API_STATUS = DOWN
```

ela responde:

```text
HTTP 503
```

Isso permite validar o fluxo de detecção de falha sem depender da indisponibilidade real de um serviço externo.

---

## Amazon CloudWatch

O CloudWatch centraliza a observabilidade do projeto.

Namespace customizado:

```text
AWS-Pulse
```

Métricas publicadas:

```text
Availability
LatencyMs
```

Dimensão utilizada:

```text
ServiceName
```

Serviços monitorados atualmente:

```text
Google
AWS Pulse Test API
```

### Availability

```text
1 = UP
0 = DOWN
```

Essa métrica também é utilizada pelos CloudWatch Alarms.

### LatencyMs

Registra o tempo necessário para concluir a requisição HTTP, em milissegundos.

---

## CloudWatch Dashboard

O dashboard reúne a disponibilidade, latência e estado dos alarmes dos dois serviços monitorados.

<!-- Adicione a imagem em: images/dashboard.png -->
Dashboard - API DOWN
<img width="1890" height="1075" alt="Dashaborad-DOWN" src="https://github.com/user-attachments/assets/bb3bbf27-f576-441f-8e4d-ce35eb7fcb80" />
Dashboard - API UP
![AWS Pulse Dashboard](images/dashboard.png)

O painel apresenta:

- Disponibilidade do Google
- Latência do Google
- Disponibilidade da Test API
- Latência da Test API
- Estado dos CloudWatch Alarms
- Informações gerais do AWS Pulse

---

## CloudWatch Alarms

Alarmes configurados:

```text
AWS PULSE | GOOGLE AVAILABILITY
AWS PULSE | API AVAILABILITY
```

Condição principal:

```text
Availability < 1
```

Quando o valor passa de `1` para `0`, o estado do alarme muda de `OK` para `ALARM`.

<!-- Adicione a imagem em: images/alarm.png -->

![Uploading Alarm cloudwatch.png…]()

---

## Amazon SNS

Quando um CloudWatch Alarm detecta indisponibilidade, o Amazon SNS envia uma notificação por e-mail.

Tópico utilizado:

```text
aws-pulse-alerts
```

Fluxo:

```text
CloudWatch Metric
       |
       v
CloudWatch Alarm
       |
       v
    Amazon SNS
       |
       v
      Email
```

<!-- Adicione a imagem em: images/sns-email.png -->

<img width="1915" height="798" alt="Email via AWS SNS" src="https://github.com/user-attachments/assets/994aa49c-11bf-415b-b9e2-14d975f31027" />

---

## Teste de indisponibilidade

O teste principal do projeto utiliza a Test API para validar o fluxo de ponta a ponta.

Estado normal:

```text
API_STATUS = UP
HTTP 200
Availability = 1
Alarm = OK
```

Falha simulada:

```text
API_STATUS = DOWN
HTTP 503
```

A partir daí o fluxo ocorre automaticamente:

```text
Test API
   |
HTTP 503
   |
   v
EventBridge Scheduler
   |
   v
monitor-function
   |
   v
Availability = 0
   |
   v
CloudWatch
   |
   v
Alarm
   |
   v
SNS
   |
   v
Email
```

Após retornar `API_STATUS = UP`, o próximo ciclo automático detecta novamente o HTTP 200 e a métrica volta para `Availability = 1`.

---

## Serviços AWS utilizados

| Serviço | Função no projeto |
|---|---|
| Amazon EventBridge Scheduler | Execução automática dos monitores |
| AWS Lambda | Monitoramento e simulação da Test API |
| Lambda Function URL | Endpoint HTTP da API de testes |
| Amazon CloudWatch Logs | Registro das execuções |
| Amazon CloudWatch Metrics | Métricas de disponibilidade e latência |
| Amazon CloudWatch Dashboard | Visualização dos dados |
| Amazon CloudWatch Alarms | Detecção de indisponibilidade |
| Amazon SNS | Envio das notificações |
| AWS IAM | Controle de permissões entre serviços |

---

## IAM

A função principal precisa publicar métricas com:

```text
cloudwatch:PutMetricData
```

O EventBridge Scheduler utiliza uma execution role com permissão para:

```text
lambda:InvokeFunction
```

Nenhuma credencial AWS é armazenada no código-fonte.

---

## Estrutura do projeto

```text
aws-pulse/
├── README.md
├── src/
│   ├── monitor_function.py
│   └── test_api.py
├── architecture/
│   └── aws-pulse-architecture.png
└── images/
    ├── dashboard.png
    ├── test-api.png
    ├── eventbridge.png
    ├── alarm.png
    └── sns-email.png
```

---

## Melhorias futuras

- Adicionar novos endpoints por configuração dinâmica
- Criar thresholds de latência
- Adicionar alarmes específicos de performance
- Integrar notificações com Slack ou Microsoft Teams
- Criar histórico de incidentes e relatório de SLA
- Implementar infraestrutura como código com Terraform ou AWS SAM
- Criar pipeline CI/CD para atualização das funções Lambda

---

## Resultado

O AWS Pulse implementa um fluxo completo de observabilidade serverless na AWS, cobrindo monitoramento automático, métricas, dashboard, detecção de incidentes e notificação por e-mail.

O projeto demonstra na prática conceitos de:

```text
Cloud Computing
Serverless Architecture
Observability
Monitoring
Incident Detection
Automation
AWS IAM
HTTP
CloudWatch Metrics
CloudWatch Alarms
Event-driven Architecture
```

---

## AWS Pulse

**Serverless Availability & Performance Monitoring**

Built with AWS Lambda, Amazon EventBridge, Amazon CloudWatch and Amazon SNS.
