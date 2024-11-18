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
            self.container=self.database.create_container_if_not_exists(id="SessionChat",partition_key=PartitionKey(path="/session_id"),offer_throughput=400)
        except Exception as e:
            print(e)
        
    def store_conversation(self,session_id: str,conversation_history: List[BaseMessage]):
        timestamp=datetime.now(timezone.utc).isoformat()
        query = "SELECT * FROM c WHERE c.session_id = @session_id"
        existing_items = list(self.container.query_items(
        query=query,
        parameters=[{'name': '@session_id', 'value': session_id}],
        enable_cross_partition_query=True
        ))  
        if existing_items:
            # Update existing document
            existing_item = existing_items[0]
            existing_item['conversation'] = [{"role": msg.type, "content": msg.content} for msg in conversation_history]
            existing_item['timestamp'] = datetime.now(timezone.utc).isoformat()
            self.container.replace_item(item=existing_item, body=existing_item)
            print("converstaion added to existing item.")
        else:
            # Create new document
            conversation = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "conversation": [{"role": msg.type, "content": msg.content} for msg in conversation_history],
                "timestamp": timestamp
            }
            self.container.create_item(body=conversation)
            print("conversation stored to new document.")

    def get_conversation(self,session_id: str) -> Dict:
        query="SELECT * FROM c WHERE c.session_id = @session_id ORDER BY c.timestamp DESC OFFSET 0 LIMIT 1"
        #Check what container returns
        self.items=self.container.query_items(query=query,parameters=[{'name':'@session_id',"value":session_id}],enable_cross_partition_query=True)
        self.conversation=list(self.items)
        if self.conversation:
            return self.conversation[0]
        else:
            return None


class CosmosDBHistory(BaseChatMessageHistory):
    def __init__(self,session_id: str, store : 'ConversationStore'):
        self.session_id=session_id
        self.store=store
        self._messages : List[BaseMessage]=[]
        self._load_messages()

    def _load_messages(self):
        conversations=self.store.get_conversation(self.session_id)
        if conversations:
            self._messages = [
            HumanMessage(content=msg['content']) if msg['role'] == 'human' else AIMessage(content=msg['content'])
             for msg in conversations['conversation']]
            print("Messages Loaded to history list.")
    
    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)
        self.store.store_conversation(self.session_id, self._messages)

    def clear(self) -> None:
        self._messages = []
        self.store.store_conversation(self.session_id, self._messages)

    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages
