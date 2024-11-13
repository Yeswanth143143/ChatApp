from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
from dotenv import load_dotenv
from azure.cosmos import CosmosClient,PartitionKey
import os
import uuid
from datetime import datetime,timezone
from typing import List,Dict
load_dotenv()

class ConversationStore():
    def __init__(self):
        self.client=CosmosClient(url=os.getenv("COSMOS_URI"),credential=os.getenv("COSMOS_KEY"))
        self.database=self.client.create_database_if_not_exists(id="ChatApp")
        try:
            self.container=self.database.create_container_if_not_exists(id="ChatConversation",partition_key=PartitionKey(path="/id"),offer_throughput=400)
            print("ConversationStore initialized successfully")
        except Exception as e:
            print(e)
        
    def store_conversation(self,session_id: str,conversation_history: List[BaseMessage]):
        conversation={
            "id":str(uuid.uuid4()),
            "session_id":session_id,
            "conversation":[ {"role":msg.type,"content":msg.content} for msg in conversation_history],
            "timestamp":datetime.now(timezone.utc).isoformat()}
        self.container.upsert_item(body=conversation)
        print(f"Conversation stored successfully.")

    def get_conversation(self,session_id: str) -> Dict:
        query="SELECT * FROM c WHERE c.session_id = @session_id"
        #Check what container returns
        self.items=self.container.query_items(query=query,parameters=[{'name':'@session_id',"value":session_id}],enable_cross_partition_query=True)
        self.conversation=list(self.items)
        print(f"Conversation retrieved successfully for session_id: {session_id}")
        print(self.conversation)
        if self.conversation:
            return self.conversation[0]
        else:
            return None


class CosmosDBHistory(BaseChatMessageHistory):
    def __init__(self,session_id: str, store : 'ConversationStore'):
        self.session_id=session_id
        self.store=store
        self._messages : List[BaseMessage]=[]
        print("Load messages started")
        self._load_messages()

    def _load_messages(self):
        conversation=self.store.get_conversation(self.session_id)
        if conversation:
            self._messages = [
            HumanMessage(content=msg['content']) if msg['role'] == 'human' else AIMessage(content=msg['content'])
            for msg in conversation['conversation']]
        print("load messages completed")
    
    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)
        print(f"Adding message: {message.type} - {message.content}")
        self.store.store_conversation(self.session_id, self._messages)

    def clear(self) -> None:
        self._messages = []
        self.store.store_conversation(self.session_id, self._messages)

    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages
