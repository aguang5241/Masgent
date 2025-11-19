# masgent/ai_mode/backend.py

import os, sys
import asyncio
from dotenv import load_dotenv

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent

import masgent.ai_mode.tools as tools

def ask_for_api_key():
    key = input('Enter your OpenAI API key: ').strip()
    if not key:
        print('\nAPI key cannot be empty. Exiting...\n')
        sys.exit(1)

    # Store temporarily for this session
    os.environ['OPENAI_API_KEY'] = key

    # Optional: write to .env so user never needs to type again
    save = input('\nSave this key to .env file for future? (y/n): ').strip().lower()
    if save == 'y':
        with open('.env', 'w') as f:
            f.write(f'OPENAI_API_KEY={key}\n')
        print('\nAPI key saved to .env file.')
        
    print('\nAPI key loaded.\n')

def print_help():
    print('\nMasgent AI Mode usage:')
    print('  Chat with the AI by typing your questions or using specific commands.\n')
    print('Available commands:')
    print('  cli                → Switch to CLI mode')
    print('  help               → Show this help message')
    print('  exit               → Exit the program\n')

async def chat_stream(agent, user_input: str, history: list):
    async with agent.run_stream(
        user_prompt=user_input, 
        message_history=history
        ) as result:
        fully_reply = ''
        async for chunk in result.stream_text(delta=True):
            fully_reply += chunk
            print(chunk, end='', flush=True)
        print('\n')

        return list(result.all_messages())

async def ai_mode(agent):
    history = []
    
    try:
        while True:
            user_input = input('Masgent AI > ').strip()

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
                    history = history[-10:]  # Keep last 10 messages
                except Exception as e:
                    print(f'[Error]: {e}')

    except (KeyboardInterrupt, EOFError):
        print('\nExiting Masgent. Goodbye!\n')
        sys.exit(0)

def main():
    load_dotenv(dotenv_path='.env')

    if 'OPENAI_API_KEY' not in os.environ:
        ask_for_api_key()
    else:
        print('API key found in environment.\n')

    model = OpenAIChatModel(model_name='gpt-5-nano')

    system_prompt = '''
You are MASGENT, a concise materials-simulation agent.

GENERAL RULES:
- Respond with ONE short sentence only.
- When asking for missing parameters, ask ONE direct question only.
- Never provide explanations unless the user asks.

PARAMETER COMPLETION:
- When parameters are missing, ask ONE short question describing the parameters in natural language.
- Do not use internal parameter names; describe what the information represents.
- Ask: "Do you want to provide <parameter information>, or should I infer it?"
- Infer a parameter only if the user explicitly says "infer", "guess", or "you decide".
- When inferring, use typical chemical and crystallographic defaults.
- After inferring multiple parameters, confirm with ONE sentence: "Proceed with a = X and alpha = Y?"

TOOL CALL RULES:
- Use a tool only when the user clearly requests an action the tool performs.
- Do not call tools until all parameters are confirmed.
- Never guess if the user does NOT explicitly give permission.

TOOL RETURN RULES:
- Tools return a string.
- If the string is empty → tool succeeded → output NOTHING.
- If the string is non-empty → output the string as the error.

CLARITY:
- No paragraphs.
- No multi-sentence reasoning.
- Only one short sentence for each reply.

    '''

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            tools.generate_simple_poscar,
            tools.generate_incar_from_poscar,
        ],
        )
    
    mode = asyncio.run(ai_mode(agent))
    return mode

if __name__ == '__main__':
    main()