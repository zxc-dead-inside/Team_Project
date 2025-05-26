"""
Скрипт для быстрого тестирования отдельных компонентов
Полезен для отладки и проверки работоспособности отдельных частей системы
"""

import time
from typing import Optional

from data_generator import CinemaDataGenerator
from database_clients import ClickHouseClient, VerticaClient
from models import BenchmarkConfig


class QuickTester:
    """Класс для быстрого тестирования компонентов"""

    def __init__(self):
        self.generator = CinemaDataGenerator()
        self.clickhouse = None
        self.vertica = None

    def test_data_generation(self, sample_size: int = 100):
        """Тестирует генерацию данных"""
        print(f"🧪 Тестирование генерации данных (выборка: {sample_size})")

        # Тест генерации пользователей
        print("👥 Генерация пользователей...")
        start_time = time.time()
        users = list(self.generator.generate_users(sample_size))
        generation_time = time.time() - start_time
        print(
            f"   ✅ Сгенерировано {len(users)} пользователей за {generation_time:.2f}с"
        )
        print(f"   📋 Пример: {users[0].model_dump()}")
        # Проверка диапазона дат рождения
        birth_dates = [user.birth_date for user in users]
        print(f"   📅 Диапазон дат рождения: {min(birth_dates)} - {max(birth_dates)}")

        # Тест генерации фильмов
        print("\n🎬 Генерация фильмов...")
        start_time = time.time()
        movies = list(self.generator.generate_movies(sample_size))
        generation_time = time.time() - start_time
        print(f"   ✅ Сгенерировано {len(movies)} фильмов за {generation_time:.2f}с")
        print(f"   📋 Пример: {movies[0].model_dump()}")
        # Проверка диапазона дат выхода
        release_dates = [movie.release_date for movie in movies]
        print(f"   📅 Диапазон дат выхода: {min(release_dates)} - {max(release_dates)}")

        # Тест генерации рейтингов
        print("\n⭐ Генерация рейтингов...")
        start_time = time.time()
        ratings = list(
            self.generator.generate_ratings(sample_size, sample_size, sample_size)
        )
        generation_time = time.time() - start_time
        print(f"   ✅ Сгенерировано {len(ratings)} рейтингов за {generation_time:.2f}с")
        print(f"   📋 Пример: {ratings[0].model_dump()}")

        print("\n✅ Тестирование генерации данных завершено успешно")

    def test_database_connections(self):
        """Тестирует подключения к базам данных"""
        print("🔌 Тестирование подключений к базам данных")

        # Тест ClickHouse
        print("\n📊 Тестирование ClickHouse...")
        try:
            self.clickhouse = ClickHouseClient()
            self.clickhouse.connect()
            result, exec_time = self.clickhouse.execute_query("SELECT 1 as test")
            print(f"   ✅ ClickHouse подключен успешно (время: {exec_time:.2f}мс)")
            print(f"   📋 Результат тестового запроса: {result}")
            self.clickhouse.disconnect()
        except Exception as e:
            print(f"   ❌ Ошибка подключения к ClickHouse: {e}")

        # Тест Vertica
        print("\n📈 Тестирование Vertica...")
        try:
            self.vertica = VerticaClient()
            self.vertica.connect()
            result, exec_time = self.vertica.execute_query("SELECT 1 as test")
            print(f"   ✅ Vertica подключена успешно (время: {exec_time:.2f}мс)")
            print(f"   📋 Результат тестового запроса: {result}")
            self.vertica.disconnect()
        except Exception as e:
            print(f"   ❌ Ошибка подключения к Vertica: {e}")

    def test_small_data_insertion(self, batch_size: int = 1000):
        """Тестирует вставку небольшого объема данных"""
        print(f"💾 Тестирование вставки данных (размер батча: {batch_size})")

        if not self.clickhouse or not self.vertica:
            print("❌ Сначала нужно протестировать подключения к БД")
            return

        # Подключение к БД
        self.clickhouse.connect()
        self.vertica.connect()

        try:
            # Создание тестовых таблиц
            print("🏗️ Создание тестовых таблиц...")
            self.clickhouse.drop_tables()
            self.clickhouse.create_tables()
            self.vertica.drop_tables()
            self.vertica.create_tables()

            # Генерация тестовых данных
            print("🎲 Генерация тестовых данных...")
            users = list(self.generator.generate_users(batch_size))
            movies = list(self.generator.generate_movies(batch_size))
            # Используем размер батча для foreign key диапазонов (безопасно)
            ratings = list(
                self.generator.generate_ratings(batch_size, batch_size, batch_size)
            )

            # Тест вставки в ClickHouse
            print("\n📊 Тестирование вставки в ClickHouse...")
            start_time = time.time()
            ch_insert_time_users = self.clickhouse.insert_users(users)
            ch_insert_time_movies = self.clickhouse.insert_movies(movies)
            ch_insert_time_ratings = self.clickhouse.insert_ratings(ratings)
            total_ch_time = time.time() - start_time

            print(f"   ✅ Пользователи: {ch_insert_time_users:.2f}мс")
            print(f"   ✅ Фильмы: {ch_insert_time_movies:.2f}мс")
            print(f"   ✅ Рейтинги: {ch_insert_time_ratings:.2f}мс")
            print(f"   📊 Общее время ClickHouse: {total_ch_time:.2f}с")

            # Тест вставки в Vertica
            print("\n📈 Тестирование вставки в Vertica...")
            start_time = time.time()
            v_insert_time_users = self.vertica.insert_users(users)
            v_insert_time_movies = self.vertica.insert_movies(movies)
            v_insert_time_ratings = self.vertica.insert_ratings(ratings)
            total_v_time = time.time() - start_time

            print(f"   ✅ Пользователи: {v_insert_time_users:.2f}мс")
            print(f"   ✅ Фильмы: {v_insert_time_movies:.2f}мс")
            print(f"   ✅ Рейтинги: {v_insert_time_ratings:.2f}мс")
            print(f"   📊 Общее время Vertica: {total_v_time:.2f}с")

            # Сравнение
            faster_db = "ClickHouse" if total_ch_time < total_v_time else "Vertica"
            speed_diff = (
                abs(total_ch_time - total_v_time)
                / max(total_ch_time, total_v_time)
                * 100
            )
            print(f"\n🏁 {faster_db} быстрее на {speed_diff:.1f}%")

        except Exception as e:
            print(f"❌ Ошибка во время тестирования вставки: {e}")
        finally:
            self.clickhouse.disconnect()
            self.vertica.disconnect()

    def test_sample_queries(self):
        """Тестирует выполнение примеров запросов"""
        print("🔍 Тестирование примеров аналитических запросов")

        if not self.clickhouse or not self.vertica:
            print("❌ Сначала нужно протестировать подключения к БД")
            return

        self.clickhouse.connect()
        self.vertica.connect()

        try:
            # Простые запросы для проверки
            test_queries = [
                (
                    "Количество пользователей",
                    "SELECT COUNT(*) as user_count FROM users",
                    "SELECT COUNT(*) as user_count FROM users",
                ),
                (
                    "Количество фильмов",
                    "SELECT COUNT(*) as movie_count FROM movies",
                    "SELECT COUNT(*) as movie_count FROM movies",
                ),
                (
                    "Средний рейтинг",
                    "SELECT AVG(score) as avg_rating FROM ratings",
                    "SELECT AVG(score) as avg_rating FROM ratings",
                ),
            ]

            for description, ch_query, v_query in test_queries:
                print(f"\n🔍 {description}:")

                # ClickHouse
                try:
                    ch_result, ch_time = self.clickhouse.execute_query(ch_query)
                    print(
                        f"   📊 ClickHouse: {ch_result[0] if ch_result else 'N/A'} ({ch_time:.2f}мс)"
                    )
                except Exception as e:
                    print(f"   ❌ ClickHouse ошибка: {e}")

                # Vertica
                try:
                    v_result, v_time = self.vertica.execute_query(v_query)
                    print(
                        f"   📈 Vertica: {v_result[0] if v_result else 'N/A'} ({v_time:.2f}мс)"
                    )
                except Exception as e:
                    print(f"   ❌ Vertica ошибка: {e}")

        except Exception as e:
            print(f"❌ Ошибка во время тестирования запросов: {e}")
        finally:
            self.clickhouse.disconnect()
            self.vertica.disconnect()

    def get_benchmark_config_from_user(self) -> BenchmarkConfig:
        """Получает параметры бенчмарка от пользователя"""
        print("\n🔧 Настройка параметров бенчмарка")
        print("=" * 40)

        # Значения по умолчанию
        defaults = {
            "num_users": 1000,
            "num_movies": 500,
            "num_ratings": 2000,
            "num_sessions": 3000,
            "num_activities": 5000,
            "num_threads": 3,
            "queries_per_thread": 10,
            "batch_size": 500,
        }

        def get_int_input(prompt: str, default: int) -> int:
            """Получает целочисленный ввод с значением по умолчанию"""
            user_input = input(f"{prompt} (по умолчанию {default:,}): ").strip()
            if not user_input:
                return default
            try:
                return int(user_input.replace(",", "").replace(" ", ""))
            except ValueError:
                print(f"❌ Неверное значение, использую {default:,}")
                return default

        print("📊 Размеры данных:")
        num_users = get_int_input("👥 Количество пользователей", defaults["num_users"])
        num_movies = get_int_input("🎬 Количество фильмов", defaults["num_movies"])
        num_ratings = get_int_input("⭐ Количество рейтингов", defaults["num_ratings"])
        num_sessions = get_int_input(
            "📺 Количество сеансов просмотра", defaults["num_sessions"]
        )
        num_activities = get_int_input(
            "📝 Количество записей активности", defaults["num_activities"]
        )

        print("\n⚙️ Параметры тестирования:")
        num_threads = get_int_input("🔀 Количество потоков", defaults["num_threads"])
        queries_per_thread = get_int_input(
            "🔍 Запросов на поток", defaults["queries_per_thread"]
        )
        batch_size = get_int_input("📦 Размер батча", defaults["batch_size"])

        config = BenchmarkConfig(
            num_users=num_users,
            num_movies=num_movies,
            num_ratings=num_ratings,
            num_sessions=num_sessions,
            num_activities=num_activities,
            num_threads=num_threads,
            queries_per_thread=queries_per_thread,
            batch_size=batch_size,
        )

        print(f"\n✅ Конфигурация создана: {config.model_dump()}")

        # Показать оценку времени выполнения
        print("\n⏱️ Оценка времени выполнения:")
        self.estimate_full_test_time(config)

        # Подтверждение
        confirm = input("\n❓ Продолжить с этими параметрами? (y/n): ").strip().lower()
        if confirm not in ["y", "yes", "да", "д"]:
            print("🚫 Отменено пользователем")
            return None

        return config

    def run_quick_benchmark(self, custom_config: BenchmarkConfig | None = None):
        """Запускает быстрый бенчмарк с возможностью настройки параметров"""
        if custom_config is None:
            # Предложить пользователю выбрать: использовать конфигурацию по умолчанию или настроить
            print("\n🚀 Настройка быстрого бенчмарка")
            print("1. 🔧 Настроить параметры вручную")
            print("2. ⚡ Использовать мини-конфигурацию по умолчанию")

            choice = input("Выберите опцию (1/2): ").strip()

            if choice == "1":
                custom_config = self.get_benchmark_config_from_user()
                if custom_config is None:
                    return  # Пользователь отменил
            else:
                # Конфигурация по умолчанию
                custom_config = BenchmarkConfig(
                    num_users=1000,
                    num_movies=500,
                    num_ratings=2000,
                    num_sessions=3000,
                    num_activities=5000,
                    num_threads=3,
                    queries_per_thread=10,
                    batch_size=500,
                )
                print(
                    f"🔧 Используется конфигурация по умолчанию: {custom_config.model_dump()}"
                )

        print("\n🚀 Запуск быстрого бенчмарка...")

        # Импорт главного класса
        from main import CinemaPerformanceStudy

        study = CinemaPerformanceStudy(custom_config)
        success = study.run_full_study()

        if success:
            print("✅ Быстрый бенчмарк завершен успешно!")
        else:
            print("❌ Быстрый бенчмарк завершен с ошибками")

    def estimate_full_test_time(self, config: BenchmarkConfig):
        """Оценивает время выполнения полного теста"""
        data_estimate = self.generator.estimate_data_size(config)

        # Примерные оценки времени
        generation_time_min = data_estimate["estimated_generation_time_minutes"]
        insertion_time_min = generation_time_min * 2  # Вставка в 2 БД
        queries_time_min = 5  # Аналитические запросы
        concurrent_time_min = (
            config.num_threads * config.queries_per_thread
        ) / 1000  # Многопоточные запросы

        total_time_min = (
            generation_time_min
            + insertion_time_min
            + queries_time_min
            + concurrent_time_min
        )

        print(f"   🎲 Генерация данных: ~{generation_time_min:.1f} минут")
        print(f"   💾 Вставка данных: ~{insertion_time_min:.1f} минут")
        print(f"   🔍 Аналитические запросы: ~{queries_time_min:.1f} минут")
        print(f"   🚀 Многопоточное тестирование: ~{concurrent_time_min:.1f} минут")
        print(
            f"   ⏱️ Общее время: ~{total_time_min:.1f} минут ({total_time_min / 60:.1f} часов)"
        )
        print(f"   📁 Размер данных: ~{data_estimate['estimated_size_mb']:.1f} МБ")


