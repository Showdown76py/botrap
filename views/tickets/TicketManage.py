import asyncio
from time import time
import discord


async def close_ticket(channel: discord.TextChannel, it=None):
    created_by: discord.Member = channel.guild.get_member(int(channel.topic))
    async for last_message in channel.history(limit=1):
        last_message: discord.Message = last_message

    if it:
        await it.response.send_message("Fermeture du ticket dans <t:{}:R>".format(int(time())+10))
    else:
        await channel.send("Fermeture du ticket dans <t:{}:R>".format(int(time())+10))
    await asyncio.sleep(9)

    close_msg = "# Votre ticket a été fermé\n"
    if last_message.author != created_by and not last_message.author.bot:
        close_msg += f"**Dernier message du staff:**\n> "
        close_msg += last_message.content

    try:
        await created_by.send(close_msg)
    except: pass

    await channel.delete()
    
class TicketManage(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container1 = discord.ui.Container(
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Fermer",
                    emoji="🔒",
                    style=discord.ButtonStyle.danger,
                    custom_id="close_ticket"
                )
            )
        )

        self.add_item(container1)
    
    async def interaction_check(self, interaction):
        iid = interaction.data.get("custom_id")
        if iid == "close_ticket":
            await close_ticket(interaction.channel, interaction)
            return True
        return False
