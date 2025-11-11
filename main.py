import asyncio
import discord, json, os, traceback
from discord import app_commands
from discord.ext import tasks

from dc.Emojis import Emojis
from views.giveaway.Giveaway import Giveaway
from views.tickets.CTicketCreate import CTicketCreate
from views.tickets.TicketManage import TicketManage, close_ticket
from views.tickets.ATicketModal import ATicketModal
from views.embeds.CCustomEmbed import CCustomEmbed

intents = discord.Intents.default()
intents.message_content = True
app = discord.Client(intents=intents)
tree = app_commands.CommandTree(app)
SYNC = True

with open("config.json", "r") as f:
    config = json.load(f)

GUILD_ID = config.get("guild_id") or os.getenv("DISCORD_GUILD_ID")
GUILD_OBJ = discord.Object(id=int(GUILD_ID)) if GUILD_ID else None


@app.event
async def on_ready():
    if SYNC:
        if GUILD_OBJ:
            await tree.sync(guild=GUILD_OBJ)
        else:
            await tree.sync()

    where = f"guild {GUILD_ID}" if GUILD_OBJ else "global"
    print(f"Logged in as {app.user}" + (f" and synced commands ({where})." if SYNC else ""))

    # Checking data files
    if not os.path.exists('data'):
        os.makedirs('data')

    if not os.path.exists('data/embeds_config.json'):
        with open('data/embeds_config.json', 'w') as f:
            json.dump([], f)
    if not os.path.exists('data/sticky_config.json'):
        with open('data/sticky_config.json', 'w') as f:
            json.dump([], f)
    if not os.path.exists('data/ticket_config.json'):
        with open('data/ticket_config.json', 'w') as f:
            json.dump([], f)
    if not os.path.exists('data/giveaways.json'):
        with open('data/giveaways.json', 'w') as f:
            json.dump([], f)

    # Persistance
    # Close ticket
    app.add_view(TicketManage())

    # Ticket creation
    with open("data/ticket_config.json", "r") as f:
        configs = json.load(f)
        for ticket_config in configs:
            app.add_view(CTicketCreate(ticket_config))

    # Custom embeds
    with open("data/embeds_config.json", "r") as f:
        configs = json.load(f)
        for embed_config in configs:
            app.add_view(CCustomEmbed(embed_config, editor=False))

    # Giveaways
    with open("data/giveaways.json", "r") as f:
        configs = json.load(f)
        for giveaway_config in configs:
            app.add_view(Giveaway(giveaway_config))


    ## Tasks
    giveaway_check.start()

