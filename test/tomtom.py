import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_cerebras import ChatCerebras


load_dotenv()

async def main():
    """Main function using OpenAI with TomTom MCP"""
    
    print("="*70)
    print("  🗺️  TomTom MCP Client (OpenAI + LangGraph)")
    print("="*70)
    print()
    print(os.getenv("TOMTOM_API_KEY"))
    
    # Initialize multi-server MCP client with TomTom
    print("🔌 Connecting to MCP servers...")
    client = MultiServerMCPClient(
        {
            "tomtom": {
                "command": "npx",
                "args": ["-y", "@tomtom-org/tomtom-mcp@latest"],
                "transport": "stdio",
                "env": {
                    "TOMTOM_API_KEY": os.getenv("TOMTOM_API_KEY")
                }
            }
        }
    )
    
    # Load tools from all servers
    print("🔧 Loading tools from MCP servers...")
    tools = await client.get_tools()
    
    print(f"✅ Loaded {len(tools)} tools:")
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool.name}")
        desc = tool.description[:80] if len(tool.description) > 80 else tool.description
        print(f"      Description: {desc}")
    print()
    
    # Initialize OpenAI chat model
    print("🧠 Initializing OpenAI LLM...")
    # llm = ChatOpenAI(
    #     model="gpt-4o-mini",  # or "gpt-4o" for better performance
    #     temperature=0.2,
    # )

    llm = ChatCerebras(
            model="gpt-oss-120b",
            temperature=0.2,
            max_tokens=10240,
            api_key=os.getenv("CEREBRAS_API_KEY")
        )

    
    # Create ReAct agent
    print("🤖 Creating ReAct agent...")
    agent = create_react_agent(llm, tools)
    
    print("="*70)
    print("💬 Interactive Mode")
    print("   Ask questions about maps, navigation, and location data")
    print("   Examples:")
    print("   - Find restaurants in New York")
    print("   - Get directions from Paris to London")
    print("   - Search for hotels near Central Park")
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
    print("   pip install langchain-mcp-adapters langgraph langchain-openai")
    print()
    print("🔑 API keys configured:")
    print("   ✅ TOMTOM_API_KEY set in code")
    print("   ⚠️  Make sure OPENAI_API_KEY is exported:")
    print("   export OPENAI_API_KEY='your-openai-key'")
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
