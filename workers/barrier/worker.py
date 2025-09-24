from barrier_notifier import BarrierNotifier
from rabbitmq import RabbitMQ
import logging
import json
import asyncio

logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")
rabbitmq = RabbitMQ()

notifiers = {}

async def callback(message):
    try:
        decoded_message = message.body.decode().strip()
        logging.info(f"Message received {decoded_message}")

        payload = json.loads(decoded_message)
        agent_id = payload.get("agent_id")
        total_docs = payload.get("total_docs")

        if not agent_id or not total_docs:
            logging.error("Invalid message: 'agent_id' or 'total_docs' missing")
            return

        logging.info(f"Agent ID received: {agent_id}")
        logging.info(f"Total documents received: {total_docs}")

        if agent_id not in notifiers or notifiers[agent_id].done():
            logging.info(f"Spawning BarrierNotifier for agent: {agent_id}")
            notifiers[agent_id] = asyncio.create_task(
                BarrierNotifier(agent_id, total_docs).run()
            )

        await rabbitmq.publish(agent_id, "Document Vectorized")
        
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        

async def main():
    await rabbitmq.consume("control", callback)


if __name__ == "__main__":
    asyncio.run(main())
