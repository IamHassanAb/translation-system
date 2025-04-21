from openai import OpenAI
from dotenv import load_dotenv


class OpenAiUtilityService:
    def __init__(self, model : str = "gpt-4o-mini"):
        load_dotenv()
        self.model = model
        self.client = OpenAI()
        
    
    # def load_env(self):
    #     load_dotenv
    
    def detect(self, text : str = None):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You will be provided with a user input in a specific langauge you are required to identify the langauge_code of the input.\nOnly output the detected langauge_code (i.e. en, fr etc), without any additional text."},
                {"role": "user", "content": f"{text}"}
            ]
        )
        return response.choices[0].message.content

model = OpenAiUtilityService()