class InvalidTokenException(Exception):
    """Исключение для невалидного токена аутентификации"""
    pass

class PushDeliveryException(Exception):
    """Исключение при неудачной доставке push-уведомления"""
    pass
