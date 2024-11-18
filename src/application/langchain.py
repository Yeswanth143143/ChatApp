from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
import os
from dotenv import dotenv_values
from src.application.db_functions import ConversationStore, CosmosDBHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.messages.ai import AIMessage
from typing import Dict
config=dotenv_values("D:\GenAI\Projects\ChatApp\.env")
AZURE_OPENAI_KEY=config["AZURE_OPENAI_KEY"]
AZURE_ENDPOINT=config["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_VERSION=config["AZURE_OPENAI_VERSION"]
AZURE_OPENAI_DEPLOYMENT=config["OPENAI_DEPLOYMENT_NAME"]



# Code for Conversation
class Conversation():
    def __init__(self):
        self.llm=AzureChatOpenAI(api_key=AZURE_OPENAI_KEY,azure_endpoint=AZURE_ENDPOINT,api_version=AZURE_OPENAI_VERSION,azure_deployment=AZURE_OPENAI_DEPLOYMENT)
        self.store=ConversationStore()
        self.history={}

        prompt=ChatPromptTemplate.from_messages(
            [("system","You are a friendly chatbot"),
             MessagesPlaceholder(variable_name="history"),
             ("human","{input}")]
        )

        chain= prompt | self.llm
        
        def get_session_history(session_id: str):
            if session_id not in self.history:
                self.history[session_id]= CosmosDBHistory(session_id,self.store)
            return self.history[session_id]
        self.conversation=RunnableWithMessageHistory(chain,get_session_history,input_messages_key="input",history_messages_key="history")
        
    def get_response(self, input: str, session_id:str):
        print(f"Getting response for input: '{input}' and session_id: {session_id}")
        try:
            self.response=self.conversation.invoke({"input":input}, config={"configurable":{"session_id":session_id}})
            print(f"Raw response: {self.response}")
            if isinstance(self.response, str):
                return self.response
            elif isinstance(self.response, AIMessage):
                return self.response.content
            elif isinstance(self.response, dict):
                if 'content' in self.response:
                    return self.response['content']
                elif isinstance(self.response.get('response'), str):
                    return self.response['response']
                else:
                    return str(self.response)
            else:
                print(f"Unexpected response format: {type(self.response)}")
                return str(self.response)
        except Exception as e:
            return f"An error occurred: {str(e)}"
    
    # Get the conversation history given session_id
    def get_conversation_history(self,session_id: str) -> list[BaseMessage]:
        if session_id in self.history:
            return self.history[session_id].messages
        else:
            history=CosmosDBHistory(session_id, self.store)
            self.history[session_id]=history
            return self.history[session_id].messages