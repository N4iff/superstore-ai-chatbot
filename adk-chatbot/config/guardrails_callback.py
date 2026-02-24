"""
Guardrails Plugin - Uses ADK's built-in callback system to protect sensitive data
This plugin checks requests and SQL queries BEFORE they execute
"""
from typing import Any, Optional


# Define sensitive columns that should never be accessed
SENSITIVE_COLUMNS = [
    'personal_email',
    'email',
    'phone',
    'phone_number',
    'ssn',
    'social_security',
    'credit_card',
    'password',
]

# Sensitive keywords in user requests
SENSITIVE_KEYWORDS = [
    'email',
    'e-mail',
    'mail address',
    'phone',
    'telephone',
    'contact',
    'ssn',
    'social security',
    'credit card',
    'personal info',
    'personal information',
    'pii',
]


def check_for_sensitive_data(text: str) -> bool:
    """
    Check if text contains references to sensitive data
    
    Args:
        text: The text to check (user request or SQL query)
        
    Returns:
        True if sensitive data detected, False otherwise
    """
    text_lower = text.lower()
    
    # Check for SELECT *
    if 'select *' in text_lower:
        return True
    
    # Check for sensitive keywords
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in text_lower:
            return True
    
    # Check for sensitive columns
    for column in SENSITIVE_COLUMNS:
        if column.lower() in text_lower:
            return True
    
    return False


def before_tool_callback(
    tool: Any,
    args: dict[str, Any],
    tool_context: Optional[Any] = None,
    **kwargs: Any,
) -> Optional[dict]:
    """
    ADK Callback - Called BEFORE any tool executes
    Blocks tools that try to access sensitive data
    
    Args:
        tool: The tool being called
        args: The arguments being passed to the tool
        
    Returns:
        None to allow execution, or dict to block with custom response
    """
    # Get the tool name
    tool_name = getattr(tool, 'name', str(tool))
    
    # Only check database-related tools
    if 'execute_query' not in tool_name and 'analytics' not in tool_name:
        return None  # Allow non-database tools
    
    # Check all arguments for sensitive data
    for arg_name, arg_value in args.items():
        if isinstance(arg_value, str):
            if check_for_sensitive_data(arg_value):
                # BLOCK: Return error response instead of executing tool
                print(f"🛡️ GUARDRAIL BLOCKED: Sensitive data detected in {tool_name}")
                print(f"   Argument: {arg_name}")
                print(f"   Contains: personal_email or other PII keywords")
                return {
                    "status": "blocked",
                    "error": "Access to sensitive personal information is not permitted",
                    "results": []
                }
    
    # SAFE: Allow tool to execute
    return None