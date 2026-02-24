"""
Main entry point for Google ADK BI Chatbot
"""
import json
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from agents.parent_agent import create_parent_agent
from integrations.report_handler import process_report


def format_response(response):
    """Format the agent's response for display"""
    # Extract text from the response event
    if hasattr(response, 'content'):
        content = response.content
        if isinstance(content, Content):
            # Extract text from parts
            text_parts = []
            for part in content.parts:
                if hasattr(part, 'text'):
                    text_parts.append(part.text)
            return ''.join(text_parts)
        return str(content)
    elif isinstance(response, dict):
        return json.dumps(response, indent=2)
    else:
        return str(response)


async def run_chatbot_async():
    """Main chatbot loop (async)"""
    print("=" * 60)
    print("BI Analytics Chatbot (Google ADK)")
    print("=" * 60)
    print("\nType your questions or 'help' for guidance.")
    print("Type 'quit' or 'exit' to end the session.\n")
    
    # Initialize agents (Flow 2: Parent -> Validator <-> Analytics, Report)
    print("Initializing agents...")
    parent_agent = create_parent_agent()
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=parent_agent,
        app_name="bi_chatbot",
        session_service=session_service
    )
    
    # Create a session
    session = await session_service.create_session(
        app_name="bi_chatbot",
        user_id="test_user"
    )
    
    print("✅ Ready! Ask me anything about your business data.\n")
    
    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Have a great day!")
                break
            
            # Run the parent agent
            print("\nAssistant: ", end="", flush=True)
            
            # Create proper Content object
            user_content = Content(
                role="user",
                parts=[Part(text=user_input)]
            )
            
            # Run agent with proper parameters
            events = []
            async for event in runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=user_content
            ):
                events.append(event)
            
            # Get the final response
            if events:
                final_event = events[-1]
                response_text = format_response(final_event)
                
                # Process report if present
                if "REPORT CONTENT:" in response_text:
                    final_message = await process_report(response_text)
                    print(final_message)
                else:
                    print(response_text)
            print()
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            print("Please try again or type 'quit' to exit.\n")


def run_chatbot():
    """Wrapper to run async chatbot"""
    asyncio.run(run_chatbot_async())


def run_web_ui():
    """Launch the ADK web UI (browser-based chat interface)"""
    print("=" * 60)
    print("Launching ADK Web UI...")
    print("=" * 60)
    print("\nThe web interface will open in your browser.")
    print("Press Ctrl+C to stop the server.\n")
    
    # This will be implemented when we add the web UI
    # For now, just run CLI
    print("⚠️  Web UI not yet implemented. Using CLI mode instead.\n")
    run_chatbot()


if __name__ == "__main__":
    import sys
    
    # Check if user wants web UI
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        run_web_ui()
    else:
        run_chatbot()