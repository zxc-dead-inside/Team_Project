superuser = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "Qwerty123!",
    "is_superuser": True,
    "is_active": True
}

weak_password_user = {
    "username": "weak_password_user",
    "email": "weak_password_user@example.com",
    "password": "qwerty",
    "is_active": True
}

regular_users = [
    {
        "username": f"username_{i}",
        "email": f"username_{i}@example.com",
        "password": "Qwerty123!",
        "is_active": True
    } for i in range(10)
]

disabled_user = {
    "username": "disabled_user",
    "email": "disabled_user@example.com",
    "password": "Qwerty123!",
    "is_active": False
}