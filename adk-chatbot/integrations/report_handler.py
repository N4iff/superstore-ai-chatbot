"""
Report Handler - Coordinates Discord approval and Gmail delivery
"""
import asyncio
import re


async def process_report(parent_response: str):
    """
    Process a report from parent agent
    
    Checks if response contains REPORT CONTENT:
    If yes, sends to Discord for approval, then Gmail if approved
    
    Args:
        parent_response: The response from parent agent
        
    Returns:
        The user message portion (without report HTML)
    """
    # Check if this is a report response
    if "REPORT CONTENT:" not in parent_response:
        return parent_response
    
    # Extract report content and user message
    parts = parent_response.split("USER MESSAGE:", 1)
    
    if len(parts) != 2:
        return parent_response
    
    report_part = parts[0].replace("REPORT CONTENT:", "").strip()
    user_message = parts[1].strip()
    
    # Import here to avoid circular imports
    from integrations.discord_integration import send_report_for_approval
    from integrations.gmail_integration import send_report_email
    
    print("\n📊 Report generated! Sending to Discord for approval...")
    
    # Send to Discord for approval
    approved = await send_report_for_approval(report_part)
    
    if approved:
        print("✅ Report approved! Sending email...")
        success = send_report_email(report_part)
        
        if success:
            return user_message
        else:
            return "Report was approved but email sending failed. Please check your Gmail configuration."
    else:
        return "Report was not approved and will not be sent."


def extract_user_message(response: str) -> str:
    """
    Extract just the user message from a report response
    (synchronous version for compatibility)
    
    Args:
        response: The full response from parent agent
        
    Returns:
        Just the user-facing message
    """
    if "USER MESSAGE:" in response:
        parts = response.split("USER MESSAGE:", 1)
        if len(parts) == 2:
            return parts[1].strip()
    
    return response