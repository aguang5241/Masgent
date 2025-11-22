# !/usr/bin/env python3

import os, sys
import asyncio
from dotenv import load_dotenv
from colorama import Fore, Style

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    ToolCallPart,
    ToolReturnPart,
    )

from masgent import tools
from masgent.utils import (
    ask_for_openai_api_key,
    validate_openai_api_key,
    load_system_prompts, 
    color_print, color_input
    )

# Track whether OpenAI key has been checked during this process
_openai_key_checked = False

def print_help():
    msg = '''
In AI mode, you can interact naturally with the assistant to help with a wide
range of materials simulation tasks. Ask questions, generate input files, diagnose
errors, or get guidance on using different tools.

Try asking:
  • "Generate a POSCAR file for NaCl."
  • "Prepare VASP input files for a graphene structure."
  • "Add defects to a silicon crystal POSCAR."
  • ...

Global Commands:
  ai    —>  Chat with the AI assistant
  back  —>  Switch back to main menu
  help  —>  List all available functions
  exit  —>  Quit the program
    '''
    color_print(msg, 'green')

def print_entry_message():
    msg = '''
Welcome to Masgent AI — Your AI Assistant for Materials Simulations.
--------------------------------------------------------------------
In AI mode, you can interact naturally with the assistant to help with a wide
range of materials simulation tasks. Ask questions, generate input files, diagnose
errors, or get guidance on using different tools.

Try asking:
  • "Generate a POSCAR file for NaCl."
  • "Prepare VASP input files for a graphene structure."
  • "Add defects to a silicon crystal POSCAR."
  • ...

Global Commands:
  ai    —>  Chat with the AI assistant
  back  —>  Switch back to console mode
  help  —>  List all available functions
  exit  —>  Quit the program
    '''
    color_print(msg, 'green')

async def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    '''
    Keep only recent messages while preserving AI model message ordering rules.

    Most AI models require proper sequencing of:
    - Tool/function calls and their corresponding returns
    - User messages and model responses
    - Multi-turn conversations with proper context

    This means we cannot cut conversation history in a way that:
    - Leaves tool calls without their corresponding returns
    - Separates paired messages inappropriately
    - Breaks the logical flow of multi-turn interactions

    Reference: https://github.com/pydantic/pydantic-ai/issues/2050
    '''
    message_window = 10

    if len(messages) <= message_window:
        return messages

    # Find system prompt if it exists
    system_prompt = None
    system_prompt_index = None
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelRequest) and any(isinstance(part, SystemPromptPart) for part in msg.parts):
            system_prompt = msg
            system_prompt_index = i
            break

    # Start at target cut point and search backward (upstream) for a safe cut
    target_cut = len(messages) - message_window

    for cut_index in range(target_cut, -1, -1):
        first_message = messages[cut_index]

        # Skip if first message has tool returns (orphaned without calls)
        if any(isinstance(part, ToolReturnPart) for part in first_message.parts):
            continue

        # Skip if first message has tool calls (violates AI model ordering rules)
        if isinstance(first_message, ModelResponse) and any(
            isinstance(part, ToolCallPart) for part in first_message.parts
        ):
            continue

        # Found a safe cut point
        result = messages[cut_index:]

        # If we cut off the system prompt, prepend it back
        if system_prompt is not None and system_prompt_index is not None and cut_index > system_prompt_index:
            result = [system_prompt] + result

        color_print(f'[Debug] Message history truncated. Only keeping recent {len(result)} messages.\n', 'green')

        return result

    # No safe cut point found, keep all messages
    return messages

async def chat_stream(agent, user_input: str, history: list):
    async with agent.run_stream(
        user_prompt=user_input, 
        message_history=history
        ) as result:
        fully_reply = ''
        async for chunk in result.stream_text(delta=True):
            fully_reply += chunk
            print(Fore.GREEN + chunk + Style.RESET_ALL, end='', flush=True)
        print('\n')

        all_msgs = list(result.all_messages())
        
        return all_msgs

async def ai_mode(agent):
    history = []
    
    try:
        while True:
            user_input = color_input('\nAsk anything or type "back" to return > ', 'yellow').strip()

            if not user_input:
                continue
            
            if user_input in {'ai'}:
                color_print('[Info] You are already in AI mode. \n', 'green')
            elif user_input in {'back'}:
                return 'cli-mode'
            elif user_input in {'help'}:
                print_help()
            elif user_input in {'exit'}:
                return 'exit-mode'
            else:
                try:
                    history = await chat_stream(agent, user_input, history)
                    color_print(f'[Debug] Message history updated. Total messages: {len(history)}.\n', 'green')
                except Exception as e:
                    color_print(f'[Error]: {e}', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent. Goodbye!\n', 'green')
        sys.exit(0)

def main():
    print_entry_message()


    # Ensure OpenAI API key exists and validate it only once per process
    load_dotenv(dotenv_path='.env')

    global _openai_key_checked
    if not _openai_key_checked:
        if 'OPENAI_API_KEY' not in os.environ:
            ask_for_openai_api_key()
        else:
            color_print('[Info] OpenAI API key found in environment.\n', 'green')
            validate_openai_api_key(os.environ['OPENAI_API_KEY'])
        _openai_key_checked = True

    model = OpenAIChatModel(model_name='gpt-5-nano')

    system_prompt = load_system_prompts()

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            tools.generate_vasp_poscar,
            tools.generate_vasp_inputs_from_poscar,
            tools.customize_vasp_kpoints_with_accuracy,
            tools.convert_structure_format,
            tools.convert_poscar_coordinates,
            tools.generate_vasp_poscar_with_defects,
        ],
        history_processors=[keep_recent_messages],
        )
    
    mode = asyncio.run(ai_mode(agent))
    return mode

if __name__ == '__main__':
    main()