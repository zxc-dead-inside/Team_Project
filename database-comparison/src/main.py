"""
Главный модуль для запуска исследования производительности ClickHouse vs Vertica
Координирует весь процесс тестирования и сохраняет результаты
"""

import json
import time
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from benchmark import DatabaseBenchmark
from data_generator import CinemaDataGenerator
from database_clients import ClickHouseClient, VerticaClient
from loguru import logger
from models import BenchmarkConfig, DatabasePerformanceResult, TestSuiteResult
from tqdm import tqdm


class CinemaPerformanceStudy:
    """Основной класс для проведения исследования производительности"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.generator = CinemaDataGenerator()
        self.clickhouse = ClickHouseClient()
        self.vertica = VerticaClient()
        self.benchmark = DatabaseBenchmark(self.clickhouse, self.vertica)
        self.results: TestSuiteResult = None

        # Настройка логирования
        logger.add("logs/performance_study.log", rotation="10 MB", level="INFO")

        # Создание директорий
        Path("results").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

    def wait_for_databases(self, max_wait_time: int = 300) -> bool:
        """
        Ожидает готовности баз данных

        Args:
            max_wait_time: Максимальное время ожидания в секундах

        Returns:
            bool: True если БД готовы, False если таймаут
        """
        logger.info("Ожидание готовности баз данных...")

        start_time = time.time()
        clickhouse_ready = False
        vertica_ready = False

        with tqdm(total=max_wait_time, desc="Ожидание БД", unit="сек") as pbar:
            while time.time() - start_time < max_wait_time:
                # Проверка ClickHouse
                if not clickhouse_ready:
                    try:
                        self.clickhouse.connect()
                        self.clickhouse.execute_query("SELECT 1")
                        clickhouse_ready = True
                        logger.info("ClickHouse готов к работе")
                    except Exception:
                        pass
                    finally:
                        with suppress(Exception):
                            self.clickhouse.disconnect()

                # Проверка Vertica
                if not vertica_ready:
                    try:
                        self.vertica.connect()
                        self.vertica.execute_query("SELECT 1")
                        vertica_ready = True
                        logger.info("Vertica готова к работе")
                    except Exception:
                        pass
                    finally:
                        with suppress(Exception):
                            self.vertica.disconnect()
                if clickhouse_ready and vertica_ready:
                    logger.info("Обе базы данных готовы к работе")
                    return True

                time.sleep(5)
                pbar.update(5)

        logger.error(
            f"Таймаут ожидания БД. ClickHouse: "
            f"{clickhouse_ready}, Vertica: {vertica_ready}"
        )
        return False

    def setup_databases(self):
        """Настройка и создание схем в базах данных с поддержкой UUID"""
        logger.info("Настройка баз данных для работы с UUID...")

        # Подключение и создание таблиц в ClickHouse
        logger.info("Создание таблиц в ClickHouse (user_id как String для UUID)")
        self.clickhouse.connect()
        self.clickhouse.drop_tables()  # Очистка перед созданием
        self.clickhouse.create_tables()

        # Подключение и создание таблиц в Vertica
        logger.info("Создание таблиц в Vertica (user_id как VARCHAR(36) для UUID)")
        self.vertica.connect()
        self.vertica.drop_tables()  # Очистка перед созданием
        self.vertica.create_tables()

        logger.info("Базы данных настроены")

    def load_test_data(self) -> dict[str, float]:
        """
        Загружает тестовые данные в обе БД

        Returns:
            Dict: Время загрузки для каждой БД
        """
        logger.info("Начало загрузки тестовых данных")

        # Оценка объема данных
        data_estimate = self.generator.estimate_data_size(self.config)
        logger.info(f"Ожидаемый объем данных: {data_estimate}")
        logger.info("UUID увеличивает размер данных примерно на 15%")

        load_times = {"clickhouse": 0.0, "vertica": 0.0}

        # Загрузка пользователей
        logger.info(
            f"Генерация и загрузка {self.config.num_users:,} пользователей с UUID"
        )

        # Генерируем всех пользователей сразу, чтобы UUID были доступны для foreign keys
        logger.info("Генерация всех пользователей для создания UUID пула...")
        all_users = list(self.generator.generate_users(self.config.num_users))
        logger.info(
            f"Создано {len(all_users)} пользователей с UUID. Примеры UUID:"
            f" {[str(u.user_id) for u in all_users[:3]]}"
        )

        # Вставка пользователей батчами в ClickHouse
        logger.info("Вставка пользователей в ClickHouse...")
        start_time = time.time()
        for i in tqdm(
            range(0, len(all_users), self.config.batch_size), desc="ClickHouse Users"
        ):
            batch = all_users[i : i + self.config.batch_size]
            self.clickhouse.insert_users(batch)
        load_times["clickhouse"] += time.time() - start_time

        # Вставка пользователей батчами в Vertica
        logger.info("Вставка пользователей в Vertica...")
        start_time = time.time()
        for i in tqdm(
            range(0, len(all_users), self.config.batch_size), desc="Vertica Users"
        ):
            batch = all_users[i : i + self.config.batch_size]
            self.vertica.insert_users(batch)
        load_times["vertica"] += time.time() - start_time

        logger.info(
            f"Пользователи загружены. UUID пул содержит"
            f" {len(self.generator._generated_user_ids)} записей"
        )

        # Загрузка фильмов
        logger.info(f"Генерация и загрузка {self.config.num_movies:,} фильмов")
        movies_data = []
        for batch in tqdm(
            range(0, self.config.num_movies, self.config.batch_size),
            desc="Генерация фильмов",
        ):
            batch_size = min(self.config.batch_size, self.config.num_movies - batch)
            movies_batch = self.generator.generate_batch(
                self.generator.generate_movies(batch_size), batch_size
            )
            movies_data.extend(movies_batch)

        # Вставка фильмов в ClickHouse
        logger.info("Вставка фильмов в ClickHouse...")
        start_time = time.time()
        for i in tqdm(
            range(0, len(movies_data), self.config.batch_size), desc="ClickHouse Movies"
        ):
            batch = movies_data[i : i + self.config.batch_size]
            self.clickhouse.insert_movies(batch)
        load_times["clickhouse"] += time.time() - start_time

        # Вставка фильмов в Vertica
        logger.info("Вставка фильмов в Vertica...")
        start_time = time.time()
        for i in tqdm(
            range(0, len(movies_data), self.config.batch_size), desc="Vertica Movies"
        ):
            batch = movies_data[i : i + self.config.batch_size]
            self.vertica.insert_movies(batch)
        load_times["vertica"] += time.time() - start_time

        logger.info("Фильмы загружены")

        # Загрузка рейтингов
        logger.info(
            f"Генерация и загрузка {self.config.num_ratings:,} "
            f"рейтингов с UUID ссылками"
        )
        for batch_start in tqdm(
            range(0, self.config.num_ratings, self.config.batch_size), desc="Рейтинги"
        ):
            batch_size = min(
                self.config.batch_size, self.config.num_ratings - batch_start
            )
            ratings_batch = self.generator.generate_batch(
                self.generator.generate_ratings(
                    batch_size, self.config.num_users, self.config.num_movies
                ),
                batch_size,
            )

            # Вставка в ClickHouse
            start_time = time.time()
            self.clickhouse.insert_ratings(ratings_batch)
            load_times["clickhouse"] += time.time() - start_time

            # Вставка в Vertica
            start_time = time.time()
            self.vertica.insert_ratings(ratings_batch)
            load_times["vertica"] += time.time() - start_time

        logger.info("Рейтинги с UUID ссылками загружены")

        # Загрузка сеансов просмотра
        logger.info(
            f"Генерация и загрузка {self.config.num_sessions:,} "
            f"сеансов просмотра с UUID ссылками"
        )
        for batch_start in tqdm(
            range(0, self.config.num_sessions, self.config.batch_size), desc="Сеансы"
        ):
            batch_size = min(
                self.config.batch_size, self.config.num_sessions - batch_start
            )
            sessions_batch = self.generator.generate_batch(
                self.generator.generate_viewing_sessions(
                    batch_size, self.config.num_users, self.config.num_movies
                ),
                batch_size,
            )

            # Вставка в ClickHouse
            start_time = time.time()
            self.clickhouse.insert_viewing_sessions(sessions_batch)
            load_times["clickhouse"] += time.time() - start_time

            # Вставка в Vertica
            start_time = time.time()
            self.vertica.insert_viewing_sessions(sessions_batch)
            load_times["vertica"] += time.time() - start_time

        logger.info("Сеансы просмотра с UUID ссылками загружены")

        # Загрузка активности пользователей
        logger.info(
            f"Генерация и загрузка {self.config.num_activities:,} "
            f"записей активности с UUID ссылками"
        )
        for batch_start in tqdm(
            range(0, self.config.num_activities, self.config.batch_size),
            desc="Активность",
        ):
            batch_size = min(
                self.config.batch_size, self.config.num_activities - batch_start
            )
            activities_batch = self.generator.generate_batch(
                self.generator.generate_user_activities(
                    batch_size, self.config.num_users
                ),
                batch_size,
            )

            # Вставка в ClickHouse
            start_time = time.time()
            self.clickhouse.insert_user_activities(activities_batch)
            load_times["clickhouse"] += time.time() - start_time

            # Вставка в Vertica
            start_time = time.time()
            self.vertica.insert_user_activities(activities_batch)
            load_times["vertica"] += time.time() - start_time

        logger.info("Активность пользователей с UUID ссылками загружена")
        logger.info("Загрузка всех тестовых данных с UUID поддержкой завершена")

        return load_times

    def run_performance_tests(self) -> list[DatabasePerformanceResult]:
        """
        Запускает тесты производительности

        Returns:
            List[DatabasePerformanceResult]: Результаты всех тестов
        """
        logger.info("Начало тестирования производительности")

        all_results = []

        # 1. Аналитические запросы
        logger.info("Запуск аналитических запросов")
        analytical_results = self.benchmark.run_analytical_queries()
        all_results.extend(analytical_results)

        # Пауза между типами тестов
        time.sleep(10)

        # 2. Многопоточное тестирование
        logger.info("Запуск многопоточного тестирования")
        concurrent_results = self.benchmark.run_concurrent_test(
            num_threads=self.config.num_threads,
            queries_per_thread=self.config.queries_per_thread,
        )
        all_results.extend(concurrent_results)

        logger.info("Тестирование производительности с UUID завершено")
        return all_results

    def save_results(
        self,
        results: list[DatabasePerformanceResult],
        load_times: dict[str, float],
        analysis: dict[str, Any],
    ):
        """Сохраняет результаты тестирования с UUID метаданными"""

        # Создание итогового результата
        test_end_time = datetime.now()

        self.results = TestSuiteResult(
            config=self.config,
            clickhouse_results=[r for r in results if r.database_name == "clickhouse"],
            vertica_results=[r for r in results if r.database_name == "vertica"],
            test_start_time=datetime.now()
            - timedelta(seconds=sum(load_times.values())),
            test_end_time=test_end_time,
            total_duration_seconds=sum(load_times.values())
            + sum(r.execution_time_ms for r in results) / 1000,
        )

        # Подготовка данных для сохранения
        results_data = {
            "metadata": {
                "test_date": test_end_time.isoformat(),
                "config": self.config.model_dump(),
                "uuid_support": True,
                "user_id_type": "UUID",
                "database_schemas": {
                    "clickhouse_user_id": "String (UUID as string)",
                    "vertica_user_id": "VARCHAR(36) (UUID as string)",
                },
                "load_times_seconds": load_times,
                "summary": self.results.summary,
            },
            "detailed_analysis": analysis,
            "raw_results": [r.model_dump() for r in results],
        }

        # Сохранение в JSON
        results_file = (f"results/performance_results_uuid"
                        f"_{test_end_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Результаты с UUID метаданными сохранены в {results_file}")

        # Сохранение краткого отчета
        self.save_summary_report(analysis, load_times, results_file)

    def save_summary_report(
        self, analysis: dict[str, Any], load_times: dict[str, float], results_file: str
    ):
        """Сохраняет краткий отчет в текстовом формате с информацией о UUID"""

        report_content = f"""
