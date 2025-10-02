import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_cerebras import ChatCerebras

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
        }
    )
    
    # Load tools from all servers
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")
    
    # Initialize Cerebras chat model
    llm = ChatCerebras(
        model="llama3.1-8b",
        temperature=0.2,
        max_tokens=10240,
        parallel_tool_calls=False,
    )
    
    # Create ReAct agent with Cerebras + MCP tools
    # Add recursion_limit to config to increase the limit
    agent = create_react_agent(llm, tools)
    
    # Example math query - with increased recursion limit and debugging
    print("\n=== Math Query ===")
    try:
        math_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]},
            config={"recursion_limit": 50}  # Increase recursion limit
        )
        final_math = math_response["messages"][-1].content
        print("Math Response:", final_math)
        print(f"Total messages in conversation: {len(math_response['messages'])}")
    except Exception as e:
        print(f"Error in math query: {e}")
    
    # Example weather query
    print("\n=== Weather Query ===")
    try:
        weather_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "what is the weather in NYC?"}]},
            config={"recursion_limit": 50}
        )
        final_weather = weather_response["messages"][-1].content
        print("Weather Response:", final_weather)
        print(f"Total messages in conversation: {len(weather_response['messages'])}")
    except Exception as e:
        print(f"Error in weather query: {e}")



if __name__ == "__main__":
    asyncio.run(main())
