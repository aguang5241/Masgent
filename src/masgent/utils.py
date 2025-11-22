# !/usr/bin/env python3

import os, sys, datetime
from pathlib import Path
from colorama import Fore, Style
from mp_api.client import MPRester
from openai import OpenAI

def write_comments(file, file_type, comments):
    with open(file, 'r') as f:
        lines = f.readlines()

    if file_type.lower() in {'poscar', 'kpoints'}:
        lines[0] = comments + '\n'
    
    elif file_type.lower() in {'incar'}:
        lines.insert(0, f'{comments}\n')
    
    with open(file, 'w') as f:
        f.writelines(lines)

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

def validate_openai_api_key(key):
    try:
        client = OpenAI(api_key=key)
        client.models.list()
        color_print('[Info] OpenAI API key validated successfully.\n', 'green')
    except Exception as e:
        color_print('[Error] Invalid OpenAI API key. Exiting...\n', 'green')
        sys.exit(1)

def ask_for_openai_api_key():
    key = color_input('Enter your OpenAI API key: ', 'yellow').strip()
    if not key:
        color_print('[Error] OpenAI API key cannot be empty. Exiting...\n', 'green')
        sys.exit(1)
    
    validate_openai_api_key(key)

    os.environ['OPENAI_API_KEY'] = key

    save = color_input('Save this key to .env file for future? (y/n): ', 'yellow').strip().lower()
    base_dir = os.getcwd()
    env_path = os.path.join(base_dir, '.env')
    if save == 'y':
        with open(env_path, 'w') as f:
            f.write(f'OPENAI_API_KEY={key}\n')
        color_print(f'[Info] OpenAI API key saved to {env_path} file.\n', 'green')
    
def validate_mp_api_key(key):
    try:
        with MPRester(key, mute_progress_bars=True) as mpr:
            _ = mpr.materials.search(
                formula='Si',
                fields=['material_id']
            )
        color_print('[Info] Materials Project API key validated successfully.\n', 'green')
    except Exception as e:
        color_print('[Error] Invalid Materials Project API key. Exiting...\n', 'green')
        sys.exit(1)
    
def ask_for_mp_api_key():
    key = color_input('Enter your Materials Project API key: ', 'yellow').strip()
    if not key:
        color_print('[Error] Materials Project API key cannot be empty. Exiting...\n', 'green')
        sys.exit(1)

    validate_mp_api_key(key)

    os.environ['MP_API_KEY'] = key

    save = color_input('Save this key to .env file for future? (y/n): ', 'yellow').strip().lower()
    base_dir = os.getcwd()
    env_path = os.path.join(base_dir, '.env')
    if save == 'y':
        with open(env_path, 'a') as f:
            f.write(f'MP_API_KEY={key}\n')
        color_print(f'Materials Project API key saved to {env_path} file.\n', 'green')

def os_path_setup():
    '''Set up base and target directories for VASP input files.'''
    base_dir = os.getcwd()
    runs_dir = os.path.join(base_dir, 'masgent_runs')
    output_dir = os.path.join(base_dir, 'masgent_outputs')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    runs_timestamp_dir = os.path.join(runs_dir, f'runs_{timestamp}')
    os.makedirs(runs_timestamp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    return base_dir, runs_dir, runs_timestamp_dir, output_dir
