import streamlit as st
from src.application.langchain import Conversation
from src.application.db_functions import ConversationStore
import uuid


conversation=Conversation()
conversation_store=ConversationStore()

if 'session_id' not in st.session_state:
    st.session_state.session_id=str(uuid.uuid4())

if 'messages' not in st.session_state:
    st.session_state.messages=[]

st.set_page_config(page_title="Chat application")
st.title("Hey Lets Chat")

# Option to load a previous conversation
load_session_id = st.sidebar.text_input("Enter Session ID to load:")
if st.sidebar.button("Load Conversation"):
    try:
        loaded_conversation = conversation_store.get_conversation(load_session_id)
        if loaded_conversation:
            st.session_state.messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in loaded_conversation['conversation']
            ]
            st.session_state.session_id = load_session_id
            st.sidebar.success("Conversation loaded successfully!")
        else:
            st.sidebar.error("No conversation found for the given Session ID.")
    except Exception as e:
        st.sidebar.error(f"Error loading conversation: {str(e)}")

        
# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt=st.chat_input("type your message")
if prompt:
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message("User"):
        st.write(prompt)

    try:
        response=conversation.get_response(session_id=st.session_state.session_id,input=prompt)
        if response:
            with st.chat_message("Assistant"):
                st.write(response)

            st.session_state.messages.append({'role':'assistant','content':response})
        else:
            st.error("No response received from the assistant.")
    except Exception as e:
        st.error(f"1st Error Getting Response: {str(e)}")
        print(f"Detailed error: {type(e).__name__}, {str(e)}")

button=st.button("End conversation")
if button:
    try:
        conversation_history=conversation.get_conversation_history(session_id=st.session_state.session_id)
        #Store Conversation

        conversation_store.store_conversation(session_id=st.session_state.session_id,conversation_history=conversation_history)
        st.success("Conversation stored successfully")
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    except Exception as e:
        st.error(f"Error Getting response: {str(e)}")
        print(f"Detailed error: {type(e).__name__}, {str(e)}")


# write conversation on sidebar
st.sidebar.write(f"Current Session ID: {st.session_state.session_id}")
