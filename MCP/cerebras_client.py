import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_cerebras import ChatCerebras
import json
import os

from dotenv import load_dotenv
import re
class MCP_Client: 
    def __init__(self,config_file="MCP/mcp_servers.json"): 
        load_dotenv()
        with open(config_file) as f:
            config = json.load(f)
        project_root = os.environ.get("PROJECT_ROOT", os.getcwd())
        for server in config.values():
            if "args" in server:
                server["args"] = [arg.replace("${PROJECT_ROOT}", project_root) for arg in server["args"]]
            if "env" in server: 
                for key in server["env"]:
                    if re.match(r".*_API_KEY$", key):
                        server["env"][key] = os.getenv(key, "")
        self.client = MultiServerMCPClient(config)
        self.llm = ChatCerebras(
            model="gpt-oss-120b",
            temperature=0.2,
            max_tokens=10240,
            api_key=os.getenv("CEREBRAS_API_KEY")
        )
        self.agent = None

    async def setup(self):
        tools = await self.client.get_tools()
        print(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")
        self.agent = create_react_agent(self.llm, tools)

    async def serve_query(self, query):
        try:
            response = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": query}]},
                config={"recursion_limit": 50}
            )
            final_weather = response["messages"][-1].content
            print("Response:", final_weather)
            
            print(f"Total messages in conversation: {len(response['messages'])}")
            return final_weather
        
        except Exception as e:
            print(f"Error in query: {e}")

async def main():
    client = MCP_Client()
    await client.setup()
    prompt = input()
    while prompt!="quit": 
        await client.serve_query(query=prompt)
        prompt = input()

if __name__ == "__main__":
    asyncio.run(main())