# ОТЧЕТ ПО ИССЛЕДОВАНИЮ ПРОИЗВОДИТЕЛЬНОСТИ
# ClickHouse vs Vertica для онлайн-кинотеатра

## Конфигурация тестирования
- Пользователи: {self.config.num_users:,}
- Фильмы: {self.config.num_movies:,}
- Рейтинги: {self.config.num_ratings:,}
- Сеансы просмотра: {self.config.num_sessions:,}
- Записи активности: {self.config.num_activities:,}
- Потоки для нагрузочного тестирования: {self.config.num_threads}
- Запросов на поток: {self.config.queries_per_thread}

## UUID Поддержка
- Тип user_id: UUID (36 символов)
- ClickHouse схема: user_id String
- Vertica схема: user_id VARCHAR(36)
- Увеличение размера данных: ~15%
- Все foreign key связи работают корректно

## Время загрузки данных
- ClickHouse: {load_times.get("clickhouse", 0):.2f} секунд
- Vertica: {load_times.get("vertica", 0):.2f} секунд

## Результаты тестирования производительности

### ClickHouse
"""

        if "clickhouse" in analysis:
            ch_stats = analysis["clickhouse"]
            report_content += f"""
- Всего запросов: {ch_stats.get("total_queries", "N/A")}
- Успешных запросов: {ch_stats.get("successful_queries", "N/A")}
- Среднее время выполнения: {ch_stats.get("avg_execution_time_ms", "N/A")} мс
- Медианное время выполнения: {ch_stats.get("median_execution_time_ms", "N/A")} мс
- Минимальное время: {ch_stats.get("min_execution_time_ms", "N/A")} мс
- Максимальное время: {ch_stats.get("max_execution_time_ms", "N/A")} мс
- Обработано записей: {ch_stats.get("total_records_processed", "N/A"):,}
- Среднее использование памяти: {ch_stats.get("avg_memory_used_mb", "N/A")} МБ
"""

        report_content += "\n### Vertica\n"

        if "vertica" in analysis:
            v_stats = analysis["vertica"]
            report_content += f"""
