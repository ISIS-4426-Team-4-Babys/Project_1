from aio_pika import connect_robust, Message, ExchangeType
import logging
import asyncio
import json
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BarrierNotifier:

    def __init__(self, agent_id: str, total_docs: int):
        self.agent_id = agent_id
        self.total_docs = total_docs
        self.counter = 0
        self.connection = None
        self.channel = None
        self.queue = None
        self.completed = asyncio.Event()

        self.user = os.getenv('RABBITMQ_USER')
        self.password = os.getenv('RABBITMQ_PASSWORD')
        self.host = os.getenv('RABBITMQ_HOST')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))

    async def connect(self):
        self.connection = await connect_robust(
            host = self.host,
            port = self.port,
            login = self.user,
            password = self.password,
            heartbeat = 60,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count = 128)
        logging.info("BarrierNotifier connected to RabbitMQ")

    async def declare_barrier(self):
        self.queue = await self.channel.declare_queue(
            self.agent_id,
            durable = True,
            auto_delete = False
        )
        logging.info("Barrier declared with name = %s", self.agent_id)

    async def declare_control_exchange(self):
        self.exchange = await self.channel.declare_exchange(
            "control",
            ExchangeType.TOPIC,
            durable = True
        )
        logging.info("Control exchange declared successfully")

    async def on_tick(self, message):
        async with message.process():
            try:
                self.counter += 1
                logging.info("On tick barrier %s / %d", self.agent_id, self.counter)

                if self.counter == self.total_docs:
                    evt = {
                        "event": "completed",
                        "agent_id": self.agent_id,
                    }

                    await self.channel.default_exchange.publish(
                        Message(body=json.dumps(evt).encode("utf-8")),
                        routing_key="deploy"
                    )

                    logging.info("Completed message published agent %s", self.agent_id)
                    
                    self.completed.set()

            except Exception as e:
                logging.exception("Notifier error in _on_tick: %s", e)

    async def run(self):
        await self.connect()
        await self.declare_control_exchange()
        await self.declare_barrier()
        self.consumer_tag = await self.queue.consume(self.on_tick)
        logging.info(f"BarrierNotifier running for agent {self.agent_id}")
        
        await self.completed.wait()
        
        try:
            if self.consumer_tag:
                await self.queue.cancel(self.consumer_tag)
        except Exception as e:
            logging.warning("Failed to cancel consumer: %s", e)

        try:
            await self.queue.delete(if_unused=False, if_empty=False)
            logging.info("Queue %s deleted", self.agent_id)
        except Exception as e:
            logging.warning("Failed to delete queue: %s", e)

        try:
            await self.channel.close()
            await self.connection.close()
        except Exception as e:
            logging.warning("Failed to close the connection: %s", e)


        logging.info("BarrierNotifier closed for agent %s", self.agent_id)

