# !/usr/bin/env python3

import sys, os
from bullet import Bullet, colors

from masgent.ai_mode import ai_backend
from masgent.cli_mode.cli_entries import run_command
from masgent.utils.utils import (
    color_print,
    print_help,
    start_new_session,
    clear_and_print_banner_and_entry_message,
    )

def main():
    # Create a single session runs directory
    start_new_session()
    
    try:
        while True:
            clear_and_print_banner_and_entry_message()
            choices = [
                '1. Density Functional Theory (DFT) Simulations',
                '2. Fast simulations using machine learning potentials (MLPs)',
                '3. Machine Learning Model Training & Evaluation',
                '',
                'AI    ->  Chat with the Masgent AI',
                'New   ->  Start a new session',
                'Help  ->  Show available functions',
                'Exit  ->  Quit the Masgent',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()
            
            if user_input.startswith('AI'):
                ai_backend.main()
            if user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('1'):
                run_command('1')
            elif user_input.startswith('2'):
                run_command('2')
            elif user_input.startswith('3'):
                run_command('3')
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

if __name__ == '__main__':
    main()