def main():
    """Главная функция для быстрого тестирования"""
    tester = QuickTester()

    print("🧪 БЫСТРОЕ ТЕСТИРОВАНИЕ КОМПОНЕНТОВ")
    print("=" * 50)

    while True:
        print("\nВыберите тест:")
        print("1. 🎲 Тестирование генерации данных")
        print("2. 🔌 Тестирование подключений к БД")
        print("3. 💾 Тестирование вставки данных")
        print("4. 🔍 Тестирование примеров запросов")
        print("5. 🚀 Быстрый бенчмарк (настраиваемый)")
        print("6. ⏱️ Оценка времени полного теста")
        print("0. 🚪 Выход")

        choice = input("\nВведите номер теста: ").strip()

        if choice == "1":
            sample_size = input("Размер выборки (по умолчанию 100): ").strip()
            sample_size = int(sample_size) if sample_size else 100
            tester.test_data_generation(sample_size)

        elif choice == "2":
            tester.test_database_connections()

        elif choice == "3":
            batch_size = input("Размер батча (по умолчанию 1000): ").strip()
            batch_size = int(batch_size) if batch_size else 1000
            tester.test_small_data_insertion(batch_size)

        elif choice == "4":
            tester.test_sample_queries()

        elif choice == "5":
            tester.run_quick_benchmark()

        elif choice == "6":
            config = BenchmarkConfig()  # Конфигурация по умолчанию
            tester.estimate_full_test_time(config)

        elif choice == "0":
            print("👋 До свидания!")
            break

        else:
            print("❌ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
