# Telegram Bybit Monitor

This project is a Telegram bot that monitors Bybit announcements and forwards messages that match certain keywords to a private channel.

## How to Use

This bot is designed to be deployed on Railway. Once deployed, it will:

- Monitor the @Bybit_Announcements Telegram channel for new messages.
- Filter messages containing all of the following keywords: 'New', 'Listing', 'Perpetual', and 'Contract'.
- Forward the filtered messages to a private Telegram channel that you specify using the `TARGET_CHANNEL_ID` environment variable.

## Setup

To set up the bot, you need to configure the following environment variables:

- `TELEGRAM_API_ID`: Your Telegram API ID.
- `TELEGRAM_API_HASH`: Your Telegram API Hash.
- `TELEGRAM_PHONE`: Your Telegram phone number.
- `BOT_TOKEN`: Your Telegram bot token.
- `TARGET_CHANNEL_ID`: The ID of the private Telegram channel where messages will be forwarded.
- `TELEGRAM_SESSION_DATA`: Your Telegram session string.

### Obtaining Credentials

1.  **`TELEGRAM_API_ID` and `TELEGRAM_API_HASH`**:
    *   Go to [my.telegram.org](https://my.telegram.org).
    *   Log in with your Telegram account.
    *   Click on "API development tools".
    *   You will find your `API ID` and `API Hash` there.

2.  **`BOT_TOKEN`**:
    *   Open Telegram and search for "BotFather".
    *   Start a chat with BotFather and send the `/newbot` command.
    *   Follow the instructions to create a new bot.
    *   BotFather will provide you with a `BOT_TOKEN`.

3.  **`TARGET_CHANNEL_ID`**:
    *   Create a private Telegram channel if you don't have one.
    *   To get the channel ID, you can temporarily make the channel public, set a unique username, and then use a bot like `@username_to_id_bot` to get the ID. Remember to make it private again. Alternatively, you can forward a message from the channel to `@getidsbot`. The channel ID will typically start with `-100`.

4.  **`TELEGRAM_SESSION_DATA`**:
    *   This project uses a pre-authenticated session to avoid interactive login on Railway.
    *   Clone this repository to your local machine.
    *   Ensure you have Python installed.
    *   Install the required dependencies: `pip install -r requirements.txt`.
    *   Create a `.env` file in the root of the project and add your `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_PHONE`.
        ```
        TELEGRAM_API_ID=your_api_id
        TELEGRAM_API_HASH=your_api_hash
        TELEGRAM_PHONE=your_phone_number
        ```
    *   Run the `local_auth.py` script: `python local_auth.py`.
    *   You will be prompted to enter your phone number and a login code sent to your Telegram account.
    *   After successful authentication, the script will print the `TELEGRAM_SESSION_DATA` to the console. Copy this value.
    *   **Important**: The `local_auth.py` script will delete the local session file (`telegram_session.session`) after generating the string for security reasons.

## Deployment on Railway

This bot is optimized for deployment on [Railway](https://railway.app/).

1.  **Create a Railway Project**:
    *   Go to your Railway dashboard and click "New Project".
    *   Choose "Deploy from GitHub repo".

2.  **Connect to GitHub**:
    *   Select your GitHub account and choose this repository.
    *   Railway will automatically detect the `Procfile` and suggest a deployment configuration.

3.  **Add Environment Variables**:
    *   In your Railway project, go to the "Variables" tab.
    *   Add all the environment variables listed in the "Setup" section (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, `BOT_TOKEN`, `TARGET_CHANNEL_ID`, and `TELEGRAM_SESSION_DATA`) with their respective values.

4.  **Deploy**:
    *   Railway will automatically trigger a deployment once the repository and environment variables are set up.
    *   You can monitor the deployment logs in the "Deployments" tab.
    *   Once deployed, the bot will start monitoring the specified Bybit channel.

## Contributing

Contributions are welcome! If you have any suggestions, find a bug, or want to add a new feature, please feel free to:

- Open an issue to discuss the changes.
- Fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
