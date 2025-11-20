# masgent/cli.py

import sys

from masgent.ai_mode import backend
from masgent.cli_mode import cli_backend
from masgent.utils import print_title, color_print, color_input


def cli_mode():
    color_print('Entering CLI mode. Type "ai" to AI mode or "exit" to quit. Type "help" to see available commands.\n', 'green')
    mode = cli_backend.main()
    return mode

def ai_mode():
    color_print('Entering AI mode. Type "cli" to CLI mode or "exit" to quit. Type "help" to see available commands. Now ask anything...\n', 'green')
    mode = backend.main()
    return mode

def main():
    '''Top-level control loop: mode selector + persistent switching.'''
    print_title()

    mode = None
    while True:
        try:
            if mode is None:
                color_print('Select Mode:', 'green')
                color_print('  - ai      → AI  mode (chat with AI)', 'green')
                color_print('  - cli     → CLI mode (manual commands)', 'green')
                color_print('  - exit    → Exit\n', 'green')

                choice = color_input('Enter mode [ai/cli/exit]: ', 'yellow').strip().lower()
                if choice == 'cli':
                    mode = 'cli-mode'
                elif choice == 'ai':
                    mode = 'ai-mode'
                elif choice == 'exit':
                    mode = 'exit-mode'
                else:
                    color_print('Invalid choice. Please type "ai" for AI or "cli" for CLI.\n', 'green')
                    continue

            if mode == 'cli-mode':
                mode = cli_mode()
            elif mode == 'ai-mode':
                mode = ai_mode()
            elif mode == 'exit-mode':
                color_print('\nExiting Masgent. Goodbye!\n', 'green')
                sys.exit(0)
    
        except (KeyboardInterrupt, EOFError):
            color_print('\nExiting Masgent. Goodbye!\n', 'green')
            sys.exit(0)

if __name__ == '__main__':
    main()
