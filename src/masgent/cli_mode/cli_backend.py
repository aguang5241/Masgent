# masgent/cli_mode/cli_backend.py

import sys

from masgent.cli_mode import cli_tools
from masgent.utils import color_print, color_input

def print_help():
    color_print('\nMasgent CLI mode usage:', 'green')
    color_print('  Type one of the following commands:\n', 'green')
    color_print('Available commands:', 'green')
    color_print('  hello              → Print a hello message', 'green')
    color_print('  goodbye            → Print a goodbye message\n', 'green')
    color_print('  ai                 → Switch to AI mode', 'green')
    color_print('  help               → Show this help message', 'green')
    color_print('  exit               → Exit the program\n', 'green')

def main():
    commands = {
        'hello': cli_tools.say_hello,
        'goodbye': cli_tools.say_goodbye,
    }

    try:
        while True:
            user_input = color_input('Masgent CLI > ', 'yellow').strip().lower()

            if not user_input:
                continue

            if user_input in {'exit'}:
                return 'exit-mode'
            elif user_input in {'ai'}:
                return 'ai-mode'
            elif user_input in {'help'}:
                print_help()
            elif user_input in commands:
                commands[user_input]()
            else:
                color_print(f'Unknown command: {user_input}', 'green')
                color_print('Type "help" to see available commands.\n', 'green')

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent. Goodbye!\n', 'green')
        sys.exit(0)

if __name__ == '__main__':
    main()