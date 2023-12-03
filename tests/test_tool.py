from llmfoo.functions import tool


@tool
def adder(x: int, y: int) -> int:
    return x + y
