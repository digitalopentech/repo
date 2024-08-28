from kafka import KafkaProducer
import json

# Configuração do produtor Kafka
producer = KafkaProducer(
    bootstrap_servers=['b-3.kafkauatdatamskcluste.n24vdd.c12.kafka.us-east-1.amazonaws.com:9094'],  # Endereço do broker Kafka
    security_protocol="SSL",
    ssl_cafile="/etc/secrets/pinot/kafka-msk/keystore.jks",  # Caminho para o arquivo de keystore
    ssl_certfile="/etc/secrets/pinot/kafka-msk/keystore.jks",  # Caminho para o arquivo de keystore
    ssl_keyfile="/etc/secrets/pinot/kafka-msk/keystore.jks",  # Caminho para o arquivo de keystore
    ssl_password="QPdqEbaVt1781n0ra1GpYQ3og",  # Senha do keystore
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
