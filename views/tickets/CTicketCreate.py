import discord

from views.tickets.TicketManage import TicketManage

class CTicketCreate(discord.ui.LayoutView):
    def __init__(self, ticket_config: dict):
        super().__init__(timeout=None)
        self.ticket_config = ticket_config

        container1 = discord.ui.Container(
            discord.ui.TextDisplay(
                content="## " + ticket_config["embed"]["title"]
            ),
            discord.ui.TextDisplay(
                content=ticket_config["embed"]["description"]
            ),
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small),
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Créer un ticket",
                    emoji="🎫",
                    style=discord.ButtonStyle.primary,
                    custom_id=ticket_config["embed"]["custom_id"]
                )
            ),
            accent_color=discord.Color(ticket_config["embed"]["color"]) if ticket_config["embed"]["color"] else None
        )

        self.add_item(container1)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        iid = interaction.data.get("custom_id")
        if iid == self.ticket_config["embed"]["custom_id"]:
            cat = interaction.guild.get_channel(self.ticket_config["category"]) if self.ticket_config["category"] else None
            ticket_channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=cat,
                topic=f"{interaction.user.id}"
            )
            await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

            await ticket_channel.send(self.ticket_config["inboard_message"].replace('{user}', interaction.user.mention))
            await ticket_channel.send(content=None, view=TicketManage())
            await interaction.response.send_message(f"**Votre ticket a été créé !**\n> {ticket_channel.mention}", ephemeral=True)

