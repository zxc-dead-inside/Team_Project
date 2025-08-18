
# Start service

1. Navigate to payment-service directory

2. Execute

```bash
docker compose up -d
```

or 

```bash
docker compose up --build
```

3. Check that the service is running

`http://localhost:8002/docs#`


# Create a payments

1. **Run a command or use endpoints directly from `http://localhost:8002/docs#`**
```bash
curl -X POST http://localhost:8002/api/v1/payments/charge \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_123","subscription_type":"premium","amount":"100.00","return_url":"https://example.com/success"}'
```

2. **Complete Payment in Browser**

- Open the `confirmation_url` from response
- Example response should look like
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
- Enter test card: 5555 5555 5555 4444
- Expiry: 12/25 (any future date)
- CVV: 123 (any 3 digits)
- Click Pay

3. **Check Status**
```bash
curl http://localhost:8002/api/v1/payments/status/{payment_id}
```

4. **Test Refund**
```bash
curl -X POST http://localhost:8002/api/v1/payments/refund \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"{payment_id}","reason":"Test refund"}'
```

YooKassa Test Cards Quick Reference:  
| Card                | Number              | What Happens                     |
|---------------------|---------------------|----------------------------------|
| ✅ Always Success   | 5555 5555 5555 4444 | Payment succeeds immediately    |
| 🔐 3D-Secure        | 5555 5555 5555 4592 | Asks for SMS code (enter: 123456) |
| ❌ No Money         | 5555 5555 5555 4543 | Fails with insufficient funds   |
| ❌ Expired          | 5555 5555 5555 4527 | Fails with card expired         |

For ALL test cards use:

- Any future expiry date (e.g., 12/25)
- Any 3-digit CVV (e.g., 123)
- Any name and email



# Proposed integration with Main Application

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
                    "X-User-Id": user_id  # Pass authenticated user ID
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