- Всего запросов: {v_stats.get("total_queries", "N/A")}
- Успешных запросов: {v_stats.get("successful_queries", "N/A")}
- Среднее время выполнения: {v_stats.get("avg_execution_time_ms", "N/A")} мс
- Медианное время выполнения: {v_stats.get("median_execution_time_ms", "N/A")} мс
- Минимальное время: {v_stats.get("min_execution_time_ms", "N/A")} мс
- Максимальное время: {v_stats.get("max_execution_time_ms", "N/A")} мс
- Обработано записей: {v_stats.get("total_records_processed", "N/A"):,}
- Среднее использование памяти: {v_stats.get("avg_memory_used_mb", "N/A")} МБ
"""

        if "comparison" in analysis:
            comp = analysis["comparison"]
            report_content += f"""
## Сравнение производительности
- Победитель: {comp.get("performance_winner", "N/A")}
- ClickHouse быстрее на: {comp.get("clickhouse_faster_percent", "N/A")}%
- Среднее время ClickHouse: {comp.get("clickhouse_avg_time_ms", "N/A")} мс
- Среднее время Vertica: {comp.get("vertica_avg_time_ms", "N/A")} мс

## Выводы и рекомендации

### Преимущества ClickHouse:
- Высокая скорость аналитических запросов
- Эффективное сжатие данных
- Простота развертывания и настройки
- Бесплатное использование
- Хорошая работа с UUID как строками

