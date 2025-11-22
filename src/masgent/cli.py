# !/usr/bin/env python3

import sys
from bullet import Bullet, colors

from masgent.ai_mode import ai_backend
from masgent.utils import color_print, print_banner, print_help
from masgent.cli_mode.cli_run import run_command


def main():
    print_banner()
    
    try:
        while True:
            prompt = '''
Welcome to Masgent — Your Materials Simulation Agent.
-----------------------------------------------------
Please select from the following options:
'''
            choices = [
                '1. Density Functional Theory (DFT) Simulations',
                '2. Machine Learning Potentials (MLP)',
                '3. Machine Learning Model Training & Evaluation',
                '',
                '--- Global Commands ---',
                'AI',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt=prompt, choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue
            
            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input == '1. Density Functional Theory (DFT) Simulations':
                run_command('1')
            elif user_input == '2. Machine Learning Potentials (MLP)':
                run_command('2')
            elif user_input == '3. Machine Learning Model Training & Evaluation':
                run_command('3')
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

if __name__ == '__main__':
    main()
