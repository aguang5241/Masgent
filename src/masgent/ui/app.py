import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent
import masgent.ai_mode.tools as tools

# ------------------------------
# 1. Page setup
# ------------------------------
st.set_page_config(
    page_title="Masgent: Materials Simulation AI Agent",
    page_icon="",
    layout="wide",
)

st.title("Masgent: Materials Simulation AI Agent Framework")

# ------------------------------
# 2. Load or ask for API key
# ------------------------------
load_dotenv(dotenv_path=".env")

if "OPENAI_API_KEY" not in os.environ:
    with st.sidebar:
        st.warning("No API key found. Please enter your OpenAI API key below.")
        key_input = st.text_input("Enter your OpenAI API key", type="password")
        if key_input:
            os.environ["OPENAI_API_KEY"] = key_input
            st.success("API key set for this session!")
else:
    st.sidebar.success("✅ API key loaded from .env")

# ------------------------------
# 3. Define the AI model & agent
# ------------------------------
if "OPENAI_API_KEY" in os.environ:
    model = OpenAIChatModel(model_name="gpt-5-nano")

    system_prompt = """
You are a materials simulation expert assistant, proficient in DFT, MD, and related computational methods.

Use a tool whenever the user requests something that one of your tools can produce or modify.
Infer reasonable default values if the user leaves parameters unspecified.

If a tool call produces an error, adjust the parameters and retry once.

After a tool runs, output NOTHING if the return status is 'Success', output ONLY the error message if the return status is 'Error'.
Do NOT output JSON, status fields, or any extra text.
If the tool returns nothing, output: "Completed"

If the user asks a question unrelated to available tools, respond normally.
If the request is ambiguous, ask for clarification.
    """

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            tools.generate_simple_poscar,
            tools.generate_vasp_inputs_from_poscar,
        ],
    )
else:
    agent = None

# ------------------------------
# 4. Initialize chat history
# ------------------------------
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ------------------------------
# 5. Define async streaming helper
# ------------------------------
async def chat_stream(agent, user_input, history):
    """Stream response from the AI agent."""
    response_box = st.empty()         # placeholder for live updates
    full_reply = ""

    async with agent.run_stream(user_prompt=user_input, message_history=history) as result:
        async for chunk in result.stream_text(delta=True):
            full_reply += chunk
            # incremental update without full redraw
            response_box.markdown(full_reply + "▌")  # blinking cursor

        # final render after streaming ends
        response_box.markdown(full_reply)
        return full_reply, list(result.all_messages())


# ------------------------------
# 6. Display chat UI
# ------------------------------
if agent:
    user_input = st.chat_input("Ask Masgent about DFT, MD, ML, or VASP setup...")

    # Display previous messages
    for msg in st.session_state.chat_history:
        role, content = msg
        st.chat_message(role).markdown(content)

    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_placeholder = st.chat_message("assistant")

        # Run async stream
        try:
            reply, history = asyncio.run(chat_stream(agent, user_input, st.session_state.chat_history))
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("assistant", reply))
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("Please provide an API key to start chatting with Masgent.")
