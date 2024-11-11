from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_openai import AzureChatOpenAI
import os
from dotenv import dotenv_values
from langchain.memory import ConversationBufferMemory
from db_functions import ConversationStore, CosmosDBHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

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

        self.prompt=ChatPromptTemplate.from_messages(
            [("system","You are a friendly chatbot"),
             MessagesPlaceholder(variable_name="history"),
             ("human",{"user_input"})]
        )

        chain= self.prompt | self.llm

        def get_session_history(session_id: str):
            if session_id not in self.history:
                self.history[session_id]= CosmosDBHistory(session_id,self.store)
            return self.history
        
        self.conversation=RunnableWithMessageHistory(chain,get_session_history,input_messages_key="user_input",history_messages_key="history")

    def get_response(self, input: str, session_id:str):
        self.response=self.conversation.invoke(input=input, config={"configurable":{"session_id":session_id}})
        return self.response
    
    # Get the conversation history given session_id

    def get_conversation_history(self,session_id: str) -> dict:
        if session_id in self.history:
            return self.history[session_id].messages
        else:
            history=CosmosDBHistory(session_id, self.store)
            self.history[session_id]=history
            return history.messages