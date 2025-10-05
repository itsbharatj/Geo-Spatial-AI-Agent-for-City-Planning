from cerebras_client import MCP_Client
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_cerebras import ChatCerebras
from pydantic import BaseModel
import json
from cerebras.cloud.sdk import Cerebras
import os
from dotenv import load_dotenv
import asyncio
from loguru import logger


'''

    Overall Query runner: 

        - Taking the input
        - Breaking the query into multiple sub-queries which can be retrived using our data sources/ML models
        - Storing these queries into a dictionary to process it one by one
        - Serve each of these individual queries with the relevant context  
        - Keep storing the output in a JSON 

    After all the queries have ran, pass all the information the the LLM for report generation 
    Pass the corresponding data points to graph service to be displayed on the frontend
    
'''

load_dotenv()

class InputBreakdown(BaseModel): 
    subquestions: list[str]


class cityplanning_query_runner: 
    def __init__(self,original_user_query,location_coordiantes=None): 
        

        ## Define the modules
        self.LLM_Client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))
        self.results_path = os.makedirs("MCP/processed_prompts",exist_ok=True)

        prompts_file = "MCP/prompts.json"
        with open(prompts_file, 'r') as f:
            self.prompts = json.load(f)

        self.MCP_client = MCP_Client()
        self.model = "llama-3.3-70b"
        self.llm = ChatCerebras(
            model=self.model,  
        )
        
        self.query_title = self.llm.invoke([("system",self.prompts["User Query Title"]),("human",original_user_query)])
        print(self.query_title.content)
        self.file_path = f"MCP/processed_prompts/{self.query_title.content}"
        

        logger.add(self.file_path,format="{message}",mode="a")
        logger.info(f"Original User Question: {original_user_query}")

        self.original_user_query = original_user_query
        self.coordinates = location_coordiantes  
    
    async def main_runner(self):
        await self.MCP_client.setup()

        ## Break the user query into multiple sub-prompts to look at it from all the different angles
        sub_queries_format = InputBreakdown.model_json_schema()
        print(sub_queries_format)

        sub_queries = self.LLM_Client.chat.completions.create(
            model = self.model, 
            messages = [
                {"role":"system","content":self.prompts["User Query Breakdown"]}, 
                {"role":"user","content":self.original_user_query}
            ], 
            response_format= {
            "type": "json_schema",
            "json_schema": {
                "name": "input_breakdown",
                "strict": True,
                "schema": sub_queries_format
            }
            }

        )
        

        subquestions = json.loads(sub_queries.choices[0].message.content)["subquestions"]
        num_sub_queries = len(subquestions)

        for i in range(num_sub_queries):
            ## Calling the agent for each of the sub-query here\
            logger.add(self.file_path,format="{message}",mode="a")
            logger.info(f"Sub Question {i}: {subquestions[i]}")

            response = await self.MCP_client.serve_query(query=subquestions[i])

            logger.add(self.file_path,format="{message}",mode="a")
            logger.info(f"Response {i}: {response}")
        



async def main(): 
    user_query = input("What is the query?")
    agent = cityplanning_query_runner(user_query)
    await agent.main_runner()

if __name__ == "__main__":
    asyncio.run(main()) 
