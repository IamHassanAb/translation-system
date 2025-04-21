import logging
import pika.exceptions
from transformers import pipeline
# from langdetect import detect_langs, DetectorFactory
from langid.langid import LanguageIdentifier, model
from utils.model import model
from core.config import settings
import pika
from typing import Dict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LanguageDetectionService:
    def __init__(self):
        logger.info("Initializing LanguageDetectionService...")
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        try:
            logger.info("Setting up RabbitMQ connection...")
            self.connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.DETECTION_QUEUE)
            logger.info("RabbitMQ setup complete.")
        except Exception as e:
            logger.error(f"Failed to set up RabbitMQ: {e}")
            raise

    def process(self, request: Dict):
        """Perform the Language Detection Process with Retry Logic"""
        logger.info("Starting language detection process...")
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                logger.info(f"Attempt {attempt + 1} for Detection: {request}")
                self.publish_status({"type": "status", "message": "Language detection started."})
                text = request.get('text')

                source_lang = self.detect(text)
                request['source_lang'] = source_lang
                self.publish_lang(request)
                self.publish_status({"type": "status", "message": "Language detection completed."})
                return {
                    "message": "Language detection process completed.",
                    "source_lang": source_lang
                }
            except Exception as e:
                attempt += 1
                if attempt >= max_retries:
                    logger.error("Max retries reached. Failing the process.")
                    self.publish_status({"type": "status", "message": "Language detection failed."})
                    raise
                else:
                    logger.info("Retrying language detection process...")

    def detect(self, text: str) -> str:
        """Detect language using lang_detect library"""
        logger.info("Detecting language...")
        try:
            # DetectorFactory.seed = 0
            # detected_lang = detect_langs(text)[0]
            # parsed_lang = utility_service.extract_lang(str(detected_lang))
            # logger.info(f"Language detected: {parsed_lang}")
            # identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
            # # identifier.classify("This is a test")
            # parsed_lang, confidence = identifier.classify(text.lower())
            # logger.info(f"Language detected: {parsed_lang} with confidence {confidence}")
            lang_code = model.detect(text)
            logger.info(f"Language detected: {lang_code}")
            
            # ('en', 0.9999999909903544) #sample answer
            return lang_code
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            raise
    
    def publish_lang(self, request: Dict):
        """Queue translation request in RabbitMQ"""
        logger.info("Publishing detected language to RabbitMQ...")
        try:
            message = {
                "id": request.get('id'),
                "text": request.get('text'),
                "source_lang": request.get('source_lang'),
                "target_lang": request.get('target_lang'),
            }
            logger.info(f"Request to Detection Queue: {message}")
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.DETECTION_QUEUE,
                body=json.dumps(message)
            )
            logger.info("Message published to Detection Queue.")

            # self.close()
        except pika.exceptions.ChannelClosed as e:
            logger.error(f"Channel is closed: {e}. Re-establishing connection...")
            # self.setup_rabbitmq()  # Re-establish connection
            # self.publish_lang(request)  # Retry publishing
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")
    
    def publish_status(self, status):
        logger.info("Publishing status to RabbitMQ...")
        try:
            logger.info(f"Request to Detection Queue: {status}")

            self.channel.basic_publish(
                    exchange='',
                    routing_key=settings.STATUS_QUEUE,
                    body=json.dumps(status)
            )
            logger.info("Message published to Status Queue.")
        except pika.exceptions.ChannelClosed as e:
            logger.error(f"Channel is closed: {e}. Re-establishing connection...")
            # self.setup_rabbitmq()  # Re-establish connection
            # self.publish_status(status)  # Retry publishing
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")

    def close(self):
        """Close RabbitMQ connection"""
        logger.info("Closing RabbitMQ connection...")
        try:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
            raise

# Create global instance
language_detection = LanguageDetectionService()
