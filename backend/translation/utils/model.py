from openai import OpenAI
from dotenv import load_dotenv

class OpenAiUtilityService:
    def __init__(self, model : str = "gpt-4o-mini"):
        load_dotenv()
        self.model = model
        self.client = OpenAI()
        
    
    def translate(self, source_lang : str = "en", target_lang : str = "fr", text : str = None):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You will be provided with a user input in language_code: {source_lang}.\nTranslate the text into language_code: {target_lang}.\nOnly output the translated text, without any additional text."},
                {"role": "user", "content": f"{text}"}
            ]
        )
        return response.choices[0].message.content
    

model = OpenAiUtilityService()