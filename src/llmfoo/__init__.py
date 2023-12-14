from openai import OpenAI


def is_statement_true(statement: str, criteria: str = "statement should be true") -> bool:
    client = OpenAI()
    instructions = f"""
We have a statement "{statement}".
Based on the following criteria: "{criteria}" is the statement true?
""".rstrip()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": instructions
            }
        ],
        logit_bias={
            "1904": 100,  # true
            "3934": 100  # false
        },
        max_tokens=1,
        temperature=0
    )
    result = response.choices[0].message.content
    return result == "true"
