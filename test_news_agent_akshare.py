
import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Ensure the project root is in python path
sys.path.append(os.getcwd())

from agents.multi_agents import NewsAggregatorAgent
from services.mcp_service import mcp_manager

# Load environment variables
load_dotenv()

async def test_news_agent():
    print("Initializing NewsAggregatorAgent...")
    try:
        agent = NewsAggregatorAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    # Test query that should trigger a tool call
    query = "查询上证指数的实时行情数据"
    print(f"\nTesting query: {query}")
    
    messages = [HumanMessage(content=query)]
    
    try:
        response = await agent.invoke(messages)
        print("\nFinal Response:")
        print(response)
    except Exception as e:
        print(f"\nError during invocation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up MCP connections...")
        await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_news_agent())
