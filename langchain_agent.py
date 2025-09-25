from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
from calendar_agent import CalendarAgent, MeetingInfo
from typing import List, Dict, Any
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LangChainCalendarAgent:
    """LangChain wrapper for the Calendar Agent with enhanced agentic capabilities"""
    
    def __init__(self):
        self.calendar_agent = CalendarAgent()
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for calendar operations"""
        
        def get_next_meeting_tool(query: str) -> str:
            """Get information about the next upcoming meeting"""
            meeting_info = self.calendar_agent.get_next_meeting_info()
            if meeting_info:
                return json.dumps({
                    "meeting_title": meeting_info.meeting_title,
                    "person_names": meeting_info.person_names,
                    "start_time": meeting_info.start_time.isoformat() if meeting_info.start_time else None,
                    "description": meeting_info.original_description
                }, indent=2)
            return "No upcoming meetings found"
        
        def search_meetings_tool(query: str) -> str:
            """Search for meetings by keyword. Input should be the search keyword."""
            meetings = self.calendar_agent.search_meetings_by_keyword(query, max_results=5)
            if meetings:
                results = []
                for meeting in meetings:
                    results.append({
                        "meeting_title": meeting.meeting_title,
                        "person_names": meeting.person_names,
                        "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                        "description": meeting.original_description[:200] + "..." if len(meeting.original_description) > 200 else meeting.original_description
                    })
                return json.dumps(results, indent=2)
            return f"No meetings found for keyword: {query}"
        
        def get_meetings_for_date_tool(date_str: str) -> str:
            """Get all meetings for a specific date. Input should be in YYYY-MM-DD format."""
            try:
                day_events = self.calendar_agent.get_events_for_day(date_str)
                if day_events.total_events > 0:
                    results = []
                    for meeting in day_events.meetings:
                        results.append({
                            "meeting_title": meeting.meeting_title,
                            "attendee_names": meeting.get_attendee_display_names(),
                            "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                            "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
                            "description": meeting.original_description,
                            "location": meeting.location,
                            "organizer": meeting.organizer_name or meeting.organizer_email
                        })
                    return json.dumps(results, indent=2)
                return f"No meetings found for date: {date_str}"
            except Exception as e:
                return f"Error getting meetings for {date_str}: {str(e)}"
        
        def get_meeting_by_id_tool(event_id: str) -> str:
            """Get specific meeting information by event ID"""
            meeting_info = self.calendar_agent.get_meeting_info_by_id(event_id)
            if meeting_info:
                return json.dumps({
                    "meeting_title": meeting_info.meeting_title,
                    "person_names": meeting_info.person_names,
                    "start_time": meeting_info.start_time.isoformat() if meeting_info.start_time else None,
                    "description": meeting_info.original_description
                }, indent=2)
            return f"Meeting not found for ID: {event_id}"
        
        return [
            Tool(
                name="get_next_meeting",
                func=get_next_meeting_tool,
                description="Get information about the next upcoming meeting including title, attendees, and description"
            ),
            Tool(
                name="get_meetings_for_date",
                func=get_meetings_for_date_tool,
                description="Get all meetings for a specific date. Input should be in YYYY-MM-DD format. This is the PRIMARY tool to use when asked for meetings on a specific date."
            ),
            Tool(
                name="search_meetings",
                func=search_meetings_tool,
                description="Search for meetings by keyword in title or description. Useful for finding specific types of meetings like 'interview', 'standup', 'review', etc."
            ),
            Tool(
                name="get_meeting_by_id",
                func=get_meeting_by_id_tool,
                description="Get detailed information about a specific meeting using its event ID"
            )
        ]
    
    def _create_agent(self):
        """Create the LangChain ReAct agent"""
        
        prompt_template = """You are a helpful calendar assistant that can access Google Calendar data and extract meeting information.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

When extracting person names and meeting titles, be thorough and accurate. 
If multiple people are mentioned, list them all.
If the meeting title in the description is more descriptive than the calendar title, prefer the description version.

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )
        
        return create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    def run(self, query: str) -> str:
        """Run the agent with a given query"""
        agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5
        )
        
        try:
            result = agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"Error executing agent: {str(e)}"

def main():
    """Example usage of the LangChain Calendar Agent"""
    print("🤖 Initializing LangChain Calendar Agent...")
    
    try:
        agent = LangChainCalendarAgent()
        print("✅ Agent initialized successfully!")
        
        # Example queries
        test_queries = [
            "What is my next meeting? Who am I meeting with and what is the meeting title?",
            "Search for any interview meetings and tell me who I'm interviewing",
            "Find meetings with the word 'standup' and list the attendees",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"📋 Query {i}: {query}")
            print('='*60)
            
            response = agent.run(query)
            print(f"🤖 Response: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("1. Google Calendar credentials set up")
        print("2. OpenAI API key in your environment")
        print("3. All required packages installed")

if __name__ == "__main__":
    main()
