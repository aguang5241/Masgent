import sys

import masgent.ai_mode.ai_backend as ai_backend
import masgent.cli_mode.cli_backend as cli_backend
from masgent.utils import print_title

def cli_mode():
    print('Entering CLI mode. Type "ai" to AI mode or "exit" to quit. Type "help" to see available commands.\n')
    mode = cli_backend.main()
    return mode

def ai_mode():
    print('Entering AI mode. Type "cli" to CLI mode or "exit" to quit. Type "help" to see available commands. Now ask anything...\n')
    mode = ai_backend.main()
    return mode

def main():
    '''Top-level control loop: mode selector + persistent switching.'''
    print_title()

    mode = None
    while True:
        try:
            if mode is None:
                print('\nSelect Mode:')
                print('  - ai:      AI  mode (chat with AI)')
                print('  - cli:     CLI mode (manual commands)')
                print('  - exit:    Exit\n')

                choice = input('Enter mode [ai/cli/exit]: ').strip().lower()
                if choice == 'cli':
                    mode = 'cli-mode'
                elif choice == 'ai':
                    mode = 'ai-mode'
                elif choice == 'exit':
                    mode = 'exit-mode'
                else:
                    print('Invalid choice. Please type "ai" for AI or "cli" for CLI.\n')
                    continue

            if mode == 'cli-mode':
                mode = cli_mode()
            elif mode == 'ai-mode':
                mode = ai_mode()
            elif mode == 'exit-mode':
                print('Exiting Masgent. Goodbye!\n')
                sys.exit(0)
    
        except (KeyboardInterrupt, EOFError):
            print('\nExiting Masgent. Goodbye!\n')
            sys.exit(0)

if __name__ == '__main__':
    main()
