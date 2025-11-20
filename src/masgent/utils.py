# masgent/utils.py

import os, sys
from pathlib import Path
from colorama import Fore, Style
from importlib.metadata import version, PackageNotFoundError

def get_color_map():
    return {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE,
    }

def color_print(text, color='cyan'):
    '''Print text in specified color.'''
    color_map = get_color_map()
    chosen_color = color_map.get(color.lower(), Fore.CYAN)
    print(chosen_color + text + Style.RESET_ALL)

def color_input(text, color='cyan'):
    '''Input prompt in specified color.'''
    color_map = get_color_map()
    chosen_color = color_map.get(color.lower(), Fore.CYAN)
    return input(chosen_color + text + Style.RESET_ALL)

def load_system_prompts():
    # src/masgent/ai_mode/system_prompt.txt
    prompts_path = Path(__file__).resolve().parent / 'ai_mode' / 'system_prompt.txt'
    try:
        return prompts_path.read_text(encoding='utf-8')
    except Exception as e:
        return f'Error loading system prompts: {str(e)}'

def ask_for_openai_api_key():
    key = color_input('Enter your OpenAI API key: ', 'yellow').strip()
    if not key:
        color_print('\nOpenAI API key cannot be empty. Exiting...\n', 'green')
        sys.exit(1)

    # Store temporarily for this session
    os.environ['OPENAI_API_KEY'] = key

    # Optional: write to .env so user never needs to type again
    save = color_input('\nSave this key to .env file for future? (y/n): ', 'yellow').strip().lower()
    if save == 'y':
        with open('.env', 'w') as f:
            f.write(f'OPENAI_API_KEY={key}\n')
        color_print('\nOpenAI API key saved to .env file.', 'green')
        
    color_print('\nOpenAI API key loaded.\n', 'green')
    
def ask_for_mp_api_key():
    key = color_input('Enter your Materials Project API key: ', 'yellow').strip()
    if not key:
        color_print('\nMaterials Project API key cannot be empty. Exiting...\n', 'green')
        sys.exit(1)

    # Store temporarily for this session
    os.environ['MP_API_KEY'] = key

    # Optional: write to .env so user never needs to type again
    save = color_input('\nSave this key to .env file for future? (y/n): ', 'yellow').strip().lower()
    if save == 'y':
        with open('.env', 'a') as f:
            f.write(f'MP_API_KEY={key}\n')
        color_print('\nMaterials Project API key saved to .env file.', 'green')
        
    color_print('\nMaterials Project API key loaded.\n', 'green')

def os_path_setup():
    '''Set up base and target directories for VASP input files.'''
    base_dir = os.getcwd()
    runs_dir = os.path.join(base_dir, 'masgent_runs')
    output_dir = os.path.join(base_dir, 'masgent_outputs')
    return base_dir, runs_dir, output_dir

def print_title():
    '''Print the Masgent ASCII banner and metadata inside a box.'''

    # Retrieve installed version
    try:
        pkg_version = version('masgent')
    except PackageNotFoundError:
        pkg_version = 'dev'

    # ASCII banner
    ascii_banner = rf'''
+---------------------------------------------------------------------------+
|                                                                           |
|   ███╗   ███╗  █████╗  ███████╗  ██████╗  ███████╗ ███╗   ██╗ ████████╗   |
|   ████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝  ██╔════╝ ████╗  ██║ ╚══██╔══╝   |
|   ██╔████╔██║ ███████║ ███████╗ ██║  ███╗ █████╗   ██╔██╗ ██║    ██║      |
|   ██║╚██╔╝██║ ██╔══██║ ╚════██║ ██║   ██║ ██╔══╝   ██║╚██╗██║    ██║      |
|   ██║ ╚═╝ ██║ ██║  ██║ ███████║ ╚██████╔╝ ███████╗ ██║ ╚████║    ██║      |
|   ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚══════╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝    ╚═╝      |
|                            A Materials Simulation AI Agent Framework      |
|                                               (c) 2025 Guangchen Liu      |
|   Version:         {pkg_version:<53}  |
|   Licensed:        MIT License                                            |
|   Repository:      https://github.com/aguang5241/masgent                  |
|   Citation:        Liu, G. et al. (2025), DOI:10.XXXX/XXXXX'              |
|   Contact:         gliu4@wpi.edu                                          |
|                                                                           |
+---------------------------------------------------------------------------+
    '''
    print(ascii_banner)