# Price Category Telegram Bot

This repository contains the source code for a Telegram bot designed to categorize products by price. The bot assists users in organizing and comparing products based on their price categories, providing a convenient tool for managing shopping lists or inventory.

## Features

- Categorizes products into predefined price ranges
- Supports adding, removing, and listing products
- Calculates the first, second, and third price categories for electricity consumers of MOSENERGOSBYT
- Interactive Telegram bot interface for user-friendly interaction
- Docker support for easy deployment

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/3yungar/price_category_telegram_bot
   cd price_category_telegram_bot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables for the Telegram bot token.

## Usage

1. Run the bot:
   ```bash
   python bot.py
   ```
2. Interact with the bot via Telegram to categorize and manage your products.

## Docker

To deploy the bot using Docker:
```bash
docker-compose up --build
```

## Contributing

Feel free to open issues or submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

For more details, visit the [GitHub repository](https://github.com/3yungar/price_category_telegram_bot).
