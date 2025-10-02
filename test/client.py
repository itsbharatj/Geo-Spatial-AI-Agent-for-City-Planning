import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async def main():
    # Initialize multi-server MCP client
    client = MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                # Full absolute path to your math_server.py
                "args": ["/home/uniqueusman/mcp/math_server.py"],
                "transport": "stdio",
            },
            "weather": {
                # HTTP server running on localhost:8000
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",
            },
            # Add more servers here if needed
        }
    )

    # Load tools from all servers
    tools = await client.get_tools()

    # Create the ReAct agent using OpenAI directly
    agent = create_react_agent("openai:gpt-4.1", tools)

    # Ask math question
    math_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
    final_math = math_response["messages"][-1].content
    print("Math Response:", final_math)

    # Ask weather question
    weather_response = await agent.ainvoke({"messages": "what is the weather in NYC?"})
    final_weather = weather_response["messages"][-1].content
    print("Weather Response:", final_weather)


if __name__ == "__main__":
    asyncio.run(main())

