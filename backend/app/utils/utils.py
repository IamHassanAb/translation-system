import logging
import threading
from core.config import settings
import requests
# from services.translation import translation_service
from services.status import status_service
from services.response import response_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UtilityService:
    def __init__(self):
        logger.info("Initializing UtilityService...")
        self.statusservice_thread = None
        self.response_thread = None

    async def start_langauge_detection(self, request: dict) -> dict:
        """ Starting Language detection by calling Language Detection Service endpoint. """
        logger.info("Starting language detection...")
        try:
            # Call the language detection service here
            logger.debug(f"Request payload for language detection: {request}")
            external_service_url = settings.LANGUAGE_DETECTION_URL
            headers = {"Content-Type": "application/json"}
            logger.debug(f"Calling external service at {external_service_url} with headers {headers}")
            response = requests.post(external_service_url, json=request, headers=headers)

            if response.status_code == 200:
                logger.info("Successfully called external language detection service")
                response_data = response.json()
                logger.debug(f"Response data from external service: {response_data}")
                return {"status": "success", "data": response_data}
            else:
                logger.error(f"Failed to call external service. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"status": "error", "message": "External service call failed"}
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return {"status": "error", "message": str(e)}
        
    def start_response_consumer(self):
        try:
            logger.info("Starting response consumer...")
            response_service.consume()
            logger.info("Response message consumer started successfully.")
        except Exception as e:
            logger.error(f"Error in response message consumer: {e}")


    def start_status_consumer(self):
        try:
            logger.info("Starting status consumer...")
            status_service.consume()
            logger.info("Process message consumer started successfully.")
        except Exception as e:
            logger.error(f"Error in process message consumer: {e}")

    async def start_background_tasks(self):
        logger.info("Starting background tasks...")
        self.statusservice_thread = threading.Thread(
            target=self.start_status_consumer, daemon=True
        )
        self.response_thread = threading.Thread(
            target=self.start_response_consumer, daemon=True
        )
        self.statusservice_thread.start()

        self.response_thread.start()
        logger.info("Background tasks started successfully.")

    def close_background_tasks(self):
        logger.info("Stopping background tasks...")
        try:
            status_service.stop_event.set()  # Signal the process message consumer to stop
            logger.info("Signaled 'Status Service' consumer to stop.")
            self.statusservice_thread.join()  # Wait for the thread to finish
            logger.info("'Status Service' consumer thread closed.")

            response_service.stop_event.set()  # Signal the process message consumer to stop
            logger.info("Signaled 'Response Service' consumer to stop.")
            self.response_thread.join()  # Wait for the thread to finish
            logger.info("'Response Service' consumer thread closed.")
        except Exception as e:
            logger.error(f"Error while stopping background tasks: {e}")


utility_service = UtilityService()