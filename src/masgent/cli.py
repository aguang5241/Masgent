# !/usr/bin/env python3

import sys

from masgent.ai_mode import ai_backend
from masgent.cli_mode import cli_backend
from masgent.utils import color_print

def cli_mode():
    mode = cli_backend.main()
    return mode

def ai_mode():
    mode = ai_backend.main()
    return mode

def main():
    # Print ascii banner
    cli_backend.print_banner()

    # Hybrid mode: default to CLI mode, allow switching to AI mode anytime
    mode = 'cli-mode'
    while True:
        try:
            if mode == 'ai-mode':
                mode = ai_mode()
            elif mode == 'cli-mode':
                cli_backend.print_entry_message()
                mode = cli_mode()
            elif mode == 'exit-mode':
                color_print('Exiting Masgent. Goodbye!\n', 'green')
                sys.exit(0)

        except (KeyboardInterrupt, EOFError):
            color_print('\nExiting Masgent. Goodbye!\n', 'green')
            sys.exit(0)

if __name__ == '__main__':
    main()
