"""
Report Agent - Generates executive summary reports
SUPPORTS: Analytics Reports + Compliance Reports
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
    """Create Report agent with both analytics and compliance report capabilities."""

    async def generate_analytics_report(
        question: str, results: str, insight: str
    ) -> str:
        """Generate HTML analytics report and send to Discord."""
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

            try:
                sent = await asyncio.wait_for(
                    send_report_for_approval(html_report, question=question),
                    timeout=12.0,
                )

                if sent:
                    return "STATUS: success\nRESULTS: Analytics report sent to Discord\nINSIGHT: Check Discord for approval"
                return "STATUS: error\nRESULTS: Failed to send to Discord\nINSIGHT: Check bot token/channel ID"

            except asyncio.TimeoutError:
                return "STATUS: error\nRESULTS: Discord timeout\nINSIGHT: Try again later"
            except Exception as e:
                return f"STATUS: error\nRESULTS: Discord error: {str(e)}\nINSIGHT: Check configuration"

        except Exception as e:
            return f"STATUS: error\nRESULTS: Report generation failed: {str(e)}\nINSIGHT: Check OpenAI API"
    

    async def generate_compliance_report(compliance_summary: str) -> str:
        """Generate HTML compliance report and send to Discord."""
        from integrations.discord_integration import send_report_for_approval

        today = datetime.now().strftime("%B %d, %Y")

        report_instruction = f"""
You are a Compliance Report Writer specializing in AI Ethics.
Create a professional compliance consultation report in HTML (bilingual: Arabic & English).

Structure:
<h1>📋 تقرير استشارة الامتثال - مبادئ سدايا<br>Compliance Consultation Report - SDAIA AI Principles</h1>
<p><strong>DATE / التاريخ:</strong> {today}<br><strong>PREPARED BY / أعد بواسطة:</strong> AI Compliance System</p>
<hr>

<h2>📌 ملخص تنفيذي / Executive Summary</h2>
<p>[1-2 sentences in Arabic and English about the consultation]</p>
<hr>

<h2>📖 الاستشارات والمراجع / Consultations & References</h2>
[For each Q&A, create a section:]
<div class="compliance-item">
<h3>السؤال / Question [N]:</h3>
<p>[question text]</p>
<h3>الإجابة / Answer:</h3>
<p>[answer with highlights for key principles]</p>
<p><strong>📖 المراجع / References:</strong> صفحة [X], صفحة [Y]</p>
</div>
<hr>

<h2>✅ الخلاصة / Summary</h2>
<p>تمت استشارة [X] أسئلة حول مبادئ أخلاقيات الذكاء الاصطناعي<br>
Consulted on [X] questions about AI ethics principles</p>

Rules:
- Bilingual (Arabic + English)
- Highlight key principles
- Include page citations
- Output ONLY HTML (no preamble)
"""
        
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": report_instruction},
                    {
                        "role": "user",
                        "content": f"Compliance Summary:\n\n{compliance_summary}",
                    },
                ],
            )

            html_report = response.choices[0].message.content

            try:
                sent = await asyncio.wait_for(
                    send_report_for_approval(html_report, question="SDAIA Compliance Consultation"),
                    timeout=12.0,
                )

                if sent:
                    return "STATUS: success\nRESULTS: Compliance report sent to Discord\nINSIGHT: SDAIA consultation summary delivered"
                return "STATUS: error\nRESULTS: Failed to send to Discord\nINSIGHT: Check bot token/channel ID"

            except asyncio.TimeoutError:
                return "STATUS: error\nRESULTS: Discord timeout\nINSIGHT: Try again later"
            except Exception as e:
                return f"STATUS: error\nRESULTS: Discord error: {str(e)}\nINSIGHT: Check configuration"

        except Exception as e:
            return f"STATUS: error\nRESULTS: Failed: {str(e)}\nINSIGHT: Check OpenAI API"
    
    # Create tools
    analytics_report_tool = FunctionTool(func=generate_analytics_report)
    compliance_report_tool = FunctionTool(func=generate_compliance_report)
    
    instruction = """
You handle TWO types of reports:

1. ANALYTICS REPORTS (Business Data)
2. COMPLIANCE REPORTS (SDAIA AI Ethics)

IDENTIFY TYPE:

ANALYTICS:
- Has: "QUESTION:", "RESULTS:", "INSIGHT:"
- About: sales, profit, business metrics
→ Use: generate_analytics_report(question, results, insight)

COMPLIANCE:
- Has SDAIA Q&As in Arabic/English
- About: AI ethics, data protection
- Has citations: "صفحة X"
→ Use: generate_compliance_report(compliance_summary)

CRITICAL: Return ONLY the exact STATUS/RESULTS/INSIGHT from the tool. No extra text.
"""
    
    return LlmAgent(
        name="report_agent",
        model=LiteLlm(model=MODEL_NAME),
        instruction=instruction,
        tools=[analytics_report_tool, compliance_report_tool],
        description="Generates analytics and compliance reports, sends to Discord."
    )