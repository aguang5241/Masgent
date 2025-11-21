# masgent/ai_mode/backend.py

import os, sys
import asyncio
from dotenv import load_dotenv
from colorama import Fore, Style

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent

from masgent.ai_mode import tools
from masgent.utils import ask_for_openai_api_key, ask_for_mp_api_key, load_system_prompts, color_print, color_input

def print_help():
    color_print('\nMasgent AI Mode usage:', 'green')
    color_print('  Chat with the AI by typing your questions or using specific commands.\n', 'green')
    color_print('Available commands:', 'green')
    color_print('  cli                → Switch to CLI mode', 'green')
    color_print('  help               → Show this help message', 'green')
    color_print('  exit               → Exit the program\n', 'green')

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
            user_input = color_input('Masgent AI > ', 'yellow').strip()

            if not user_input:
                continue
            
            if user_input in {'exit'}:
                return 'exit-mode'
            elif user_input in {'cli'}:
                return 'cli-mode'
            elif user_input in {'help'}:
                print_help()
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
    load_dotenv(dotenv_path='.env')

    if 'OPENAI_API_KEY' not in os.environ:
        ask_for_openai_api_key()
    else:
        color_print('OpenAI API key found in environment.\n', 'green')

    if 'MP_API_KEY' not in os.environ:
        ask_for_mp_api_key()
    else:
        color_print('Materials Project API key found in environment.\n', 'green')

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
        )
    
    mode = asyncio.run(ai_mode(agent))
    return mode

if __name__ == '__main__':
    main()