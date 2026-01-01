import secrets
import string



def generate_access_code(length: int = 8) -> str:
    """
    Генерирует уникальный код доступа для опроса.
    По умолчанию — 8 символов: заглавные буквы и цифры (без 0 и O для удобства).
    """
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace('0', '').replace('O', '')  # исключаем похожие символы
    return ''.join(secrets.choice(alphabet) for _ in range(length))


