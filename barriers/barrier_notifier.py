import threading
import logging
import json 
import pika
import os

logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")

class BarrierNotifier:

    def __init__(self, agent_id: str, total_docs: int, ):
        # Manejar conexion
        self.user = os.getenv('RABBITMQ_USER')
        self.password = os.getenv('RABBITMQ_PASSWORD')
        self.host = os.getenv('RABBITMQ_HOST')
        self.port = int(os.getenv('RABBITMQ_PORT'))
        self.connection = None
        self.channel = None

        # Control de la barrera
        self.agent_id = agent_id
        self.total_docs = total_docs
        self.counter = 0
    
    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(host = self.host, port = self.port, credentials = credentials, heartbeat = 600, blocked_connection_timeout = 300)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
    
    def declare_barrier(self):

        assert self.channel is not None
        self.channel.queue_declare(
            queue = self.agent_id,
            durable = True,
            auto_delete = False,
            #arguments = {
            #    "x-single-active-consumer": True
            #}
        ) 

        logging.info("Barrier declared with name = %s", self.agent_id)
    
    def declare_control_exchange(self):

        assert self.channel is not None
        self.channel.exchange_declare(exchange = "control", exchange_type = "topic", durable = True)

        logging.info("Control exchange declared succesfully")

    def on_tick(self, ch, method, properties, body):

        try:
            self.counter += 1
            logging.info("On tick barrier %s / %d", self.agent_id, self.counter)
            ch.basic_ack(method.delivery_tag)

            if self.counter == self.total_docs:

                evt = {
                    "event": "completed",
                    "agent_id": self.agent_id,
                }

                self.channel.queue_declare(queue = "deploy", durable = True)
                self.channel.basic_publish(
                    exchange = '',
                    routing_key = "deploy",
                    body = json.dumps(evt).encode("utf-8"),
                    properties = pika.BasicProperties(
                        delivery_mode = 2  
                    )
                )
                logging.info("Completed message published agent %s", self.agent_id)

                ch.stop_consuming()

        except Exception as e:
            logging.exception("Notifier error in _on_tick: %s", e)

    def run(self):
        try:
            self.connect()
            self.declare_control_exchange()
            self.declare_barrier()

            self.channel.basic_qos(prefetch_count = 128)
            self.channel.basic_consume(queue = self.agent_id, on_message_callback = self.on_tick, auto_ack = False)
            self.channel.start_consuming()
        
        finally:
            self.close()
            self.channel.queue_delete(queue = self.agent_id)
    
    def start_in_thread(self):

        thread = threading.Thread(target = self.run, name = self.agent_id, daemon = True)
        thread.start()
        return  thread



