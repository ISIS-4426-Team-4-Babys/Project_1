import pika
import os

class RabbitMQ:

    def __init__(self):
        self.user = os.getenv('RABBITMQ_USER')
        self.password = os.getenv('RABBITMQ_PASSWORD')
        self.host = os.getenv('RABBITMQ_HOST')
        self.port = int(os.getenv('RABBITMQ_PORT'))
        self.connection = None
        self.channel = None
        self.connect()


    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(host = self.host, port = self.port, credentials = credentials, heartbeat = 600, blocked_connection_timeout = 300)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
    

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()


    def consume(self, queue_name, callback):
        if not self.channel:
            raise Exception("Connection is not established.")
        # Crear la cola si no existe
        self.channel.queue_declare(queue = queue_name, durable = True)
        self.channel.basic_consume(
            queue = queue_name,
            on_message_callback = callback,
            auto_ack = True
        )
        print(f" [*] Esperando mensajes en la cola '{queue_name}'...")
        self.channel.start_consuming()
    

    def publish(self, queue_name, message):
        if not self.channel:
            raise Exception("Connection is not established.")
        self.channel.queue_declare(queue = queue_name, durable = True)
        self.channel.basic_publish(exchange = '',
                                   routing_key = queue_name,
                                   body = message,
                                   properties = pika.BasicProperties(
                                       delivery_mode = 2, 
                                   ))
        print(f"Sent message to queue {queue_name}: {message}")