# !/usr/bin/env python3

import os, datetime, random, asyncio
from dotenv import load_dotenv
from colorama import Fore, Style
from yaspin import yaspin
from yaspin.spinners import Spinners
from bullet import Bullet, colors

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    ToolCallPart,
    ToolReturnPart,
    )

from masgent.cli_mode.cli_run import run_command
from masgent.utils import tools
from masgent.utils.utils import (
    ask_for_api_key,
    load_system_prompts, 
    color_print,
    color_input,
    start_new_session,
    print_help,
    exit_and_cleanup,
    clear_and_print_entry_message,
    )

_provider = None

def print_entry_message():
    msg_1 = f'''
Welcome to Masgent AI — Your Materials Simulations Agent.
---------------------------------------------------------
Current Session Runs Directory: {os.environ["MASGENT_SESSION_RUNS_DIR"]}
'''
    
    if _provider == 'Masgent - Masgent AI':
        msg_2 = f'Provider: {_provider}\n\nNote: Initial response time may be up to one minute during cold start.'
    else:
        msg_2 = f'Provider: {_provider}'
    
    msg_3 = '''
Try asking:
  • "Generate a POSCAR file for NaCl."
  • "Prepare full VASP input files for LaCoO3."
  • "Add vacancy defects to a LiFePO4 crystal."
  • ...
'''
    color_print(msg_1, 'white')
    color_print(msg_2, 'white')
    color_print(msg_3, 'green')

def save_msg(msg, role, filename):
    '''
    Save model/user conversation history to a text file in a readable format.
    '''
    timestamp = datetime.datetime.now().strftime('%Y-%m-%-d %H:%M:%S')
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {role}:\n\n{msg}\n')
        f.write('\n' + '-'*60 + '\n\n')

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
    # Define how many recent messages to keep
    message_window = 20

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

        # color_print(f'[Debug] Message history truncated. Only keeping recent {len(result)} messages.\n', 'green')

        return result

    # No safe cut point found, keep all messages
    return messages

async def chat_stream(agent, user_input: str, history: list):
    print('')
    with yaspin(Spinners.dots, text='Thinking...', color='cyan') as sp:
        async with agent.run_stream(
            user_prompt=user_input, 
            message_history=history
            ) as result:
            
            # Live streaming preview
            sp.hide()
            all = ''
            async for chunk in result.stream_text(delta=True):
                all += chunk
                print(Fore.GREEN + chunk + Style.RESET_ALL, end='', flush=True)
            print('')
        
        sp.stop()

        # Save AI response to conversation history
        msg_path = os.path.join(os.environ['MASGENT_SESSION_RUNS_DIR'], 'conversation_history.txt')
        save_msg(all, 'Masgent AI', filename=msg_path)

        # Get full message history after the interaction
        all_msgs = list(result.all_messages())

        return all_msgs
    