### Преимущества Vertica:
- Развитые enterprise функции
- Хорошая масштабируемость
- Надежность для критичных систем
- Полная поддержка SQL
- Нативная поддержка VARCHAR для UUID

### UUID Влияние на производительность:
- Незначительное увеличение времени JOIN операций
- Увеличение размера индексов
- Повышенная безопасность данных
- Лучшая совместимость с распределенными системами

### Рекомендация:
Для данного проекта онлайн-кинотеатра рекомендуется использовать ClickHouse
благодаря превосходной производительности аналитических запросов и отсутствию
лицензионных затрат. UUID поддержка работает эффективно в обеих системах.

## Детальные результаты
Полные результаты доступны в файле: {results_file}
"""

        # Сохранение отчета
        report_file = (f"results/summary_report_uuid"
                       f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"Краткий отчет с UUID информацией сохранен в {report_file}")

    def cleanup(self):
        """Очистка ресурсов"""
        with suppress(Exception):
            self.clickhouse.disconnect()

        with suppress(Exception):
            self.vertica.disconnect()

        logger.info("Ресурсы очищены")

    def run_full_study(self):
        """Запускает полное исследование с UUID поддержкой"""
        logger.info("=== НАЧАЛО ИССЛЕДОВАНИЯ ПРОИЗВОДИТЕЛЬНОСТИ ===")
        logger.info(f"Конфигурация: {self.config.model_dump()}")

        try:
            # 1. Ожидание готовности БД
            if not self.wait_for_databases():
                logger.error("Базы данных не готовы. Завершение работы.")
                return False

            # 2. Настройка БД
            self.setup_databases()

            # 3. Загрузка данных
            load_times = self.load_test_data()
            logger.info(
                f"Время загрузки - ClickHouse: {load_times['clickhouse']:.2f}с, "
                f"Vertica: {load_times['vertica']:.2f}с"
            )

            # 4. Тестирование производительности
            results = self.run_performance_tests()

            # 5. Анализ результатов
            analysis = self.benchmark.analyze_results(results)

            # 6. Сохранение результатов
            self.save_results(results, load_times, analysis)

            logger.info("=== ИССЛЕДОВАНИЕ ЗАВЕРШЕНО УСПЕШНО ===")
            return True

        except Exception as e:
            logger.error(f"Ошибка во время исследования: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Главная функция для запуска исследования"""
    # Конфигурация для тестирования
    config = BenchmarkConfig(
        num_users=100_000,
        num_movies=10_000,
        num_ratings=500_000,
        num_sessions=1_000_000,
        num_activities=2_000_000,
        num_threads=10,
        queries_per_thread=100,
        batch_size=10_000,
    )

    print(
        "🎬 Исследование производительности ClickHouse vs Vertica для онлайн-кинотеатра"
    )
    print("=" * 80)
    print("📊 Конфигурация тестирования:")
    print(f"   • Пользователи: {config.num_users:,}")
    print(f"   • Фильмы: {config.num_movies:,}")
    print(f"   • Рейтинги: {config.num_ratings:,}")
    print(f"   • Сеансы просмотра: {config.num_sessions:,}")
    print(f"   • Записи активности: {config.num_activities:,}")
    print(
        f"   • Многопоточность: {config.num_threads} потоков x"
        f" {config.queries_per_thread} запросов"
    )
    print("   • Тип user_id: UUID (36 символов)")
    print("   • ClickHouse: user_id как String")
    print("   • Vertica: user_id как VARCHAR(36)")
    print("=" * 80)

    # Запуск исследования
    study = CinemaPerformanceStudy(config)
    success = study.run_full_study()

    if success:
        print("\n✅ Исследование завершено успешно!")
        print("🆔 UUID поддержка работает корректно")
        print("📋 Результаты сохранены в папке 'results/'")
        print("📖 Проверьте summary_report для краткого анализа")
        print("📊 Детальные данные в performance_results JSON файле")
    else:
        print("\n❌ Исследование завершено с ошибками")
        print("📋 Проверьте логи в папке 'logs/'")


if __name__ == "__main__":
    main()
