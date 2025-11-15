import asyncio
import json
import uuid
import discord

from dc.Emojis import Emojis
from views.embeds.ContentModal import ContentModal

example_embed_config = {
    "name": "",
    "owner_id": 0,
    "components": [
        {"type": "text", "content": "# Tarifs disponibles"},
        {"type": "text", "content": "Sélectionnez le moyen de paiement auquel vous souhaitez vous renseigner."},
        {"type": "separator", "spacing": "small"},
        {"type": "select", "placeholder": "Sélectionnez une option", "custom_id": "uuid4", "options": [
            {"label": "PayPal", "description": "Voir les tarifs PayPal.", "message": "Voici les tarifs pour PayPal..."},
            {"label": "Carte bancaire", "description": "Voir les tarifs par carte bancaire.", "message": "Voici les tarifs pour carte bancaire..."},
            {"label": "Cryptomonnaies", "description": "Voir les tarifs en cryptomonnaies.", "message": "Voici les tarifs pour cryptomonnaies..."}
        ]}
    ],
    "color": 3447003
}

class CCustomEmbed(discord.ui.LayoutView):
    def __init__(self, embed_config: dict, editor: bool = True):
        self.embed_config = embed_config
        super().__init__(timeout=None)
        self.editor = editor

        deleteoptions = [
            discord.SelectOption(
                label=f"Composant {i+1}: {comp.get('type', 'unknown').title()}",
                description=comp.get("content", "")[:50] if comp.get("type") == "text" else "",
                value=str(i)
            ) for i, comp in enumerate(embed_config.get("components", []))
        ]
        if not deleteoptions:
            deleteoptions.append(
                discord.SelectOption(
                    label="Aucun composant à supprimer",
                    description="",
                    value="none",
                )
            )

        components = [self.dict_to_component(comp) for comp in embed_config.get("components", [])]
        if len(components) == 0:
            components.append(
                discord.ui.TextDisplay("** **")
            )
        work_embed = discord.ui.Container(
            *components,
            accent_color=discord.Color(embed_config.get("color")) if embed_config.get("color") else None
        )

        container1 = discord.ui.Container(
            discord.ui.TextDisplay(f"{Emojis.pencil} **Création d'embed** • Sélectionnez ci-dessous le type de composant à ajouter."),
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small),
            discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    emoji=Emojis.add_text,
                    custom_id="add_text"
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    emoji=Emojis.separator,
                    custom_id="add_separator"
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    emoji=Emojis.filemenu,
                    custom_id="add_select"
                )
            ),
            discord.ui.ActionRow(
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    emoji=Emojis.add_photo,
                    custom_id="add_photo"
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    emoji=Emojis.paint,
                    custom_id="add_color"
                ),
                discord.ui.Button(
                    style=discord.ButtonStyle.blurple,
                    emoji=Emojis.save,
                    custom_id="save_embed"
                ),
            ),
            discord.ui.ActionRow(
                discord.ui.Select(
                    placeholder="Supprimer un élément...",
                    custom_id="delete_component",
                    options=deleteoptions,
                    disabled=len(embed_config.get("components", [])) == 0
                )
            ),
            accent_color=discord.Color(embed_config.get("color")) if embed_config.get("color") else None
        )

        self.add_item(work_embed)
        if self.editor:
            self.add_item(container1)

    async def handle_menu_select(self, interaction: discord.Interaction, iid: str):
        # find iid index in embed_config selects
        if iid == "delete_component":
            selected_index = interaction.data.get("values", [])[0]
            if selected_index == "none":
                return False

            self.embed_config["components"].pop(int(selected_index))

            await interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
            return True

        for comp in self.embed_config.get("components", []):
            if comp.get("type") == "select" and comp.get("custom_id") == iid:
                index = self.embed_config["components"].index(comp)
                break
        else:
            return False

        selected_values = interaction.data.get("values", [])
        print(selected_values)
        if "add_option" in selected_values:
            selected_comp = self.embed_config["components"][index]
            cm = ContentModal(
                title="Ajouter une option au menu de sélection",
                elements=[
                    discord.ui.TextInput(
                        label="Label de l'option",
                        placeholder="Option 1",
                        required=True
                    ),
                    discord.ui.TextInput(
                        label="Description de l'option",
                        placeholder="Description de l'option",
                        style=discord.TextStyle.paragraph,
                        required=False
                    ),
                    discord.ui.TextInput(
                        label="Message à envoyer",
                        placeholder="Voici les informations que vous avez demandées...",
                        style=discord.TextStyle.paragraph,
                        required=True
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            selected_comp["options"].append({
                "label": cm.response[0],
                "description": cm.response[1],
                "message": cm.response[2]
            })

        elif "delete_option" in selected_values:
            selected_comp = self.embed_config["components"][index]
            deleteoptions = [
                discord.SelectOption(
                    label=f"Option {i+1}: {opt.get('label', 'Option')}",
                    description=opt.get("description", "")[:50],
                    value=str(i)
                ) for i, opt in enumerate(selected_comp.get("options", []))
            ]
            if not deleteoptions:
                deleteoptions.append(
                    discord.SelectOption(
                        label="Aucune option à supprimer",
                        description="",
                        value="none",
                    )
                )

            cm = ContentModal(
                title="Supprimer une option du menu de sélection",
                elements=[
                    discord.ui.Label(
                        text="Option à supprimer",
                        component=discord.ui.Select(
                            placeholder="Sélectionnez une option à supprimer...",
                            custom_id="delete_select_option",
                            options=deleteoptions,
                            required=True
                        )
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            selected_index = cm.response[0]
            if selected_index != "none":
                selected_comp["options"].pop(int(selected_index))

                # permanently delete from embed config
                self.embed_config["components"][index] = selected_comp

        else:
            # print the `message` for the selected options
            messages = []
            selected_comp = self.embed_config["components"][index]
            for val in selected_values:
                for opt in selected_comp.get("options", []):
                    if val == opt.get("label", "").lower().replace(" ", "_")[:10] + opt.get("label", "").lower().replace(" ", "_")[10:]:
                        messages.append(opt.get("message", ""))

            await interaction.response.send_message("\n\n".join(messages), ephemeral=True)
            return True

        await cm.interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        iid = interaction.data.get("custom_id")
        print('Recieved callback for custom_id:', iid)

        if iid == "add_text":
            cm = ContentModal(
                title="Ajouter du texte",
                elements=[
                    discord.ui.TextInput(
                        label="Contenu du texte",
                        placeholder="...",
                        required=True
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            self.embed_config["components"].append({
                "type": "text",
                "content": cm.response[0]
            })

            await cm.interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
            return False

        elif iid == "add_separator":
            self.embed_config["components"].append({
                "type": "separator",
                "spacing": "small"
            })
            await interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
            return False

        elif iid == "add_select":
            cm = ContentModal(
                title="Ajouter un menu de sélection",
                elements=[
                    discord.ui.TextInput(
                        label="Titre du menu de sélection",
                        placeholder="Séléctionnez une option",
                        style=discord.TextStyle.short,
                        required=True
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            self.embed_config["components"].append({
                "type": "select",
                "placeholder": cm.response[0],
                "custom_id": str(uuid.uuid4()).replace('-', ''),
                "options": []
            })

            await cm.interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
            return False

        elif iid == "add_photo":
            cm = ContentModal(
                title="Ajouter une image",
                elements=[
                    discord.ui.TextInput(
                        label="URL de l'image",
                        placeholder="https://example.com/image.png",
                        required=True
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            self.embed_config["components"].append({
                "type": "image",
                "content": f"{cm.response[0]}"
            })

            await cm.interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
            return False

        elif iid == "add_color":
            cm = ContentModal(
                title="Définir la couleur de l'embed",
                elements=[
                    discord.ui.TextInput(
                        label="Couleur hexadécimale",
                        placeholder="ex: #3498db",
                        min_length=6,
                        max_length=7,
                        required=True
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            try:
                color_value = int(cm.response[0].lstrip('#'), 16)
                self.embed_config["color"] = color_value
            except ValueError:
                await interaction.response.send_message("Couleur hexadécimale invalide.", ephemeral=True)
                return False

            await cm.interaction.response.edit_message(view=CCustomEmbed(self.embed_config))
            return False

        elif iid == "save_embed":
            # Save the embed configuration somewhere or process it as needed
            cm = ContentModal(
                title="Nom de la sauvegarde",
                elements=[
                    discord.ui.TextInput(
                        label="Nom de l'embed",
                        placeholder="Mon embed personnalisé",
                        required=True
                    )
                ]
            )

            await interaction.response.send_modal(cm)
            await cm.wait()

            if not cm.interaction:
                return

            self.embed_config["name"] = cm.response[0]
            self.embed_config["owner_id"] = interaction.user.id

            x = discord.ui.LayoutView()
            x.add_item(discord.ui.Container(discord.ui.TextDisplay(content=f"{Emojis.checkmark} Embed sauvegardé avec succès !")))

            with open('data/embeds_config.json', 'r') as f:
                configs = json.load(f)
            # delete existing config with same name if exists for this user
            configs = [cfg for cfg in configs if not (cfg.get("name") == self.embed_config["name"] and cfg.get("owner_id") == interaction.user.id)]
            configs.append(self.embed_config)
            with open('data/embeds_config.json', 'w') as f:
                json.dump(configs, f, indent=4)

            await cm.interaction.response.edit_message(content=None, view=x)
            return False

        return await self.handle_menu_select(interaction, iid)

    def dict_to_component(self, component_dict: dict):
        ctype = component_dict.get("type")
        if ctype == "text":
            return discord.ui.TextDisplay(content=component_dict.get("content", ""))
        elif ctype == "separator":
            spacing = component_dict.get("spacing", "small")
            spacing_enum = {
                "small": discord.SeparatorSpacing.small,
                "large": discord.SeparatorSpacing.large
            }.get(spacing, discord.SeparatorSpacing.small)
            return discord.ui.Separator(spacing=spacing_enum)
        elif ctype == "select":
            options = [
                discord.SelectOption(
                    label=opt.get("label", "Option"),
                    description=opt.get("description", ""),
                    value=opt.get("label", "").lower().replace(" ", "_")[:10] + opt.get("label", "").lower().replace(" ", "_")[10:]
                ) for opt in component_dict.get("options", [])
            ]

            if self.editor:
                options.append(discord.SelectOption(
                    label="Ajouter une option",
                    description="Ajouter une option au menu de sélection.",
                    value="add_option"
                ))
                options.append(discord.SelectOption(
                    label="Supprimer une option",
                    description="Supprimer une option du menu de sélection.",
                    value="delete_option"
                ))

            return discord.ui.ActionRow(discord.ui.Select(
                placeholder=component_dict.get("placeholder", "Sélectionnez une option"),
                custom_id=component_dict.get("custom_id", "select_menu"),
                options=options
            ))
        elif ctype == "image":
            return discord.ui.MediaGallery(
                discord.MediaGalleryItem(media=component_dict.get("content", ""))
            )
        return None
