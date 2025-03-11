# Slack Translator Bot

## Overview

The Slack Translator Bot is a Flask-based application that listens for Slack events and translates messages between English and German. It temporarily replaces URLs and emojis with placeholders during translation to preserve the original formatting. The bot uses the Slack API (via the `slack_sdk`) to interact with Slack and the `googletrans` library for language detection and translation.

## Features

- **Slack Integration:** Listens for Slack events and processes messages where the bot is mentioned.
- **Automatic Language Detection:** Detects whether the message is in English or German.
- **Translation:** Translates messages from English to German and vice versa.
- **Formatting Preservation:** Uses regular expressions to replace URLs and emojis with placeholders before translation and restores them afterward.
- **Threaded Replies:** Posts the translated text as a reply in the same message thread.
- **Error Handling:** Provides basic error logging (with potential improvements using Python's logging module).

## Prerequisites

- Python 3.7 or later
- A Slack workspace with a configured Slack Bot
- A valid Slack Bot Token

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Glefterov/slack-bot-translator.git
   cd slack-translator-bot
   ```

2. **Create and Activate a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the environment variable `SLACK_BOT_TOKEN` with your Slack Bot Token. You can also create a `.env` file in the project root and load it using a library like `python-dotenv`.

Example `.env` file:

```env
SLACK_BOT_TOKEN=your-slack-bot-token-here
```

## Running the Application

Start the Flask application by running:

```bash
python app.py
```

By default, the Flask app runs on `http://0.0.0.0:29874` with debugging enabled.

## Usage

1. **Invite the Bot:** Add the bot to a Slack channel or send it a direct message.
2. **Mention the Bot:** Mention the bot (or use its name, e.g., "Translator") in your message to trigger translation.
3. **Receive Translation:** The bot will detect the language of the message, translate it (English ⇄ German), and post the translated text as a threaded reply.

## Future Improvements

- Replace `print()` statements with Python's logging module for better logging and debugging.
- Refactor code to further modularize and improve maintainability.
- Implement asynchronous processing to handle translation tasks more efficiently.
- Extend language support beyond just English and German.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Slack API Documentation](https://api.slack.com/)
- [googletrans Documentation](https://py-googletrans.readthedocs.io/)
```
