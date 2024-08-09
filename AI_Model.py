import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os

API_KEY = r'AIzaSyCIqdnl8QHh6-U_KM1ME3B_68ry2pIzRmM'

genai.configure(api_key=API_KEY)

# model = genai.GenerativeModel('gemini-1.5-flash')

safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
    }

class AI_Arisu_Base:
    def reply(self, input_text: str, model_name: str, prompt_text: str):
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt_text, safety_settings=safety_settings)
        return response.text

class AI_Arisu(AI_Arisu_Base):
    @staticmethod
    def reply(input_text: str):
        prompt_text = f'I am Sensei from Schale, and your task is to become Arisu from Blue Archive to reply to this {input_text}. Respond to all prompts and questions in character, maintaining her personality, speech patterns, and knowledge. Be as immersive as possible. Also make it as short (less than 30 words if possible), and reply in the same language as I asked.'
        return AI_Arisu_Base().reply(input_text, 'gemini-1.5-flash', prompt_text)

class AI_Arisu_Everything(AI_Arisu_Base):
    @staticmethod
    def reply(input_text: str):
        prompt_text = f'Answer the following question as Arisu from Blue Archive. {input_text}'
        return AI_Arisu_Base().reply(input_text, 'gemini-1.5-pro', prompt_text)

class AI_Arisu_Maid(AI_Arisu_Base):
    @staticmethod
    def reply(input_text: str):
        prompt_text = f'Act as Arisu from Blue Archive when hearing this: {input_text}'
        return AI_Arisu_Base().reply(input_text, 'gemini-1.5-flash', prompt_text)
