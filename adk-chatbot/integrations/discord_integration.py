"""
Discord Integration - Send reports for approval
"""
import discord
from discord import Client, Intents, Interaction
from discord.ui import Button, View
import asyncio
import io
from config.settings import DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID


class ReportApprovalView(View):
    """Discord view with Approve/Reject buttons. Email is sent when user clicks Approve."""

    def __init__(self, report_html: str, question: str = "BI Report"):
        super().__init__(timeout=None)
        self.report_html = report_html
        self.question = question

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve_button(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        from integrations.gmail_integration import send_report_email
        try:
            email_sent = send_report_email(
                self.report_html, subject=f"BI Report: {self.question}"
            )
            if email_sent:
                await interaction.followup.send("✅ Report approved! Email sent.", ephemeral=True)
            else:
                await interaction.followup.send("✅ Approved but email failed. Check Gmail config.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"✅ Approved but email error: {e}", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("❌ Report rejected.", ephemeral=True)
        self.stop()


class DiscordReportClient:
    """Discord client for sending reports for approval"""

    def __init__(self):
        self.token = DISCORD_BOT_TOKEN
        self.channel_id = None
        try:
            if DISCORD_CHANNEL_ID is not None and str(DISCORD_CHANNEL_ID).strip():
                self.channel_id = int(DISCORD_CHANNEL_ID)
        except (TypeError, ValueError):
            pass
        self.client = None
        self.ready = False

    async def start_client(self):
        """Start the Discord client (with timeout so we don't hang forever)."""
        if self.client is not None:
            return
        if not self.token or not str(self.token).strip():
            print("Discord: DISCORD_BOT_TOKEN is missing or empty in .env")
            return
        if self.channel_id is None:
            print("Discord: DISCORD_CHANNEL_ID is missing or invalid in .env (use the channel's numeric ID)")
            return
        # Use only default intents so the bot connects without enabling
        # privileged intents in the Discord Developer Portal. We only send
        # messages, we don't read message content.
        intents = Intents.default()
        self.client = Client(intents=intents)

        @self.client.event
        async def on_ready():
            self.ready = True
            print(f"Discord: Bot logged in as {self.client.user}")

        # Start client in background
        asyncio.create_task(self.client.start(self.token))

        # Wait for ready with timeout (15 sec)
        for _ in range(150):
            if self.ready:
                break
            await asyncio.sleep(0.1)
        if not self.ready:
            print("Discord: Connection timed out (check token and that the bot is not running elsewhere).")

    async def send_for_approval(
        self, report_html: str, question: str = "BI Report"
    ) -> bool:
        """
        Post report to Discord with Approve/Reject buttons.
        When user clicks Approve in Discord, email is sent from the button handler.
        """
        if not self.token or self.channel_id is None:
            return False
        if not self.ready:
            await self.start_client()
        if not self.ready or not self.client:
            print("Discord: Bot not connected. Check terminal for connection errors.")
            return False
        try:
            # fetch_channel works even if channel isn't in cache (get_channel can return None)
            channel = await self.client.fetch_channel(self.channel_id)
        except discord.Forbidden:
            print("Discord: Bot has no access to that channel (check permissions).")
            return False
        except discord.NotFound:
            print("Discord: Channel ID not found. Enable Developer Mode in Discord, right-click the channel, Copy ID.")
            return False
        except Exception as e:
            print(f"Discord: Failed to get channel: {e}")
            return False
        view = ReportApprovalView(report_html=report_html, question=question)
        try:
            msg = (
                "📊 **New Report Ready for Review**\n\n"
                "Please review the attached report and click Approve or Reject."
            )

            if len(report_html) <= 1500:
                await channel.send(
                    f"{msg}\n\n```html\n{report_html}\n```",
                    view=view,
                )
            else:
                html_file = discord.File(
                    io.BytesIO(report_html.encode("utf-8")),
                    filename="report.html",
                )
                await channel.send(msg, view=view, file=html_file)

            print(f"Discord: Report posted to channel {getattr(channel, 'name', self.channel_id)}.")
            return True
        except Exception as e:
            print(f"Discord: Failed to send message: {e}")
            return False
    
    async def close(self):
        """Close the Discord client"""
        if self.client:
            await self.client.close()


# Singleton instance
_discord_client = None


async def send_report_for_approval(
    report_html: str, question: str = "BI Report"
) -> bool:
    """
    Post report to Discord with Approve/Reject buttons. Returns immediately.
    When user clicks Approve in Discord, the report is sent to email from there.

    Args:
        report_html: The HTML report content
        question: Report question (used for email subject on approve)

    Returns:
        True if posted successfully
    """
    global _discord_client
    if _discord_client is None:
        _discord_client = DiscordReportClient()
        if not _discord_client.token or not str(_discord_client.token).strip():
            print("Discord: DISCORD_BOT_TOKEN is missing. Set it in adk-chatbot/.env")
        elif _discord_client.channel_id is None:
            print("Discord: DISCORD_CHANNEL_ID is missing or invalid. Set numeric channel ID in adk-chatbot/.env")
        else:
            print("Discord: Config OK (channel_id=%s). Bot will connect when first report is sent." % _discord_client.channel_id)
    return await _discord_client.send_for_approval(report_html, question=question)