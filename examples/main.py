#### main.py
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent

from dotenv import load_dotenv
import tools

load_dotenv(dotenv_path='.env')
model = OpenAIChatModel(model_name='gpt-5-nano')

agent = Agent(
    model=model,
    system_prompt='You are a experienced programmer',
    tools=[tools.read_file, tools.list_files, tools.rename_file],
    )

def main():
    history = []
    while True:
        user_input = input("Input: ")
        resp = agent.run_sync(user_prompt=user_input,
                              message_history=history)
        history = list(resp.all_messages())
        print(resp.output)


if __name__ == "__main__":
    main()