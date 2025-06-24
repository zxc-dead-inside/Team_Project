#!/usr/bin/env python3
"""
Тест для проверки работы UGC API
"""

import requests
import time

BASE_URL = "http://localhost:8001/api/v1"

def test_health():
    """Тест здоровья сервиса"""
    print("Тестирование здоровья сервиса...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.json()}")
    print()

def test_bookmarks():
    """Тест закладок"""
    print("Тестирование закладок...")
    
    # Создание закладки
    bookmark_data = {"user_id": "test_user_1", "film_id": "test_film_1"}
    response = requests.post(f"{BASE_URL}/bookmarks/", json=bookmark_data)
    print(f"Создание закладки: {response.status_code}")
    if response.status_code == 201:
        print(f"Создана закладка: {response.json()}")
    
    # Получение закладок пользователя
    response = requests.get(f"{BASE_URL}/bookmarks/user/test_user_1")
    print(f"Получение закладок: {response.status_code}")
    if response.status_code == 200:
        bookmarks = response.json()
        print(f"Найдено закладок: {len(bookmarks)}")
    
    print()

def test_likes():
    """Тест лайков"""
    print("Тестирование лайков...")
    
    # Создание лайка
    like_data = {"user_id": "test_user_1", "film_id": "test_film_1", "rating": 8}
    response = requests.post(f"{BASE_URL}/likes/", json=like_data)
    print(f"Создание лайка: {response.status_code}")
    if response.status_code == 201:
        print(f"Создан лайк: {response.json()}")
    
    # Получение средней оценки фильма
    response = requests.get(f"{BASE_URL}/likes/film/test_film_1/rating")
    print(f"Получение рейтинга фильма: {response.status_code}")
    if response.status_code == 200:
        rating = response.json()
        print(f"Средняя оценка: {rating['average_rating']}, всего оценок: {rating['total_ratings']}")
    
    print()

def test_reviews():
    """Тест рецензий"""
    print("Тестирование рецензий...")
    
    # Создание рецензии
    review_data = {
        "user_id": "test_user_1", 
        "film_id": "test_film_1", 
        "text": "Отличный фильм! Очень понравился сюжет и актерская игра.",
        "rating": 9
    }
    response = requests.post(f"{BASE_URL}/reviews/", json=review_data)
    print(f"Создание рецензии: {response.status_code}")
    if response.status_code == 201:
        print(f"Создана рецензия: {response.json()}")
    
    # Получение рецензий фильма
    response = requests.get(f"{BASE_URL}/reviews/film/test_film_1")
    print(f"Получение рецензий фильма: {response.status_code}")
    if response.status_code == 200:
        reviews = response.json()
        print(f"Найдено рецензий: {reviews['total']}")
    
    print()

def main():
    """Основная функция тестирования"""
    print("Запуск тестов UGC API")
    print("=" * 50)
    
    # Ждем немного, чтобы сервис запустился
    print("Ожидание запуска сервиса...")
    time.sleep(3)
    
    try:
        test_health()
        test_bookmarks()
        test_likes()
        test_reviews()
        
        print("Все тесты завершены!")
        
    except requests.exceptions.ConnectionError:
        print("Ошибка подключения к сервису. Убедитесь, что сервис запущен на порту 8001")
    except Exception as e:
        print(f"Ошибка во время тестирования: {e}")

if __name__ == "__main__":
    main() 