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

st.title("Friendly Chat App")

prompt=st.chat_input("type your message")
if prompt:
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message("User"):
        st.write(prompt)

    try:
        response=conversation.get_response(session_id=st.session_state.session_id,input=prompt)

        with st.chat_message("Assistant"):
            st.write(response)

        st.session_state.messages.append({'role':'assistant','content':response})
    except Exception as e:
        st.error(f"1st Error Getting Response: {str(e)}")

button=st.button("End conversation")
if button:
    try:
        conversation_history=conversation.get_conversation_history(session_id=st.session_state.session_id)
        #Store Conversation
        conversation_store.store_conversation(session_id=st.session_state.session_id,conversation_history=conversation_history)
        st.success("Conversation stored successfully")
    except Exception as e:
        st.error(f"Error Getting response: {str(e)}")