@tree.command(name="setup-ticket", description="Mettre en place un système de ticket.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="Le channel où sera l'embed pour créer un ticket")
async def setup_ticket(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(ATicketModal(interaction, channel))

# EMBEDS
embed_group = app_commands.Group(
    name="embed",
    description="Commandes pour gérer les embeds."
)
sticky_group = app_commands.Group(
    name="sticky",
    description="Commandes pour gérer les messages épinglés."
)
giveaway_group = app_commands.Group(
    name="giveaway",
    description="Commandes pour gérer les giveaways."
)

@embed_group.command(name="create", description="Créer un embed personnalisé.")
@app_commands.checks.has_permissions(manage_messages=True)
async def create_embed(interaction: discord.Interaction):
    await interaction.response.send_message(content=None, view=CCustomEmbed({"components": []}))

async def autocomplete_embed(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=cfg.get("name"), value=cfg.get("name").lower().replace(" ", "_"))
        for cfg in json.load(open('data/embeds_config.json', 'r'))
        if cfg.get("owner_id") == interaction.user.id and current.lower() in cfg.get("name", "").lower()
    ][:25]

@embed_group.command(name="send", description="Envoyer un embed sauvegardé.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.autocomplete(embed_id=autocomplete_embed)
async def send_embed(interaction: discord.Interaction, embed_id: str):
    with open('data/embeds_config.json', 'r') as f:
        configs = json.load(f)

    # search for embed config with same `owner_id` and same `name`
    embed_config = next((cfg for cfg in configs if cfg.get("owner_id") == interaction.user.id and cfg.get("name").lower().replace(" ", "_") == embed_id), None)
    if not embed_config:
        return await interaction.response.send_message(f"{Emojis.error} Aucun embed trouvé avec cet ID.", ephemeral=True)

    await interaction.channel.send(content=None, view=CCustomEmbed(embed_config, editor=False))
    await interaction.response.send_message(f"{Emojis.checkmark} Embed envoyé dans {interaction.channel.mention}.", ephemeral=True)

@embed_group.command(name="edit", description="Éditer un embed sauvegardé.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.autocomplete(embed_id=autocomplete_embed)
async def edit_embed(interaction: discord.Interaction, embed_id: str):
    with open('data/embeds_config.json', 'r') as f:
        configs = json.load(f)

    embed_config = next((cfg for cfg in configs if cfg.get("owner_id") == interaction.user.id and cfg.get("name").lower().replace(" ", "_") == embed_id), None)
    if not embed_config:
        return await interaction.response.send_message(f"{Emojis.error} Aucun embed trouvé avec cet ID.", ephemeral=True)

    await interaction.response.send_message(content=None, view=CCustomEmbed(embed_config, editor=True))

@embed_group.command(name="delete", description="Supprimer un embed sauvegardé.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.autocomplete(embed_id=autocomplete_embed)
async def delete_embed(interaction: discord.Interaction, embed_id: str):
    with open('data/embeds_config.json', 'r') as f:
        configs = json.load(f)

    embed_config = next((cfg for cfg in configs if cfg.get("owner_id") == interaction.user.id and cfg.get("name").lower().replace(" ", "_") == embed_id), None)
    if not embed_config:
        return await interaction.response.send_message(f"{Emojis.error} Aucun embed trouvé avec cet ID.", ephemeral=True)

    configs.remove(embed_config)
    with open('data/embeds_config.json', 'w') as f:
        json.dump(configs, f, indent=4)

    await interaction.response.send_message(f"{Emojis.checkmark} Embed **{embed_config.get('name', 'No Title')}** supprimé avec succès.", ephemeral=True)

@sticky_group.command(name="create", description="Créer un message épinglé.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.autocomplete(embed_id=autocomplete_embed)
async def create_sticky(interaction: discord.Interaction, embed_id: str):
    embed_config = None
    if embed_id:
        with open('data/embeds_config.json', 'r') as f:
            configs = json.load(f)

        # search for embed config with same owner and same name
        embed_config = next((cfg for cfg in configs if cfg.get("owner_id") == interaction.user.id and cfg.get("name").lower().replace(" ", "_") == embed_id), None)
        if not embed_config:
            return await interaction.response.send_message(f"{Emojis.error} Aucun embed trouvé avec cet ID.", ephemeral=True)

    view = CCustomEmbed(embed_config if embed_config else {"components": []}, editor=False)
    msg: discord.Message = await interaction.channel.send(content=None, view=view)
    with open('data/sticky_config.json', 'r') as f:
        stickies = json.load(f)
    stickies.append({
        "message_id": msg.id,
        "channel_id": interaction.channel.id,
        "guild_id": interaction.guild.id,
        "embed_config_info": [embed_id, interaction.user.id] if embed_config else None
    })
    with open('data/sticky_config.json', 'w') as f:
        json.dump(stickies, f, indent=4)

    await interaction.response.send_message(f"{Emojis.sticky} Message épinglé créé dans {interaction.channel.mention}.", ephemeral=True)

async def autocomplete_sticky(interaction: discord.Interaction, current: str):
    stickies = json.load(open('data/sticky_config.json', 'r'))
    choices = []
    for sticky in stickies:
        if sticky.get("guild_id") != interaction.guild.id:
            continue
        embed_info = sticky.get("embed_config_info")
        if embed_info:
            name = f"Sticky '{embed_info[0]}' in channel ID {interaction.guild.get_channel(int(sticky.get('channel_id'))).name}"
        else:
            name = f"Sticky in channel ID {interaction.guild.get_channel(int(sticky.get('channel_id'))).name}"
        if current.lower() in name.lower():
            choices.append(app_commands.Choice(name=name, value=str(sticky.get("channel_id"))))
    return choices[:25]

@sticky_group.command(name="delete", description="Supprimer un message épinglé.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.autocomplete(channel_id=autocomplete_sticky)
async def delete_sticky(interaction: discord.Interaction, channel_id: str):
    stickies = json.load(open('data/sticky_config.json', 'r'))
    sticky = next((s for s in stickies if str(s.get("channel_id")) == channel_id and s.get("guild_id") == interaction.guild.id), None)
    if not sticky:
        return await interaction.response.send_message(f"{Emojis.error} Aucun message épinglé trouvé avec cet ID.", ephemeral=True)

    stickies.remove(sticky)
    with open('data/sticky_config.json', 'w') as f:
        json.dump(stickies, f, indent=4)

    # delete the actual message
    channel = interaction.guild.get_channel(sticky.get("channel_id"))
    if channel:
        try:
            msg = await channel.fetch_message(sticky.get("message_id"))
            await msg.delete()
        except:
            pass

    await interaction.response.send_message(str(Emojis.sticky) + " Message épinglé supprimé avec succès.", ephemeral=True)

@giveaway_group.command(name="create", description="Créer un giveaway.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(prize="Le prix du giveaway", duration="La durée du giveaway (ex: 7m, 3h, 7d)", winners="Le nombre de gagnants")
async def create_giveaway(interaction: discord.Interaction, prize: str, duration: str, winners: int):
    # parse duration
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration[-1]
    if unit not in time_units:
        return await interaction.response.send_message(f"{Emojis.error} Unité de temps invalide. Utilisez 's', 'm', 'h' ou 'd'.", ephemeral=True)
    try:
        time_value = int(duration[:-1])
    except ValueError:
        return await interaction.response.send_message(f"{Emojis.error} Durée invalide. Veuillez fournir un nombre suivi d'une unité de temps (ex: 10m, 2h).", ephemeral=True)
    duration_seconds = time_value * time_units[unit]

    msg = await interaction.channel.send(content=None, view=Giveaway({
        "prize": prize,
        "end_timestamp": int(interaction.created_at.timestamp()) + duration_seconds,
        "channel_id": interaction.channel.id,
        "participants_count": 0,
        "winners": winners,
        "participants": []
    }))

    giveaway_config = {
        "prize": prize,
        "message_id": msg.id,
        "channel_id": interaction.channel.id,
        "end_timestamp": int(interaction.created_at.timestamp()) + duration_seconds,
        "winners": winners,
        "participants": []
    }
    with open('data/giveaways.json', 'r') as f:
        giveaways = json.load(f)
    giveaways.append(giveaway_config)
    with open('data/giveaways.json', 'w') as f:
        json.dump(giveaways, f, indent=4)

    await interaction.response.send_message(f"{Emojis.checkmark} Giveaway créé avec succès !", ephemeral=True)

@giveaway_group.command(name="end", description="Terminer un giveaway immédiatement.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(message_id="L'ID du message du giveaway à terminer")
async def end_giveaway(interaction: discord.Interaction, message_id: str):
    with open('data/giveaways.json', 'r') as f:
        giveaways = json.load(f)

    giveaway_config = next((g for g in giveaways if g.get("message_id") == int(message_id)), None)
    if not giveaway_config:
        return await interaction.response.send_message(f"{Emojis.error} Aucun giveaway trouvé avec cet ID de message.", ephemeral=True)

    channel = app.get_channel(giveaway_config["channel_id"])
    if not channel:
        return await interaction.response.send_message(f"{Emojis.error} Le channel du giveaway est introuvable.", ephemeral=True)
    try:
        msg = await channel.fetch_message(giveaway_config["message_id"])
    except:
        return await interaction.response.send_message(f"{Emojis.error} Le message du giveaway est introuvable.", ephemeral=True)

    if giveaway_config.get("ended", False):
        return await interaction.response.send_message(f"{Emojis.error} Ce giveaway est déjà terminé.", ephemeral=True)

    g_view = Giveaway(giveaway_config)
    winner_ids = await g_view.roll(end=True)

    await msg.edit(view=g_view)
    if winner_ids:
        winner_mentions = ', '.join(f"<@{wid}>" for wid in winner_ids)
        await channel.send(f"🎉 Félicitations {winner_mentions} ! Vous avez gagné le giveaway pour **{giveaway_config['prize']}** !")
    else:
        await channel.send(f"Le giveaway pour **{giveaway_config['prize']}** s'est terminé, mais il n'y a pas eu de participants.")

    await interaction.response.send_message(f"{Emojis.checkmark} Giveaway terminé avec succès.", ephemeral=True)

@giveaway_group.command(name="reroll", description="Relancer un giveaway pour choisir de nouveaux gagnants.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(message_id="L'ID du message du giveaway à relancer")
async def reroll_giveaway(interaction: discord.Interaction, message_id: str):
    with open('data/giveaways.json', 'r') as f:
        giveaways = json.load(f)

    giveaway_config = next((g for g in giveaways if g.get("message_id") == int(message_id)), None)
    if not giveaway_config:
        return await interaction.response.send_message(f"{Emojis.error} Aucun giveaway trouvé avec cet ID de message.", ephemeral=True)

    channel = app.get_channel(giveaway_config["channel_id"])
    if not channel:
        return await interaction.response.send_message(f"{Emojis.error} Le channel du giveaway est introuvable.", ephemeral=True)
    try:
        msg = await channel.fetch_message(giveaway_config["message_id"])
    except:
        return await interaction.response.send_message(f"{Emojis.error} Le message du giveaway est introuvable.", ephemeral=True)

    g_view = Giveaway(giveaway_config)
    winner_ids = await g_view.roll(end=True)
    await msg.edit(view=g_view)
    if winner_ids:
        winner_mentions = ', '.join(f"<@{wid}>" for wid in winner_ids)
        await channel.send(f"🎉 Félicitations {winner_mentions} ! Vous avez gagné le giveaway pour **{giveaway_config['prize']}** !")
    else:
        await channel.send(f"Le giveaway pour **{giveaway_config['prize']}** a été relancé, mais il n'y a pas eu de participants.")

    await interaction.response.send_message(f"{Emojis.checkmark} Giveaway relancé avec succès.", ephemeral=True)


if GUILD_OBJ:
    tree.add_command(embed_group, guild=GUILD_OBJ)
    tree.add_command(sticky_group, guild=GUILD_OBJ)
    tree.add_command(giveaway_group, guild=GUILD_OBJ)
else:
    tree.add_command(embed_group)
    tree.add_command(sticky_group)
    tree.add_command(giveaway_group)

@tasks.loop(seconds=30)
async def giveaway_check():
    with open('data/giveaways.json', 'r') as f:
        giveaways = json.load(f)

    current_timestamp = int(discord.utils.utcnow().timestamp())
    for giveaway in giveaways:
        if not giveaway.get("ended") and giveaway["end_timestamp"] <= current_timestamp:
            channel = app.get_channel(giveaway["channel_id"])
            if not channel:
                continue
            try:
                msg = await channel.fetch_message(giveaway["message_id"])
            except:
                continue

            giveaway["ended"] = True
            g_view = Giveaway(giveaway)
            winners = []
            for _ in range(giveaway.get("winners", 1)):
                winner_id = await g_view.roll(end=True)
                if winner_id and winner_id not in winners:
                    winners.append(winner_id)

            await msg.edit(view=g_view)
            if winners:
                winner_mentions = ', '.join(f"<@{wid}>" for wid in winners)
                await channel.send(f"🎉 Félicitations {winner_mentions} ! Vous avez gagné le giveaway pour **{giveaway['prize']}** !")
            else:
                await channel.send(f"Le giveaway pour **{giveaway['prize']}** s'est terminé, mais il n'y a pas eu de participants.")

@app.event
async def on_message(message: discord.Message):
    if not message.author.bot and message.author.guild_permissions.manage_messages:
        if message.content.lower() == ".close":
            await message.delete()
            return await close_ticket(message.channel)

        if message.content.lower().startswith('.rename'):
            new_name = message.content[7:].strip()
            if not new_name:
                return

            with open('data/ticket_config.json', 'r') as f:
                configs = json.load(f)

            category_ids = [cfg['category'] for cfg in configs if cfg['category'] is not None]
            if message.channel.category_id not in category_ids:
                return

            await message.delete()
            await message.channel.edit(name=new_name)
            return await message.channel.send(f"{Emojis.checkmark} Le nom du ticket a été changé en **{new_name}**.", delete_after=5)

    await check_for_sticky(message)

async def check_for_sticky(message: discord.Message):
    channel_id = message.channel.id
    if message.author.bot: return
    with open('data/sticky_config.json', 'r') as f:
        stickies = json.load(f)
    with open('data/embeds_config.json', 'r') as f:
        embed_configs = json.load(f)
    stickies = [s for s in stickies if s.get("channel_id") == channel_id]
    for sticky in stickies:
        if sticky.get("message_id") == message.id:
            continue
        try:
            msg = await message.channel.fetch_message(sticky.get("message_id"))
            await msg.delete()
        except:
            pass

        e_id, e_owner_id = sticky.get("embed_config_info")
        embed_configs = {cfg.get("name").lower().replace(" ", "_"): cfg for cfg in embed_configs if cfg.get("owner_id") == e_owner_id}
        embed_config = embed_configs.get(e_id) if e_id else None
        if not embed_config:
            stickies.remove(sticky)
            with open('data/sticky_config.json', 'w') as f:
                json.dump(stickies, f, indent=4)
            return
        view = CCustomEmbed(embed_config if embed_config else {"components": []}, editor=False)
        msg: discord.Message = await message.channel.send(content=None, view=view)
        stickies[stickies.index(sticky)]["message_id"] = msg.id
        with open('data/sticky_config.json', 'w') as f:
            json.dump(stickies, f, indent=4)

@app.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(f"{Emojis.error} Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{Emojis.error} Une erreur est survenue lors de l'exécution de la commande.", ephemeral=True)
        traceback.print_exc()
        raise error


if __name__ == "__main__":
    app.run(config["discord_token"])
