import inspect
import json
import os
from typing import Callable, TypedDict, Dict, Any

from openai import OpenAI


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

    # Set definition to func.openai_schema
    func.openai_schema = json_schema

    return func


def extract_metadata_with_openai_api(func: Callable) -> Dict[str, Any]:
    source = inspect.getsource(func)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": f"Extract function metadata from the following function definition:\n```\n{source}\n```\n"
            }
        ]
    )
    metadata = response.choices[0].message.content
    return json.loads(metadata)  # Assuming the response is in JSON format


def generate_json_schema(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": metadata["function_name"],
            "description": metadata["function_description"],
            "parameters": {
                "type": "object",
                "properties": {param["name"]: {
                    "type": param["type"],
                    "description": param["description"]
                } for param in metadata["parameters"]
                },
                "required": metadata["required_parameters"]
            },
        }
    }


function_schema = """
{
  "type": "function",
  "function": {
    "name": "<function_name>",
    "description": "<function_description>",
    "parameters": {
      "$ref": "#/definitions/parametersSchema"
    }
  },
  "definitions": {
    "parametersSchema": {
      // Parameter schema definition goes here
    }
  }
}
"""

parameter_schema = """
{
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "enum": ["string", "number", "integer", "boolean", "object", "array", "null"]
    },
    "description": {
      "type": "string"
    },
    "enum": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1
    }
  },
  "required": ["type", "description"],
  "dependencies": {
    "type": {
      "oneOf": [
        {
          "properties": {
            "type": {
              "const": "string"
            }
          }
        },
        {
          "properties": {
            "type": {
              "not": {
                "const": "string"
              }
            },
            "enum": {
              "not": {}
            }
          }
        }
      ]
    }
  }
}
"""

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


class FunctionDefinition(TypedDict):
    function_name: str
    function_description: str
    argument_description: str


def is_valid_function_definition(data: dict) -> bool:
    required_keys = ['function_name', 'function_description', 'argument_description']
    return all(key in data and isinstance(data[key], str) for key in required_keys)


def create_definition(func: Callable, goal: str) -> FunctionDefinition:
    source = inspect.getsource(func)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": f"""Extract function metadata from the following function definition:
```
{source}
```

Focus on details that are meaningful for the following assignment:
```
{goal}
```

Extract the function metadata.
""",
            }
        ],
        functions=[
            {
                "description": "FunctionDefinition is a tool for metadata extraction",
                "name": "FunctionDefinition",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thinking": {
                            "type": "string",
                            "description": (
                                "Logical thinking about function metadata extraction and draft of the answer."
                            ),
                        },
                        "function_name": {
                            "type": "string",
                            "description": "Name of the function.",
                        },
                        "function_description": {
                            "type": "string",
                            "description": "Short well thought description of what the function is used for.",
                        },
                        "argument_description": {
                            "type": "string",
                            "description": "Short well thought description of what the function argument is used for.",
                        },
                    },
                    "required": [
                        "thinking",
                        "function_name",
                        "function_description",
                        "argument_description",
                    ],
                },
            }
        ],
        function_call={"name": "FunctionDefinition"},
    )
    msg = response.choices[0].message
    assert msg.function_call
    print(msg.function_call)
    args: FunctionDefinition = json.loads(msg.function_call.arguments)

    if not is_valid_function_definition(args):
        raise ValueError("Invalid data format for FunctionDefinition")

    return args
