from kafka import KafkaProducer
import json

# Configuração do produtor Kafka
producer = KafkaProducer(
    bootstrap_servers=['b-3.kafkauatdatamskcluste.n24vdd.c12.kafka.us-east-1.amazonaws.com:9094'],  # Endereço do broker Kafka
    security_protocol="SSL",
    ssl_cafile="/caminho/para/ca.crt",  # Caminho para o certificado da CA
    ssl_certfile="/caminho/para/tls.crt",  # Caminho para o certificado do cliente
    ssl_keyfile="/caminho/para/tls.key",  # Caminho para a chave privada do cliente
    ssl_password=None,  # Caso a chave privada esteja sem senha, use None
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serializador de mensagens JSON
)

# Dados a serem publicados no tópico
message = {
    "example_key": "example_value",
    "another_key": 1234
}

# Publica a mensagem no tópico
producer.send('GRMKT-UAT-LOG-STREAMING-GEOLOCATION', value=message)

# Certifica-se de que todas as mensagens foram enviadas
producer.flush()

# Fecha o produtor Kafka
producer.close()

print("Mensagem publicada com sucesso!")
