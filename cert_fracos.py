import ssl

# Criar um contexto SSL que permite certificados mais fracos
context = ssl.create_default_context()
context.set_ciphers('DEFAULT:@SECLEVEL=1')

# Configuração do produtor Kafka
producer = KafkaProducer(
    bootstrap_servers=['b-3.kafkauatdatamskcluste.n24vdd.c12.kafka.us-east-1.amazonaws.com:9094'],
    security_protocol="SSL",
    ssl_cafile="/caminho/correto/para/ca.crt",
    ssl_certfile="/caminho/correto/para/tls.crt",
    ssl_keyfile="/caminho/correto/para/tls.key",
    ssl_password=None,
    ssl_context=context,  # Usando o contexto SSL personalizado
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
