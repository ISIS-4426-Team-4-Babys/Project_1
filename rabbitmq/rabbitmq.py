import aio_pika
import logging
import os


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class RabbitMQ:

    def __init__(self):
        self.user = os.getenv("RABBITMQ_USER")
        self.password = os.getenv("RABBITMQ_PASSWORD")
        self.host = os.getenv("RABBITMQ_HOST")
        self.port = int(os.getenv("RABBITMQ_PORT"))

        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None
        self.running = True


    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host = self.host,
            port = self.port,
            login = self.user,
            password = self.password,
            heartbeat = 60
        )
        self.channel = await self.connection.channel()
        logging.info("RabbitMQ connected (async)")


    async def close(self):
        self.running = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logging.info("RabbitMQ connection closed (async)")


    async def publish(self, queue_name: str, message: str):
        if not self.channel or self.channel.is_closed:
            await self.connect()
        
        queue = await self.channel.declare_queue(queue_name, durable = True)
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body = message.encode(),
                delivery_mode = aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key = queue.name
        )
        logging.info(f"Sent message to queue {queue_name}: {message}")


    async def consume(self, queue_name: str, callback):
        if not self.channel or self.channel.is_closed:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable = True)
        logging.info(f"[*] Waiting for messages in queue '{queue_name}'...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        await callback(message)
                    except Exception as e:
                        logging.error(f"Error processing message: {e}")
                        await message.nack(requeue = True)
