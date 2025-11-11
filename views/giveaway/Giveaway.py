import json
import random
import discord

class Giveaway(discord.ui.LayoutView):
    def __init__(self, giveaway_config: dict):
        super().__init__(timeout=None)
        self.giveaway_config = giveaway_config
        self.set_embed()


    def set_embed(self) -> None:
        ongoing = [
            discord.ui.TextDisplay(
                content=("**Fin dans :** <t:{}:R>".format(self.giveaway_config["end_timestamp"])+ "\n**Nombre de participants :** {}".format(len(self.get_participants())))
            )
        ]
        finished = [
            discord.ui.TextDisplay(
                content="**Le giveaway est terminé !**"
            )
        ]

        container1 = discord.ui.Container(
            discord.ui.TextDisplay(
                content="## :tada: " + self.giveaway_config["prize"]
            ),
            *(ongoing if not self.giveaway_config.get("ended", False) else finished),
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small),
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Participer au giveaway",
                    emoji="🎉",
                    style=discord.ButtonStyle.primary,
                    custom_id="participe_giveaway",
                    disabled=self.giveaway_config.get("ended", False)
                )
            ),
            discord.ui.TextDisplay(
                content="-# Vous serez mentionné ici si vous gagnez le giveaway !" if not self.giveaway_config.get("ended", False) else "-# Vous ne pouvez plus participer car le giveaway est terminé."
            ),
            accent_color=discord.Color.gold() if not self.giveaway_config.get("ended", False) else discord.Color(0x331b01)
        )

        if len(self.children) > 0:
            self.remove_item(self.children[0])

        self.add_item(container1)

    def get_participants(self) -> list[int]:
        return self.giveaway_config.get("participants", [])

    async def add_participant(self, it: discord.Interaction):
        if "participants" not in self.giveaway_config:
            self.giveaway_config["participants"] = []
        if it.user.id not in self.giveaway_config["participants"]:
            self.giveaway_config["participants"].append(it.user.id)
            self.giveaway_config["participants_count"] = len(self.giveaway_config["participants"])

            self.set_embed()
            await it.response.edit_message(view=self)
            return await self.save()
        return await it.response.send_message('You have already participated in this giveaway!', ephemeral=True)

    async def roll(self, end: bool=True) -> int | None:
        self.giveaway_config["ended"] = end
        participants = self.get_participants()
        winners = []
        if participants:
            max_winners = self.giveaway_config.get("winners", 1)
            for _ in range(min(max_winners, len(participants))):
                winner_id = random.choice(participants)
                while winner_id in winners:
                    winner_id = random.choice(participants)
                winners.append(winner_id)
            await self.save()
            return winners

    async def save(self):
        with open('data/giveaways.json', 'r') as f:
            giveaways = json.load(f)

        for i, g in enumerate(giveaways):
            if g["message_id"] == self.giveaway_config["message_id"]:
                giveaways[i] = self.giveaway_config
                break

        with open('data/giveaways.json', 'w') as f:
            json.dump(giveaways, f, indent=4)

    async def interaction_check(self, interaction):
        iid = interaction.data.get("custom_id")
        if not self.giveaway_config.get("message_id"):
            self.giveaway_config["message_id"] = interaction.message.id
        if iid == "participe_giveaway":
            await self.add_participant(interaction)
            return False
        return True
