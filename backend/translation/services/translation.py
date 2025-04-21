import logging
# from transformers import pipeline
import requests
from utils.model import model
from core.config import settings
import pika
import json
from threading import Event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.stop_event = Event()
        self.models = {}
        self.request = {}
        self.setup_rabbitmq()
        logger.info("TranslationService initialized.")
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            # Create Connection to Translation Queue
            self.channel = self.connection.channel()
            # self.channel.exchange_declare(exchange='translation_exchange', exchange_type='direct')
            # self.channel.queue_bind(exchange='translation_exchange', queue=settings.TRANSLATION_QUEUE)
            self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)
            logger.info("RabbitMQ connection and channel setup completed.")
        except Exception as e:
            logger.error(f"Error setting up RabbitMQ: {e}")
            raise

    def get_model(self, source_lang: str = settings.DEFAULT_SOURCE_LANG, target_lang: str = settings.DEFAULT_TARGET_LANG):
        """Get or create translation model for language pair"""
        model_key = f"{source_lang}-{target_lang}"
        logger.info(f"Fetching model for language pair: {model_key}")
        if model_key not in self.models:
            model_name = settings.HUGGINGFACE_MODEL_URL
            model_name = settings.HUGGINGFACE_MODEL_URL.format(
                src=source_lang,
                tgt=target_lang
            )
            logger.info(f"Model not found in cache. Loading model for {model_key}: {model_name}")
            self.models[model_key] = model_name
            logger.info("After setting model key-value")
        else:
            logger.info(f"Model for {model_key} found in cache.")
        
        return self.models[model_key]
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            """            # Construct the prompt for translation
            prompt = f"Translate the following text from {source_lang} to {target_lang}:\n\n{text}"
            
            # Make a request to OpenAI API
            response = requests.post(
                "https://api.openai.com/v1/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "prompt": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.7
                })"""
            if source_lang == target_lang:
                logger.info("Source and target languages are the same. Returning original text.")
                return text

            logger.info(f"Translating text from {source_lang} to {target_lang} using OpenAI API.")
            translation = model.translate(source_lang=source_lang, target_lang=target_lang, text=text)
            
            
            
            # if response.status_code != 200:
            #     logger.error(f"Failed to translate text. Status code: {response.status_code}, Response: {response.text}")
            #     raise Exception(f"Translation API returned an error: {response.status_code}")
            
            # response_json = response.json()  # Parse the response
            # translation = response_json.get('choices', [{}])[0].get('text', '').strip()
            logger.info(f"Translation completed: {translation}")
            return translation
        
        # except requests.exceptions.RequestException as e:
        #     self.publish_status({"type": "status", "message": "Translation Failed Invalid Request to OpenAI API."})
        #     logger.error(f"Request to OpenAI API failed: {e}")
        #     raise
        # except json.JSONDecodeError as e:
        #     self.publish_status({"type": "status", "message": "Translation Failed Invalid Response From OpenAI API."})
        #     logger.error(f"Failed to decode JSON response: {e}")
        #     raise
        except Exception as e:
            self.publish_status({"type": "status", "message": "Translation Failed."})
            logger.error(f"An error occurred during translation: {e}")
            raise

    
    def publish_translation(self):
        """Queue translation request in RabbitMQ"""
        message = {
            "id": self.request.get('id'),
            "text": self.request.get('text'),
            "translation_text": self.request.get('translation_text'),
            "source_lang": self.request.get('source_lang'),
            "target_lang": self.request.get('target_lang'),
        }
        try:
            try:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=settings.TRANSLATION_QUEUE,
                    body=json.dumps(message)
                )
                logger.info("Translation request published to RabbitMQ.")
            except pika.exceptions.ChannelClosed as e:
                logger.error(f"Channel is closed: {e}. Re-establishing connection...")
                self.setup_rabbitmq()  # Re-establish connection
                self.publish_translation()  # Retry publishing
        except Exception as e:
            logger.error(f"Error publishing translation request: {e}")
            raise
    
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
            self.setup_rabbitmq()  # Re-establish connection
            self.publish_status(status)  # Retry publishing
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")


    def produce(self):
        try:
            logger.info("Producing translation request.")
            self.publish_status({"type": "status", "message": "Translation Started."})
            self.publish_translation()
            self.publish_status({"type": "status", "message": "Translation Completed."})
        except Exception as e:
            logger.error(f"Error in produce method: {e}")

    def consume(self):
        while not self.stop_event.is_set():
            try:
                def callback(ch, method, properties, body):
                    logger.info(f"Received message from RabbitMQ: {body}")
                    try:
                        message = json.loads(body.decode())
                        logger.info(f"Processing message: {message}")
                        text = message.get('text')
                        source_lang = message.get('source_lang')
                        target_lang = message.get('target_lang')
                        
                        # Retry logic for translation
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                translated_text = self.translate(text=text, source_lang=source_lang, target_lang=target_lang)
                                message['translation_text'] = translated_text
                                self.request = message  # Store the request for later use
                                logger.info(f"Translation result: {translated_text}")
                                self.produce()
                                logger.info("Updated message published with translation.")
                                break
                            except Exception as e:
                                logger.error(f"Attempt {attempt + 1} failed: {e}")
                                if attempt + 1 == max_retries:
                                    logger.error("Max retries reached. Failing the message.")
                                    raise
                                else:
                                    logger.info("Retrying translation...")
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                    finally:
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                logger.info("Starting to consume messages from RabbitMQ...")
                self.channel.basic_consume(queue=settings.DETECTION_QUEUE, on_message_callback=callback)
                logger.info("Waiting for messages...")
                while not self.stop_event.is_set():
                    self.connection.process_data_events(time_limit=1)
            except Exception as e:
                logger.error(f"Error in consume method: {e}")

    def close(self):
        """Close RabbitMQ connection"""
        try:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

# Create global instance
translation_service = TranslationService()
