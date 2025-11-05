import os
import json
from openai import OpenAI
import datetime

def log_message(role, content):
    """
    Append a log entry with a timestamp, role, and content to conversation_log.txt.
    """
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"{timestamp} [{role}]: {content}\n"
    with open("conversation_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
 
class LLM:

    def __init__(self, model, temperature=0.7, max_tokens=1024):
        self.model = model  # Use the provided model parameter
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.model:
            raise ValueError("请提供有效的模型名称。")
        
        if self.model not in [           
            "gpt-4.1-mini"                        
        ]:
            raise ValueError(f"不支持的模型：{self.model}")
               
        if self.model == "gpt-4.1-mini":
            self.api_key = ""  # Set your OpenAI API key here
            self.api_base = None

        if not self.api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量。")

    def chat(self, messages):
        """
        Calls the ChatCompletion API with the provided messages and returns the reply.
        """

        try:
            if self.api_base:
                client = OpenAI(api_key=self.api_key, base_url=self.api_base)
            else:
                client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            reply = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    reply += chunk.choices[0].delta.content
            log_message("user", reply)
            return reply

        except Exception as e:
            error_msg = f"Error calling OpenAI API: {e}"
            return error_msg
