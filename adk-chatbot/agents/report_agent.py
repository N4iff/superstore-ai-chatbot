"""
Report Agent - Generates executive summary reports
Returns raw status for Parent to validate
"""
import asyncio
from datetime import datetime
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from config.settings import MODEL_NAME
import openai
from config.settings import OPENAI_API_KEY


def create_report_agent() -> LlmAgent:
    """Create Report agent."""

    async def generate_and_send_report(
        question: str, results: str, insight: str
    ) -> str:
        """Generate HTML report and send to Discord. Returns STATUS/RESULTS/INSIGHT."""
        from integrations.discord_integration import send_report_for_approval

        today = datetime.now().strftime("%B %d, %Y")

        report_instruction = f"""
You are a Senior BI Report Writer.
Create an executive summary report in HTML.

Structure:
<h1>REPORT TITLE: BI Analytics Report — [topic]</h1>
<p><strong>DATE:</strong> {today}<br><strong>PREPARED BY:</strong> BI Analytics System</p>
<hr>
<h2>EXECUTIVE SUMMARY</h2>
<p>[1-2 sentences]</p>
<hr>
<h2>KEY FINDINGS</h2>
<div class="metric-group">
[formatted findings]
</div>
<hr>
<h2>KEY INSIGHT</h2>
<p>[one sentence]</p>
<hr>
<h2>RECOMMENDATION</h2>
<p>[one actionable sentence]</p>

Rules:
- Use ONLY the data provided
- Currency: $
- Percentages: %
- 2 decimal places
- Output ONLY HTML (no preamble)
"""
        
        try:
            # Generate report (sync OpenAI call inside async tool is acceptable here)
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": report_instruction},
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nResults: {results}\n\nInsight: {insight}",
                    },
                ],
            )

            html_report = response.choices[0].message.content

            # Send to Discord (await the coroutine inside existing event loop)
            try:
                sent = await asyncio.wait_for(
                    send_report_for_approval(html_report, question=question),
                    timeout=12.0,
                )

                if sent:
                    return (
                        "STATUS: success\n"
                        "RESULTS: Report sent to Discord for approval\n"
                        "INSIGHT: Check Discord channel"
                    )
                return (
                    "STATUS: error\n"
                    "RESULTS: Failed to send to Discord\n"
                    "INSIGHT: Check bot token/channel ID"
                )

            except asyncio.TimeoutError:
                return (
                    "STATUS: error\n"
                    "RESULTS: Discord timeout while sending report\n"
                    "INSIGHT: Try again later or check connectivity"
                )
            except Exception as e:
                return (
                    "STATUS: error\n"
                    f"RESULTS: Discord error: {str(e)}\n"
                    "INSIGHT: Check configuration"
                )

        except Exception as e:
            return (
                "STATUS: error\n"
                f"RESULTS: Report generation failed: {str(e)}\n"
                "INSIGHT: Check OpenAI API"
            )
    
    report_tool = FunctionTool(func=generate_and_send_report)
    
    instruction = """
You are a Report Generation Specialist.

When you receive a request, extract QUESTION, RESULTS, and INSIGHT from it (they may be labeled "QUESTION:", "RESULTS:", "INSIGHT:" or similar). Then:
1. Call generate_and_send_report(question=..., results=..., insight=...) with those three values
2. Return ONLY the exact string the tool returns (the STATUS/RESULTS/INSIGHT block). No preamble, no "I have sent...", no extra words. The Parent will pass this to the validator; it must see the raw STATUS line.
"""
    
    return LlmAgent(
        name="report_agent",
        model=LiteLlm(model=MODEL_NAME),
        instruction=instruction,
        tools=[report_tool],
        description="Generates executive summary reports and sends to Discord."
    )