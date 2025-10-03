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
                "args": ["/home/uniqueusman/mcp/math_server.py"],
                "transport": "stdio",
            },
            "weather": {
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",
            },
            "duckduckgo": {
                "command": "docker",
                "args": [
                    "run",
                    "-i",
                    "--rm",
                    "mcp/duckduckgo"
                ],
                "transport": "stdio",
            },
        }
    )
    
    # Load tools from all servers
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")
    
    # Initialize Cerebras chat model
    llm = ChatCerebras(
        model="qwen-3-32b",
        temperature=0.2,
        max_tokens=10240,
    )
    
    # Create ReAct agent
    agent = create_react_agent(llm, tools)
    
    # Example math query
    print("\n=== Math Query ===")
    try:
        math_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]},
            config={"recursion_limit": 50}
        )
        final_math = math_response["messages"][-1].content
        print("Math Response:", final_math)
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
    except Exception as e:
        print(f"Error in weather query: {e}")
    
    # Example DuckDuckGo search query
    print("\n=== DuckDuckGo Search Query ===")
    try:
        search_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What is the networth of Elon Musk"}]},
            config={"recursion_limit": 50}
        )
        final_search = search_response["messages"][-1].content
        print("Search Response:", final_search)
        print(f"Total messages in conversation: {len(search_response['messages'])}")
    except Exception as e:
        print(f"Error in search query: {e}")

if __name__ == "__main__":
    asyncio.run(main())
