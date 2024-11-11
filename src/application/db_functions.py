from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
import os
import uuid
from datetime import datetime
load_dotenv()

class ConversationStore():
    def __init__(self):
        self.client=CosmosClient(url=os.getenv("COSMOS_URI"),credential=os.getenv("COSMOS_KEY"))

        self.database=self.client.create_database_if_not_exists(id="ChatApp")
        self.container=self.database.create_container_if_not_exists(id="ChatConversation",partition_key="/id",offer_throughput=400)

    def store_conversation(self,session_id: str,conversation_history: list[BaseMessage]):
        conversation={
            "id":str(uuid.uuid4()),
            "session_id":session_id,
            "conversation":[ {"role":msg.type,"content":msg.content} for msg in conversation_history],
            "timestamp":datetime.isoformat()
        }
        self.container.upsert_item(body=conversation)

    def get_conversation(self,session_id: str) -> dict:
        self.query=f"SELECT * FROM c WHERE c.session_id == {session_id}"
        #Check what container returns
        self.conversation=list[self.container.query_items(query=self.query)]
        if self.conversation:
            return self.conversation[0]
        else:
            None


class CosmosDBHistory(BaseChatMessageHistory):
    def __init__(self,session_id: str, store : 'ConversationStore'):
        self.session_id=session_id
        self.store=store
        self._messages : list[BaseMessage]=[]
        self._load_messages()

        def _load_messages(self):
            conversation=self.store.get_conversation(self.session_id)
            if conversation:
                self._messages = [
                HumanMessage(content=msg['content']) if msg['role'] == 'human' else AIMessage(content=msg['content'])
                for msg in conversation['conversation']
                                ]
        def add_message(self, message: BaseMessage) -> None:
            self._messages.append(message)
            self.store.store_conversation(self.session_id, self._messages)

    def clear(self) -> None:
        self._messages = []
        self.store.store_conversation(self.session_id, self._messages)

    @property
    def messages(self) -> list[BaseMessage]:
        return self._messages
