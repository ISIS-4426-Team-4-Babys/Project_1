from rabbitmq import RabbitMQ   
import logging
import os


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
rabbitmq = RabbitMQ()

def callback(ch, method, properties, body):
    decoded_message = body.decode().strip()
    logging.info(f"Message received with content = {body}")

rabbitmq.consume("deploy", callback)