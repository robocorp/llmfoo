import inspect
import json
import os
from typing import Callable, Dict, Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCall


def tool(func: Callable) -> Callable:
    file_path = inspect.getfile(func)
    json_file_path = file_path.replace('.py', '.tool.json')

    # Load existing data from .tool.json
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            existing_data = json.load(file)
    else:
        existing_data = {}

    # If the function's definition does not exist, extract metadata, generate schema, and update the file
    if func.__name__ not in existing_data:
        # Extract metadata using OpenAI API
        function_metadata = extract_metadata_with_openai_api(func)

        # Generate JSON schema from the metadata
        json_schema = generate_json_schema(function_metadata)

        # Update the .tool.json file with the new schema
        existing_data[func.__name__] = json_schema
        with open(json_file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
    else:
        # Use existing schema from the .tool.json file
        json_schema = existing_data[func.__name__]

    # Set definition to func.openai_xxx
    func.openai_schema = json_schema
    func.openai_tool_call = create_tool_call_handler(func, json_schema)
    func.openai_tool_output = create_tool_output_handler(func, json_schema)

    return func


def create_tool_output_handler(func: Callable, json_schema):
    def handler(msg: ChatCompletionMessageToolCall):
        if func.__name__ == msg.function.name:
            result = func(*json.loads(msg.function.arguments).values())
            return {
                "tool_call_id": msg.id,
                "output": str(result)
            }
        return None

    return handler


def create_tool_call_handler(func: Callable, json_schema):
    def handler(msg: ChatCompletionMessageToolCall):
        if func.__name__ == msg.function.name:
            result = func(*json.loads(msg.function.arguments).values())
            return {
                "role": "tool",
                "tool_call_id": msg.id,
                "name": msg.function.name,
                "content": str(result)
            }
        return None

    return handler


def extract_metadata_with_openai_api(func: Callable) -> Dict[str, Any]:
    source = inspect.getsource(func)
    client = OpenAI()
    instructions = f"""
Extract function metadata from the following function definition:
```python
{source}
```

Use the following Pydantic style JSON schema in your response:
```json
{schema}
```
""".rstrip()
    print(instructions)
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": instructions
            }
        ]
    )
    print(repr(response))
    metadata = response.choices[0].message.content
    print(metadata)
    return json.loads(metadata)  # Assuming the response is in JSON format


def generate_json_schema(metadata: Dict[str, Any]) -> Dict[str, Any]:
    func = metadata["function"]
    params = func["parameters"]
    props = params["properties"]
    return {
        "type": "function",
        "function": {
            "name": func["name"],
            "description": func["description"],
            "parameters": {
                "type": "object",
                "properties": {prop: {
                    "type": props[prop]["type"],
                    "description": props[prop]["description"]
                } for prop in props
                },
                "required": params["required"]
            },
        }
    }


schema = """
{
  "type": "function",
  "function": {
    "name": "<function_name>",
    "description": "<function_description>",
    "parameters": {
      "type": "object",
      "properties": {
        "<parameter1_name>": {
          "type": "<parameter1_type>",
          "description": "<parameter1_description>"
        },
        "<parameter2_name>": {
          "type": "<parameter2_type>",
          "description": "<parameter2_description>"
        }
        // Add more parameters as needed
      },
      "required": ["<required_parameter1_name>", "<required_parameter2_name>"]
      // List all required parameters
    }
  }
}
"""
