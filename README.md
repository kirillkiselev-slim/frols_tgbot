### Encar Car Monitor
A system to monitor specific car models on the Encar website and notify via Telegram when new listings are found.

## Features
- Monitors Encar for new car listings.
- Supports multiple car models (Audi A7 and A5 by default).
- Sends Telegram notifications for new listings.
- Uses Selenium for web scraping.
- Manages browser profiles with Multilogin.
- Logs system resource usage.
- Requirements
- Python 3.8+
- selenium
- psutil
- requests
- python-telegram-bot
- python-dotenv
- multilogin
- logging
- multiprocessing


## Installation

#### Clone the repository:

`git clone https://github.com/kirillkiselev-slim/frols_tgbot/`

#### Cd into it
`cd frols_tgbot` 

#### Create a virtual environment and activate it:

`python3 -m venv venv`

- On Mac: `source venv/bin/activate ` 
- On Windows: `venv\Scripts\activate`
#### Install the required packages:

`pip install -r requirements.txt`

### Configuration
Create a .env file in the root directory with the following:`

```
TELEGRAM_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
MLX_EMAIL=your-multilogin-email
MLX_PASS=your-multilogin-password
```

#### Update site_elements.py with correct XPaths and elements for the Encar website.

## Usage
### Ensure Multilogin application is running.
Run the main script:

`python main.py`

#### Project Structure

```
frols_tgbot/
├── check_tokens.py          # Token checking functions
├── exceptions.py            # Custom exceptions
├── main.py                  # Main script
├── multilogin.py            # Multilogin handling functions
├── site_elements.py         # XPaths for site elements
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
├── README.md                # Documentation
└── monitor_cars.logs        # Log file
```

Author: Kirill Kiselev