# import requests
# # This is a simple example of how to use the LibreTranslate API

# response = requests.post(
#     "https://libretranslate.com/translate",
#     json={
#         "q": "Hello!",
#         "source": "en",
#         "target": "es",
#     },
#     headers={"Content-Type": "application/json"},
# )


# print(response.json())

from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

response = client.responses.create(model="gpt-4o-mini", input="Hello")

print(response.output_text)