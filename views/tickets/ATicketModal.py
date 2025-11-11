import json
import traceback
import uuid
import discord

from views.tickets.CTicketCreate import CTicketCreate

class ATicketModal(discord.ui.Modal):
    def __init__(self, prev_it: discord.Interaction, channel: discord.TextChannel):
        super().__init__(title="Embed création ticket")
        self.prev_it = prev_it
        self.channel = channel

        # Avoid shadowing Modal.title (must remain a string)
        self.embed_title_input = discord.ui.TextInput(
            label="Titre de l'embed",
            placeholder="Entrez le titre de l'embed",
            default="Ticket d'assistance",
            min_length=5,
            max_length=40,
            required=True
        )
        self.description_input = discord.ui.TextInput(
            label="Description de l'embed",
            placeholder="Entrez la description de l'embed",
            default="Cliquez sur le bouton ci-dessous pour créer un ticket.",
            style=discord.TextStyle.paragraph,
            min_length=5,
            max_length=200,
            required=True
        )
        self.inboard_message_input = discord.ui.TextInput(
            label="Message dans le ticket",
            placeholder="Entrez le message à envoyer dans le ticket. {user} pour mentionner l'utilisateur.",
            default="Votre ticket a été créé, {user} ! Un membre du support vous assistera bientôt.",
            style=discord.TextStyle.paragraph,
            min_length=5,
            max_length=300,
            required=True
        )
        self.color_input = discord.ui.TextInput(
            label="Couleur de l'embed (hex)",
            placeholder="Hexadécimal (ex: #3498db)",
            min_length=6,
            max_length=7,
            required=False
        )

        # Add all TextInput items to the modal
        self.add_item(self.embed_title_input)
        self.add_item(self.description_input)
        self.add_item(self.inboard_message_input)
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        # convert hex color to int
        color_value = None
        if self.color_input.value:
            try:
                color_value = int(self.color_input.value.lstrip('#'), 16)
            except ValueError:
                await interaction.response.send_message("Couleur hexadécimale invalide. Utilisation de la couleur par défaut.", ephemeral=True)

        ticket_config = {
            "embed": {
                "title": self.embed_title_input.value,
                "description": self.description_input.value,
                "color": color_value,
                "custom_id": str(uuid.uuid4()).replace('-', '')
            },
            "inboard_message": self.inboard_message_input.value,
            "category": self.channel.category_id if self.channel.category else None,
            "message_id": None,
            "channel_id": self.channel.id
        }

        m: discord.Message = await self.channel.send(
            content=None,
            view=CTicketCreate(ticket_config)
        )

        await interaction.response.send_message("Le système de ticket a été configuré avec succès !\n> " + m.jump_url, ephemeral=True)

        with open('data/ticket_config.json', 'r') as f:
            configs = json.load(f)
        configs.append(ticket_config)
        with open('data/ticket_config.json', 'w') as f:
            json.dump(configs, f, indent=4)


    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Une erreur est survenue lors de la soumission du modal.", ephemeral=True)
        traceback.print_exc()
