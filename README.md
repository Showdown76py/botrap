# [botrap](https://github.com/Showdown76py/botrap)

A French Discord bot focused on server management and community engagement, customized for Timrap in Python.

## Features
- Custom Embeds: Create and manage custom embed messages with ease.
- Stickies: Pin important messages in channels for quick access.
- Giveaways: Host and manage giveaways to engage your community.
- Ticket System: Set up a ticketing system for support and inquiries.

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/Showdown76py/botrap.git
    ```
2. Navigate to the project directory:
    ```bash
    cd botrap
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Create a `config.json` file in the root directory and add your Discord bot token and optional guild ID:
    ```json
    {
        "token": "YOUR_BOT_TOKEN_HERE",
        "guild_id": "YOUR_GUILD_ID_HERE" (optional)
    }
    ```
5. Add your bot in a Discord server with emojis found in `emojis/`, and edit `dc/Emojis.py` with their name and IDs.
   **You can also add the emojis via Discord's developer portal for this bot.**

6. Run the bot:
    ```bash
    python main.py
    ```

## Usage
- Invite the bot to your Discord server using the OAuth2 URL with appropriate permissions.
URL: `https://discord.com/oauth2/authorize?client_id=[YOUR_CLIENT_ID]&permissions=8&integration_type=0&scope=bot+applications.commands`
- Use slash commands to interact with the bot and access its features.
