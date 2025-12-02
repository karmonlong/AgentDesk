import sys
import os
from agents.multi_agents import multi_agent_system
from graph.daily_tech_graph import run_daily_tech_flow

# Mock environment variables if needed
# os.environ["GEMINI_API_KEY"] = "..." 

def test_daily_tech():
    print("Starting Daily Tech Flow Test...")
    try:
        keywords = ["AI", "Agent"]
        result = run_daily_tech_flow(keywords, days=1)
        print("Flow completed successfully.")
        print("Report length:", len(result.get("report", "")))
    except Exception as e:
        print(f"Flow failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_daily_tech()
