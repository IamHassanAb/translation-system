import logging
from threading import Event
import time
import json
import requests
import redis
import pika
from typing import Dict
from queue import Queue
# import asyncio
from core.config import settings
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessResponseService:
    def __init__(self) -> None:
        self.translation_response_queue = Queue()
        self.stop_event = Event()
        self.request = {}
        self.response = {}
        logger.info("Initializing response service")
        self.setup_rabbitmq()
        # self.setup_redis() #NOT USING REDIS FOR THE TIME BEING
    


    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel."""
        try:
            logger.info("Setting up RabbitMQ connection")
            self.connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)
            logger.info("RabbitMQ setup completed")
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ: {e}")
            raise

    def consume(self):
        """
        Consume messages from the RabbitMQ translation queue.
        When a message is received from translation, it given as a status response to the user.
        """
        while not self.stop_event.is_set():
            try:
                def callback(ch, method, properties, body):
                    logger.info(f"Received message from translation queue: {body}")
                    try:
                        # Assuming the body is a JSON-encoded string
                        request_data = json.loads(body.decode())
                        self.translation_response_queue.put(request_data)
                        logger.info(f"Message added to the translation queue: {request_data}")
                    except Exception as e:
                        logger.error(f"Error adding  message: {e}")
                        # ch.basic_ack(delivery_tag=method.delivery_tag)
                        raise
                    finally:
                        logger.info("Status message produced successfully")
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                try:
                    logger.info("Starting Translation Consumer...")
                    # Note: Using auto_ack=False to ensure messages are acknowledged after processing.
                    self.channel.basic_consume(queue=settings.TRANSLATION_QUEUE, 
                                               on_message_callback=callback, 
                                               auto_ack=False)
                    logger.info("Waiting for translation messages...")
                    while not self.stop_event.is_set():
                        self.connection.process_data_events(time_limit=1)
                except Exception as e:
                    logger.error(f"Error during message consumption: {e}")
                    raise
            except Exception as e:
                logger.error(f"Translation consumer error: {e}")
        self.close()

    def close(self):
        """Close RabbitMQ connection"""
        logger.info("Closing RabbitMQ connection...")
        try:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
            raise

# Initialize an instance of your process message service.
response_service = ProcessResponseService()
