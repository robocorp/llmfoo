# LLM FOO

## Overview
LLM FOO is a cutting-edge project blending the art of Kung Fu with the science of Large Language Models... or 
actually this is about automatically making the OpenAI tool JSON Schema, parsing call and constructing the
result to the chat model.

But hey I hope this will become a set of small useful LLM helper functions that will make building stuff easier.

![](/llmfoo.webp)

## Installation
```bash
pip install llmfoo
```

## Usage
Here's a quick example of how to use LLM FOO:
```python
from time import sleep

from openai import OpenAI

from llmfoo.functions import tool


@tool
def adder(x: int, y: int) -> int:
    return x + y


@tool
def multiplier(x: int, y: int) -> int:
    return x * y


client = OpenAI()


def test_chat_completion_with_adder():
    number1 = 3267182746
    number2 = 798472847
    messages = [
        {
            "role": "user",
            "content": f"What is {number1} + {number2}?"
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=[adder.openai_schema]
    )
    messages.append(response.choices[0].message)
    messages.append(adder.openai_tool_call(response.choices[0].message.tool_calls[0]))
    response2 = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=[adder.openai_schema]
    )
    assert str(adder(number1, number2)) in response2.choices[0].message.content.replace(",", "")


def test_assistant_with_multiplier():
    number1 = 1238763428176
    number2 = 172388743612
    assistant = client.beta.assistants.create(
        name="The Calc Machina",
        instructions="You are a calculator with a funny pirate accent.",
        tools=[multiplier.openai_schema],
        model="gpt-4-1106-preview"
    )
    thread = client.beta.threads.create(messages=[
        {
            "role":"user",
            "content":f"What is {number1} * {number2}?"
        }
    ])
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    while True:
        run_state = client.beta.threads.runs.retrieve(
            run_id=run.id,
            thread_id=thread.id,
        )
        if run_state.status not in ['in_progress', 'requires_action']:
            break
        if run_state.status == 'requires_action':
            tool_call = run_state.required_action.submit_tool_outputs.tool_calls[0]
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[
                    multiplier.openai_tool_output(tool_call)
                ]
            )
            sleep(1)
        sleep(0.1)
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    assert str(multiplier(number1, number2)) in messages.data[0].content[0].text.value.replace(",", "")

```

## Features
- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Contributing
Interested in contributing? We'd love your help to make this project even better. Check out our contributing guidelines.

## License
This project is licensed under the [MIT License](LICENSE).

## Contact
For any questions or feedback, please contact us at contact@example.com.

## Acknowledgements
- Thanks to all the contributors and maintainers.
- Special thanks to the Kung Fu masters who inspired this project.
