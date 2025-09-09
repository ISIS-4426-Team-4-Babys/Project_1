from barrier_notifier import BarrierNotifier
from rabbitmq import RabbitMQ
import logging
import json

logging.basicConfig(level = logging.INFO, format = "%(asctime)s [%(levelname)s] %(message)s")
rabbitmq = RabbitMQ()

received_agents = set()

def callback(ch, methos, properties, body):
    decoded_message = body.decode().strip()
    logging.info(f"Message received {decoded_message}")

    payload = json.loads(decoded_message)
    agent_id = payload.get("agent_id")
    total_docs = payload.get("total_docs")

    if not agent_id or not total_docs:
        logging.error("Invalid message: 'agent_id' or 'total_docs' missing")
        return

    logging.info(f"Agent ID received: {agent_id}")
    logging.info(f"Total documents received: {total_docs}")

    if agent_id not in received_agents:
        logging.info(f"Creating barrier notifier for agent: {agent_id}")
        BarrierNotifier(agent_id, total_docs).start_in_thread()
        logging.info(f"Barrier notifier created for agent: {agent_id}")
        received_agents.add(agent_id)

    rabbitmq.publish(agent_id, "Document Vectorized")

rabbitmq.consume("control", callback)
