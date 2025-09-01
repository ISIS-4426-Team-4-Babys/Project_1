import logging
from rabbitmq import RabbitMQ

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def callback(ch, method, properties, body):
    logging.info(f"Received {body}")
    decoded = body.decode().strip()
    logging.info(f"Decoded {decoded}")

rabbitmq = RabbitMQ()
rabbitmq.consume("files", callback)
