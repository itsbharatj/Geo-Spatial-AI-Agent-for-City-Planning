from langchain_cerebras import ChatCerebras

llm = ChatCerebras(
    model="llama-3.3-70b",
    # other params...
)

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
print(ai_msg)
