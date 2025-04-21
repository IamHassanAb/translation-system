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

class StatusService:
    def __init__(self) -> None:
        self.status_message_queue = Queue()
        self.stop_event = Event()
        self.request = {}
        self.response = {}
        logger.info("Initializing ProcessMessageService")
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
            self.channel.queue_declare(queue=settings.STATUS_QUEUE)
            logger.info("RabbitMQ setup completed")
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ: {e}")
            raise

    def setup_redis(self):
        """Setup Redis connection."""
        try:
            logger.info("Setting up Redis connection")
            # pool = redis.ConnectionPool().from_url(settings.REDIS_URL)
            self.redis_client = redis.Redis().from_url(settings.REDIS_URL)
            # self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
            self.redis_client.ping()
            logger.info("Redis setup completed")
        except Exception as e:
            logger.error(f"Failed to setup Redis: {e}")
            raise
    
    def process(self, request: Dict) -> Dict:
        """
        Perform the message processing and return a response.
        logger.info("Starting message processing")
        try:
            # Assign a unique ID based on the current time (or use another unique method)
            self.mesage_id = round(time.time())
            request['id'] = self.mesage_id

            # Example: Call an external language detection service
            external_service_url = "https://example.com/language-detection"
            headers = {"Content-Type": "application/json"}
            response = requests.post(external_service_url, json=request, headers=headers)

            if response.status_code == 200:
                logger.info("Successfully called external language detection service")
                response_data = response.json()
                logger.info(f"Response from external service: {response_data}")
                return {"status": "success", "data": response_data}
            else:
                logger.error(f"Failed to call external service. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"status": "error", "message": "External service call failed"}
        except Exception as e:
            logger.error(f"Error during message processing: {e}")
            return {"status": "error", "message": str(e)}
        """
        pass

    def store(self, request: Dict) -> str:
        """
        Store the translation request in Redis and publish a notification for subscribers.
        :param request: The translation request to store
        :return: The request ID
                try:
            logger.info("Storing translation request in Redis")

            # Validate request ID
            request_id = request.get('id')
            if not request_id:
                logger.error("Request ID is missing or invalid.")
                raise ValueError("Request ID is required to store the translation request.")

            # Serialize the request
            try:
                serialized_request = json.dumps(request)
            except TypeError as e:
                logger.error(f"Error serializing request: {e}")
                raise ValueError("Request contains non-serializable data.")

            # Ensure Redis connection is healthy
            try:
                self.redis_client.ping()
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                raise ConnectionError("Failed to connect to Redis.")

            # Store the request in Redis
            self.redis_client.set(request_id, serialized_request)
            self.redis_client.publish('translation_channel', serialized_request)
            logger.info(f"Stored request with ID: {request_id} and data: {serialized_request}")

            return request_id
        except Exception as e:
            logger.error(f"Error storing request in Redis: {e}")
            raise
        """
        pass

    def consume(self):
        """
        Consume messages from the RabbitMQ status queue.
        When a message is received from translation, it given as a status response to the user.
        """
        while not self.stop_event.is_set():
            try:
                def callback(ch, method, properties, body):
                    logger.info(f"Received message from status queue: {body}")
                    try:
                        # Assuming the body is a JSON-encoded string
                        request_data = json.loads(body.decode())
                        self.status_message_queue.put(request_data)
                        logger.info(f"Message added to queue: {request_data}")
                    except Exception as e:
                        logger.error(f"Error adding status message: {e}")
                        # ch.basic_ack(delivery_tag=method.delivery_tag)
                        raise
                    finally:
                        logger.info("Status message produced successfully")
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                try:
                    logger.info("Starting Status Consumer...")
                    # Note: Using auto_ack=False to ensure messages are acknowledged after processing.
                    self.channel.basic_consume(queue=settings.STATUS_QUEUE, 
                                               on_message_callback=callback, 
                                               auto_ack=False)
                    logger.info("Waiting for status messages...")
                    while not self.stop_event.is_set():
                        self.connection.process_data_events(time_limit=1)
                except Exception as e:
                    logger.error(f"Error during message consumption: {e}")
                    raise
            except Exception as e:
                logger.error(f"Status consumer error: {e}")
        self.close()

    # def subscribe(self):
    #     """
    #     Subscribe to the Redis Pub/Sub channel ('translation_channel') to receive notifications in real time.
    #     This can be run in a separate thread or integrated into your asynchronous workflow.
    #     """
    #     pubsub = self.redis_client.pubsub()
    #     pubsub.subscribe('translation_channel')
    #     logger.info("Subscribed to 'translation_channel'")
    #     for message in pubsub.listen():
    #         if message['type'] == 'message':
    #             request_id = json.loads(message['data'])["id"]
    #             logger.info(f"Received published message for request ID: {request_id}")
    #             response_string = self.redis_client.get(request_id)
    #             if response_string:
    #                 response = json.loads(response_string)
    #                 await websocket.send_text(json.dumps(response))
    #                 logger.info(f"Sent response: {response} to room: {room_id}")
    #             # Optionally, fetch the stored data from Redis.
    #             # data = self.redis_client.get(request_id)
    #             # if data:
    #             #     logger.info(f"Retrieved data for {request_id}: {data.decode()}")
    #             # else:
    #             #     logger.warning(f"No data found for request ID: {request_id}")

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
status_service = StatusService()