async def chat(agent, user_input: str, history: list):
    print('')
    with yaspin(Spinners.dots, text='Thinking...', color='cyan') as sp:
        result = await agent.run(
            user_prompt=user_input,
            message_history=history
        )
        sp.stop()

    text = result.output

    # color_print(text, 'green')

    # Random split to simulate streaming
    chunks = []
    split_points = sorted(random.sample(range(1, len(text)), k=min(10, len(text)//10)))
    prev = 0
    for point in split_points:
        chunks.append(text[prev:point])
        prev = point
    chunks.append(text[prev:])
    
    # Fake streaming effect
    for chunk in chunks:
        print(Fore.GREEN + chunk + Style.RESET_ALL, end='', flush=True)
        await asyncio.sleep(0.1)
    print('')

    # Save AI response to conversation history
    msg_path = os.path.join(os.environ['MASGENT_SESSION_RUNS_DIR'], 'conversation_history.txt')
    save_msg(text, 'Masgent AI', filename=msg_path)

    return list(result.all_messages())

async def ai_mode(agent):
    history = []

    msg_path = os.path.join(os.environ['MASGENT_SESSION_RUNS_DIR'], 'conversation_history.txt')
    with open(msg_path, 'a', encoding='utf-8') as f:
        f.write('\n' + '='*60 + '\n')
        f.write(f'New AI Session Started at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('='*60 + '\n\n')
    
    try:
        while True:
            user_input = color_input('\nAsk anything, or type "back" to return, "new" to start a new session > ', 'yellow').strip()

            if not user_input:
                continue

            if user_input.lower() in {'new'}:
                start_new_session()
                os.system('cls' if os.name == 'nt' else 'clear')
                print_entry_message()
            elif user_input.lower() in {'back'}:
                return
            else:
                try:
                    # Save user message to conversation history
                    save_msg(user_input, 'User', filename=msg_path)
                    # Start regular chat or chat stream based on provider
                    if _provider == 'Masgent - Masgent AI':
                        history = await chat(agent, user_input, history)
                    else:
                        history = await chat_stream(agent, user_input, history)
                    # color_print(f'[Debug] Message history updated. Total messages: {len(history)}.\n', 'green')
                except Exception as e:
                    color_print(f'[Error]: {e}', 'red')

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

def main():
    global _provider
    if not _provider:
        try:
            while True:
                clear_and_print_entry_message()
                choices = [
                    'Masgent    ->  Masgent AI (no API key needed, response time may be longer during cold start)',
                    'OpenAI     ->  GPT-5 Nano (requires OpenAI API key)',
                    'Anthropic  ->  Claude Sonnet 4.5 (requires Anthropic API key)',
                    'Google     ->  Gemini 2.5 Flash (requires Google API key)',
                    'xAI        ->  Grok 4.1 Fast (requires Grok API key)',
                    'Deepseek   ->  Deepseek Chat (requires Deepseek API key)',
                    'Alibaba    ->  Qwen Flash (requires Alibaba Cloud API key)',
                    '',
                    'New   ->  Start a new session',
                    'Back  ->  Return to previous menu',
                    'Main  ->  Return to main menu',
                    'Help  ->  Show available functions',
                    'Exit  ->  Quit the Masgent',
                ]
                cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
                user_input = cli.launch()
                
                if user_input.startswith('New'):
                    start_new_session()
                elif user_input.startswith('Back'):
                    return
                elif user_input.startswith('Main'):
                    run_command('0')
                elif user_input.startswith('Help'):
                    print_help()
                elif user_input.startswith('Exit'):
                    exit_and_cleanup()
                elif user_input.startswith('Masgent'):
                    _provider = 'Masgent - Masgent AI'
                    break
                elif user_input.startswith('OpenAI'):
                    _provider = 'OpenAI - GPT-5 Nano'
                    break
                elif user_input.startswith('Anthropic'):
                    _provider = 'Anthropic - Claude Sonnet 4.5'
                    break
                elif user_input.startswith('Google'):
                    _provider = 'Google - Gemini 2.5 Flash'
                    break
                elif user_input.startswith('xAI'):
                    _provider = 'xAI - Grok 4.1 Fast'
                    break
                elif user_input.startswith('Deepseek'):
                    _provider = 'Deepseek - Deepseek Chat'
                    break
                elif user_input.startswith('Alibaba'):
                    _provider = 'Alibaba - Qwen Flash'
                else:
                    continue
        
        except (KeyboardInterrupt, EOFError):
            exit_and_cleanup()

    os.system('cls' if os.name == 'nt' else 'clear')
    print_entry_message()

    if _provider == 'Masgent - Masgent AI':
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(base_url='https://masgent-ai.onrender.com/v1')
        model = OpenAIChatModel(model_name='gpt-5-nano', provider=provider)
    elif _provider == 'OpenAI - GPT-5 Nano':
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        load_dotenv(dotenv_path='.env')
        if 'OPENAI_API_KEY' not in os.environ:
            ask_for_api_key('OPENAI_API_KEY')
        provider = OpenAIProvider(api_key=os.environ['OPENAI_API_KEY'])
        model = OpenAIChatModel(model_name='gpt-5-nano', provider=provider)
    elif _provider == 'Anthropic - Claude Sonnet 4.5':
        from pydantic_ai.models.anthropic import AnthropicModel
        load_dotenv(dotenv_path='.env')
        if 'ANTHROPIC_API_KEY' not in os.environ:
            ask_for_api_key('ANTHROPIC_API_KEY')
        model = AnthropicModel(model_name='claude-sonnet-4-5')
    elif _provider == 'Google - Gemini 2.5 Flash':
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider
        load_dotenv(dotenv_path='.env')
        if 'GOOGLE_API_KEY' not in os.environ:
            ask_for_api_key('GOOGLE_API_KEY')
        provider = GoogleProvider(api_key=os.environ['GOOGLE_API_KEY'])
        model = GoogleModel('gemini-2.5-flash', provider=provider)
    elif _provider == 'xAI - Grok 4.1 Fast':
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.grok import GrokProvider
        load_dotenv(dotenv_path='.env')
        if 'GROK_API_KEY' not in os.environ:
            ask_for_api_key('GROK_API_KEY')
        provider = GrokProvider(api_key=os.environ['GROK_API_KEY'])
        model = OpenAIChatModel(model_name='grok-4-1-fast-non-reasoning', provider=provider)
    elif _provider == 'Deepseek - Deepseek Chat':
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.deepseek import DeepSeekProvider
        load_dotenv(dotenv_path='.env')
        if 'DEEPSEEK_API_KEY' not in os.environ:
            ask_for_api_key('DEEPSEEK_API_KEY')
        provider = DeepSeekProvider(api_key=os.environ['DEEPSEEK_API_KEY'])
        model = OpenAIChatModel(model_name='deepseek-chat', provider=provider)
    elif _provider == 'Alibaba - Qwen Flash':
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.alibaba import AlibabaProvider
        load_dotenv(dotenv_path='.env')
        if 'DASHSCOPE_API_KEY' not in os.environ:
            ask_for_api_key('DASHSCOPE_API_KEY')
        provider = AlibabaProvider(api_key=os.environ['DASHSCOPE_API_KEY'])
        model = OpenAIChatModel(model_name='qwen-flash', provider=provider)
    else:
        color_print('[Error]: Unsupported AI provider selected.', 'red')
        exit_and_cleanup()

    system_prompt = load_system_prompts()

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            tools.list_files,
            tools.rename_file,
            tools.read_file,
            tools.generate_vasp_poscar,
            tools.generate_vasp_inputs_from_poscar,
            tools.generate_vasp_inputs_hpc_slurm_script,
            tools.customize_vasp_kpoints_with_accuracy,
            tools.convert_structure_format,
            tools.convert_poscar_coordinates,
            tools.generate_vasp_poscar_with_vacancy_defects,
            tools.generate_vasp_poscar_with_substitution_defects,
            tools.generate_vasp_poscar_with_interstitial_defects,
            tools.generate_supercell_from_poscar,
            tools.generate_sqs_from_poscar,
            tools.generate_surface_slab_from_poscar,
            tools.generate_interface_from_poscars,
            tools.visualize_structure_from_poscar,
            tools.generate_vasp_workflow_of_convergence_tests,
            tools.generate_vasp_workflow_of_eos,
            tools.generate_vasp_workflow_of_elastic_constants,
            tools.generate_vasp_workflow_of_aimd,
            tools.generate_vasp_workflow_of_neb,
            tools.analyze_vasp_workflow_of_convergence_tests,
            tools.analyze_vasp_workflow_of_eos,
            tools.analyze_vasp_workflow_of_elastic_constants,
            tools.analyze_vasp_workflow_of_aimd,
            tools.run_simulation_using_mlps,
            tools.analyze_features_for_machine_learning,
            tools.reduce_dimensions_for_machine_learning,
            tools.augment_data_for_machine_learning,
            tools.design_model_for_machine_learning,
            tools.train_model_for_machine_learning,
            tools.model_prediction_for_AlMgSiSc,
            tools.model_prediction_for_AlCoCrFeNi,
        ],
        history_processors=[keep_recent_messages],
        )
    
    mode = asyncio.run(ai_mode(agent))
    return mode

if __name__ == '__main__':
    main()