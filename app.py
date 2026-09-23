import os
import streamlit as st
from dotenv import  load_dotenv
from openai import OpenAI

# Load environmental libraries
load_dotenv()

# Initialize OpenAI client
def get_api_key():
    """Get OpenAI API key from .env file, then fall back from to streamlit secrets"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
         api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
         pass
    return api_key

api_key = get_api_key()
client = OpenAI(api_key=api_key) if api_key else None

st.set_page_config(
    page_title = "🦆 Mini Rubber Ducky",
    page_icon = "🦆",
    layout = "wide",
    initial_sidebar_state = "expanded"
)

# Define the model
MODEL = "gpt-5.2"

# Define the initial message
INITIAL_MESSAGE = """
👋 Hi! I am Mini Rubber Ducky, your friendly assistant.
How can I help you today?
"""

INSTRUCTIONS = """
You are Mini Rubber Ducky, the course assistant for a multimodal RAG assistant course.
Be concise, direct, and practical. Use active voice. No fluff.

Primary objective
- Answer questions about the course content and code using the attached Vector Store (transcripts, notebooks, scripts).
- Prefer retrieved facts over memory. If the files don't cover it, say so.
- Focus on multimodal RAG concepts, implementations, and best practices.

Retrieval & citations
- Always use File Search first.
- Ground every substantive answer in retrieved snippets.
- If nothing relevant is found, say: "I don't see this in the course files." Then suggest the most relevant module(s) the learner should review.
- Never include source citations or reference labels in the final answer text.

Answer style
- Keep outputs scannable: short paragraphs, bullet steps, compact runnable code samples when needed.
- When explaining "how to build X", outline the pipeline stages (ingest → retrieve → generate → evaluate) before diving into code.
- Close each reply with a friendly follow-up question the learner might ask next.
- Stay approachable, encouraging, and human.

Boundaries
- Don't invent references, credentials, metrics, or file names.
- If the topic is outside multimodal RAG/this curriculum, acknowledge the gap and offer a high-level pointer or ask for clarification.

Context: Course focus
- Multimodal RAG: handling text, images, audio, and video in retrieval-augmented generation systems
- Vector stores and embeddings for multimodal data
- Integration patterns and architectures
- Practical implementations and code examples

If the learner references a lecture/section by name/number, search for files with that stem and tailor the answer.
Never invent lecture numbers or titles—they change over time.
If the answer isn't in the corpus, say so clearly.
"""

# Main App Content
st.title("🦆 Mini Rubber Ducky")
st.write("👋 Welcome to Mini Rubber Ducky!")

# Initialize the Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None
if "previous_response_id" not in st.session_state:
    st.session_state.previous_response_id = None

# Function to load the Vector Store
def load_vector_store():
    """load the vector store id from .env file, then fall back to streamlit secrets"""
    try:
        vector_store_id = os.getenv("VECTOR_STORE_ID")

        if not vector_store_id:
            st.secrets.get("vector_store_id")
    except Exception:
        pass

    if not vector_store_id:
        st.error("⚠️ No vector id found. Please set the VECTOR_STORE_ID environment variable or add it to the Streamlit secrets.")
        return None

    return vector_store_id


# Build the ask_bot function
def ask_bot(user_prompt: str):
    """Send questions to OpenAI and get responses"""
    common_kwargs = {
        "model": MODEL,
        "tools": [
        {"type": "file_search",
         "vector_store_ids": [st.session_state.vector_store_id],
         "max_num_results": 20
        }
    ],
        "text": {"verbosity": "low"},
        "instructions": INSTRUCTIONS
    }
    if st.session_state.previous_response_id:
        resp = client.responses.create(
            previous_response_id=st.session_state.previous_response_id,
            input = [{"role": "user", "content": user_prompt}],
            **common_kwargs
        )
    else:
        resp = client.responses.create(
            input = [
                {"role": "assistant", "content": INITIAL_MESSAGE.strip()},
                {"role": "user", "content": user_prompt}],
                **common_kwargs
        )
    st.session_state.previous_response_id = resp.id
    return resp.output_text




# Build function to reset conversation
def reset_conversation():
    """Reset the conversatiob history"""
    st.session_state.messages = [{
        "role": "assistant",
        "content": INITIAL_MESSAGE.strip()
    }]
    st.rerun()

def main():
    # Sidebar with reset button
    with st.sidebar:
        st.header("⚙️ Settings")
        if st.button("🔄 Reset Conversation"):
            reset_conversation()

    # Load the Vector Store
    if not st.session_state.vector_store_id:
        st.session_state.vector_store_id = load_vector_store()

    # Initialize the message
    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role" : "assistant",
                "content" : INITIAL_MESSAGE.strip()
            }
        ]

    # Display the entire conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    # Chat input
    prompt = st.chat_input("💬 Ask me anything about multimodal RAG")
    if prompt:
        st.session_state.messages.append(
            {"role" : "user", "content" : prompt}
            )
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process the user input
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = ask_bot(prompt)
            st.markdown(response)
        st.session_state.messages.append(
            {"role" : "assistant", "content" : response})


if __name__=="__main__":
    main()
