from typing import Tuple
from exceptions import TokensNotPresentError

TOKEN_NAMES = ('TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')


def check_each_token(tokens: Tuple[str]):
    """Проверяет наличие каждого токена."""
    for token, token_name in zip(tokens, TOKEN_NAMES):
        if token is None:
            raise TokensNotPresentError(f'Отсутствует обязательная '
                                        f'переменная окружения: "{token_name}".'
                                        f'Программа принудительно'
                                        f' остановлена')
