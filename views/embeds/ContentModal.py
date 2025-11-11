import discord

class ContentModal(discord.ui.Modal):
    def __init__(self, title: str, elements: list[discord.ui.TextInput, discord.ui.TextDisplay, discord.ui.Select]):
        super().__init__(title=title)
        for element in elements:
            self.add_item(element)

        self.response = []
        self.interaction = None

    async def on_submit(self, interaction: discord.Interaction):
        for item in self.children:
            if isinstance(item, discord.ui.TextInput):
                self.response.append(item.value)
            elif isinstance(item, discord.ui.Select):
                self.response.append(item.values)
            elif isinstance(item, discord.ui.Label):
                self.response.append(item.component.values)
        self.interaction = interaction
        self.stop()

