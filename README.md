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
from llmfoo import tool

# Example usage
@tool
def adder(x: int, y: int) -> int:
    return x + y

..
Function call from messages
adder.handle(message) -> result message or None

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
