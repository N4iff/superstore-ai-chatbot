"""
Root agent with ADK Guardrails using callbacks
"""
from agents.parent_agent import create_parent_agent
from config.guardrails_callback import before_tool_callback


# Create root agent
root_agent = create_parent_agent()

# Apply guardrails callback to the agent
# This will be called BEFORE every tool execution
root_agent.before_tool_callback = before_tool_callback

print("✅ Agent loaded with guardrails enabled")
print("🛡️ Protected columns: personal_email, phone, ssn, credit_card")