# LLM FOO

[![Version](https://img.shields.io/pypi/v/llmfoo.svg)](https://pypi.python.org/pypi/llmfoo)
[![Downloads](http://pepy.tech/badge/llmfoo)](http://pepy.tech/project/llmfoo)

## Overview
LLM FOO is a cutting-edge project blending the art of Kung Fu with the science of Large Language Models... or 
actually this is about automatically making the OpenAI tool JSON Schema, parsing call and constructing the
result to the chat model.
And then there is a second utility `is_statement_true` that uses [genius logit_bias trick](https://twitter.com/AAAzzam/status/1669753721574633473)
that only uses one output token.

But hey I hope this will become a set of small useful LLM helper functions that will make building stuff easier
because current bleeding edge APIs are a bit of a mess and I think we can do better.

![](/llmfoo.webp)

## Installation
```bash
pip install llmfoo
```

## Usage

* You need to have OPENAI_API_KEY in env and ability to call `gpt-4-1106-preview` model

* `is_statement_true` should be easy to understand.
Make some natural language statement, and check it against criteria or general truthfulness. You get back boolean.

For the LLM FOO tool:

1. Add `@tool` annotation.
2. llmfoo will generate the json schema to YOURFILE.tool.json with GPT-4-Turbo - "Never send a machine to do a human's job" .. like who wants to write boilerplate docs for Machines???
3. Annotated functions have helpers:
   - `openai_schema` to return the schema (You can edit it from the json if your not happy with what the machines did)
   - `openai_tool_call` to make the tool call and return the result in chat API message format
   - `openai_tool_output` to make the tool call and return the result in assistant API tool output format

```python
from time import sleep

from openai import OpenAI

from llmfoo.functions import tool
from llmfoo import is_statement_true


def test_is_statement_true_with_default_criteria():
    assert is_statement_true("Earth is a planet.")
    assert not is_statement_true("1 + 2 = 5")


def test_is_statement_true_with_own_criteria():
    assert not is_statement_true("Temperature outside is -2 degrees celsius",
                                 criteria="Temperature above 0 degrees celsius")
    assert is_statement_true("1984 was written by George Orwell",
                             criteria="George Orwell is the author of 1984")


def test_is_statement_true_criteria_can_change_truth_value():
    assert is_statement_true("Earth is 3rd planet from the Sun")
    assert not is_statement_true("Earth is 3rd planet from the Sun",
                                 criteria="Earth is stated to be 5th planet from the Sun")


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

## Contributing
Interested in contributing? Loved to get your help to make this project better!
The APIs under are changing and system is still very much first version.

## License
This project is licensed under the [MIT License](LICENSE).

## Acknowledgements
- Thanks to all the contributors and maintainers.
- Special thanks to the Kung Fu masters such as Bruce Lee who inspired this project.
