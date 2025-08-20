
# Payment Service

Сервис для обработки платежей онлайн-кинотеатра с интеграцией YooKassa. Поддерживает создание платежей, возврат средств и проверку статуса транзакций.

## Запуск сервиса

1. Перейдите в директорию payment-service

2. Выполните команду

```bash
docker compose up -d
```

или

```bash
docker compose up --build
```

3. Проверьте, что сервис запущен

`http://localhost:8002/docs#`

## Архитектура

Сервис использует трёхслойную архитектуру:
- **API Layer** - обработка HTTP запросов
- **Business Layer** - бизнес-логика платежей
- **Provider Layer** - интеграция с YooKassa

### Интеграция с Auth Service

Payment Service интегрирован с Auth Service для:
- Получения пользователя из JWT токена
- Сохранения транзакций в базу данных
- Управления подписками пользователей

**Endpoints Auth Service:**
- `POST /api/v1/billing/charge` - создание платежа
- `POST /api/v1/billing/refund` - возврат средств


## API Endpoints

### Прямое обращение к Payment Service

1. **Выполните команду или используйте endpoints напрямую из `http://localhost:8002/docs#`**
```bash
curl -X POST http://localhost:8002/api/v1/payments/charge \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_123","subscription_type":"premium","amount":"100.00","return_url":"https://example.com/success"}'
```

2. **Завершите оплату в браузере**

- Откройте `confirmation_url` из ответа
- Пример ответа должен выглядеть так
```
{
  "provider_payment_id": "30340b69-000f-5000-8000-1f1dbde67a90",
  "status": "pending",
  "amount": "1.00",
  "currency": "RUB",
  "created_at": "2025-08-17T15:39:21.294000Z",
  "confirmation_url": "https://yoomoney.ru/checkout/payments/v2/contract?orderId=30340b69-000f-5000-8000-1f1dbde67a90",
  "metadata": {
    "subscription_type": "new_sub",
    "order_id": "sub_user_123_26d0014c",
    "user_id": "user_123",
    "cms_name": "yookassa_sdk_python",
    "service": "online_cinema"
  }
}
```
- Введите тестовую карту: 5555 5555 5555 4444
- Срок действия: 12/25 (любая будущая дата)
- CVV: 123 (любые 3 цифры)
- Нажмите "Оплатить"

3. **Проверьте статус**
```bash
curl http://localhost:8002/api/v1/payments/status/{payment_id}
```

4. **Протестируйте возврат средств**
```bash
curl -X POST http://localhost:8002/api/v1/payments/refund \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"{payment_id}","reason":"Test refund"}'
```

### Обращение через Auth Service

Для использования с авторизацией обращайтесь к Auth Service:

```bash
# Создание платежа (требует JWT токен)
curl -X POST http://localhost:8100/api/v1/billing/charge \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subscription_type":"premium","amount":"150.00","return_url":"https://example.com/success"}'

# Возврат средств (требует JWT токен)
curl -X POST http://localhost:8100/api/v1/billing/refund \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"{payment_id}","amount":"50.00","reason":"Test refund"}'
```

## Тестовые карты YooKassa

| Карта               | Номер               | Что происходит                   |
|---------------------|---------------------|----------------------------------|
| ✅ Всегда успех     | 5555 5555 5555 4444 | Платёж проходит сразу           |
| 🔐 3D-Secure        | 5555 5555 5555 4592 | Запрашивает SMS код (введите: 123456) |
| ❌ Недостаточно средств | 5555 5555 5555 4543 | Ошибка недостатка средств       |
| ❌ Истёк срок       | 5555 5555 5555 4527 | Ошибка истёкшего срока карты    |

Для ВСЕХ тестовых карт используйте:

- Любую будущую дату истечения (например, 12/25)
- Любой 3-значный CVV (например, 123)
- Любое имя и email



## Интеграция с основным приложением

### Клиент для Payment Service

```python
import httpx
from typing import Optional

class CinemaPaymentClient:
    def __init__(self, payment_service_url: str = "http://payment-service:8000"):
        self.base_url = payment_service_url
    
    async def create_subscription_payment(
        self,
        user_id: str,
        subscription_type: str,
        amount: float,
        return_url: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/payments/charge",
                json={
                    "user_id": user_id,
                    "subscription_type": subscription_type,
                    "amount": str(amount),
                    "return_url": return_url
                },
                headers={
                    "X-User-Id": user_id  # Передача ID аутентифицированного пользователя
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def check_payment_status(self, payment_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/payments/status/{payment_id}"
            )
            response.raise_for_status()
            return response.json()
```

### Клиент для Auth Service (рекомендуется)

```python
import httpx
from typing import Optional

class CinemaBillingClient:
    def __init__(self, auth_service_url: str = "http://auth-service:8100"):
        self.base_url = auth_service_url
    
    async def create_charge(
        self,
        token: str,
        subscription_type: str,
        amount: float,
        return_url: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/billing/charge",
                json={
                    "subscription_type": subscription_type,
                    "amount": str(amount),
                    "return_url": return_url
                },
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def create_refund(
        self,
        token: str,
        payment_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            payload = {"payment_id": payment_id}
            if amount:
                payload["amount"] = str(amount)
            if reason:
                payload["reason"] = reason
                
            response = await client.post(
                f"{self.base_url}/api/v1/billing/refund",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )
            response.raise_for_status()
            return response.json()
```

