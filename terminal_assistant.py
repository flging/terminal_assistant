import json
import subprocess
import numpy as np
from openai import OpenAI
import threading

class TerminalAssistant:
    def __init__(self):
        self.api_key = ""
        self.client = None
        self.RAG_DB = []
        self.messages = [{"role": "system", "content": "너는 맥 운영체제의 터미널을 제어하는 함수인 run_command를 사용할 수 있어. 'create chat'은 유저에게 작업 결과를 설명하거나 추가 질문이 있을 경우에만 사용하고, 터미널 제어는 'function calling'을 이용해서만 가능해. RAG 기능이 활성화되어 있다면, 항상 가장 먼저 search_rag 함수를 호출하여 유사한 명령어를 찾아봐. search_rag 함수의 결과를 바탕으로 가장 적절한 명령어를 직접 선택하거나 수정하여 run_command 함수를 호출해. RAG를 통해 얻은 정보를 활용하거나 또는, 네가 알고 있던 명령어를 사용해. 사용자에게 추가 확인 없이 자동으로 판단하고 실행해."}]
        self.processing = False
        self.stop_event = threading.Event()

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.upstage.ai/v1/solar")

    def load_RAG_DB(self):
        try:
            with open('RAG_DB.json', 'r') as f:
                self.RAG_DB = json.load(f)
            return "RAG DB loaded successfully."
        except FileNotFoundError:
            return "RAG DB file not found. Please make sure 'RAG_DB.json' exists."

    def process_message(self, user_message, use_rag=True):
        self.messages.append({"role": "user", "content": user_message})
        self.processing = True
        self.stop_event.clear()
        
        try:
            return self.process_function_calls(use_rag)
        finally:
            self.processing = False

    def process_function_calls(self, use_rag):
        responses = []
        while not self.stop_event.is_set():
            response = self.function_call(use_rag)
            if isinstance(response, str):  
                responses.append(("assistant", response))
                return responses

            self.messages.append(response)
            
            if not response.tool_calls:
                responses.append(("assistant", response.content))
                return responses

            for tool_call in response.tool_calls:
                if self.stop_event.is_set():
                    return responses
                if tool_call.function.name == "search_rag" and use_rag:
                    function_args = json.loads(tool_call.function.arguments)
                    query = function_args.get("query")
                    function_response = self.search_rag(query)
                    self.messages.append({
                        "role": "assistant",
                        "content": f"RAG 검색 결과: {function_response}\n이 결과를 바탕으로 적절한 명령어를 선택하거나 생성하세요."
                    })
                    continue
                elif tool_call.function.name == "run_command":
                    function_args = json.loads(tool_call.function.arguments)
                    command = function_args.get("command")
                    responses.append(("command_input", command))
                    function_response = self.run_command(command)
                    responses.append(("command_output", function_response))
                else:
                    function_response = "Unexpected function call"
                    responses.append(("error", function_response))

                self.messages.append({
                    "role": "assistant",
                    "content": f"명령어 실행 결과: {function_response}"
                })

        return responses

    def function_call(self, use_rag):
        try:
            tools = [{
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Run a command in the terminal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to run in the terminal",
                            },
                        },
                        "required": ["command"],
                    },
                },
            }]

            if use_rag:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "search_rag",
                        "description": "Search the command database using RAG",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The query to search in the command database",
                                },
                            },
                            "required": ["query"],
                        },
                    },
                })

            response = self.client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=self.messages,
                tools=tools,
                tool_choice="auto",
            )
            return response.choices[0].message
        except Exception as e:
            return f"Error occurred: {str(e)}"

    def search_rag(self, query):
        query_embedding = self.client.embeddings.create(
            model="solar-embedding-1-large-query",
            input=query
        ).data[0].embedding
        
        similarities = [np.dot(np.array(query_embedding), np.array(cmd['embedding'])) for cmd in self.RAG_DB]
        top_3_indices = np.argsort(similarities)[-3:][::-1]
        
        results = []
        for idx in top_3_indices:
            results.append({
                "command": self.RAG_DB[idx]['command'],
                "similarity": similarities[idx]
            })
        
        return json.dumps(results)

    def run_command(self, command):
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Error during command execution: {str(e)}"

    def stop_processing(self):
        self.stop_event.set()
        return "Processing stopped by user."