import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_cerebras import ChatCerebras

async def main():
    """Main function using Cerebras with Data Commons MCP"""
    
    print("="*70)
    print("  🌐 Data Commons MCP Client (Cerebras + LangGraph)")
    print("="*70)
    print()
    
    # Initialize multi-server MCP client with Data Commons
    print("🔌 Connecting to MCP servers...")
    client = MultiServerMCPClient(
        {
            "datacommons": {
                "url": "http://localhost:8080/sse",
                "transport": "sse",
            },
            # You can add other servers here
            # "math": {
            #     "command": "python",
            #     "args": ["/home/uniqueusman/mcp/math_server.py"],
            #     "transport": "stdio",
            # },
        }
    )
    
    # Load tools from all servers
    print("🔧 Loading tools from MCP servers...")
    tools = await client.get_tools()
    
    print(f"✅ Loaded {len(tools)} tools:")
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool.name}")
        print(f"      Server: datacommons")
        print(f"      Description: {tool.description}")
    print()
    
    # Initialize Cerebras chat model
    print("🧠 Initializing Cerebras LLM...")
    llm = ChatCerebras(
        model="qwen-3-32b",  # or "qwen-3-32b"
        temperature=0.2,
        max_tokens=10240,
    )
    
    # Create ReAct agent
    print("🤖 Creating ReAct agent...")
    agent = create_react_agent(llm, tools)
    
    print("="*70)
    print("💬 Interactive Mode")
    print("   Ask questions about data from Data Commons")
    print("   Examples:")
    print("   - What is the population of California?")
    print("   - Compare GDP between USA and China")
    print("   - Show unemployment statistics for New York")
    print()
    print("   Commands:")
    print("   - 'tools' to list available tools")
    print("   - 'quit' or 'exit' to close")
    print("="*70)
    print()
    
    # Interactive loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'tools':
                print("\n📋 Available tools:")
                for tool in tools:
                    print(f"   • {tool.name}: {tool.description}")
                continue
            
            print("\n🤔 Thinking...\n")
            
            # Run the agent
            response = await agent.ainvoke(
                {"messages": [("user", user_input)]},
                config={"configurable": {"thread_id": "1"}}
            )
            
            # Extract the final answer
            messages = response["messages"]
            final_message = messages[-1]
            
            print("\n" + "="*70)
            print("📊 Answer:")
            print("-"*70)
            print(final_message.content)
            print("="*70)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print(f"   Type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print()
    
    # Cleanup
    await client.cleanup()

def run():
    """Entry point"""
    print("\n📦 Required packages:")
    print("   pip install langchain-mcp-adapters langgraph langchain-cerebras")
    print()
    print("🔑 Make sure you have set your Cerebras API key:")
    print("   export CEREBRAS_API_KEY='your-key-here'")
    print()
    print("🚀 Make sure your Data Commons MCP server is running on:")
    print("   http://localhost:8080/sse")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
