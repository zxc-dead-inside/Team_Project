from datetime import datetime

from dateutil.relativedelta import relativedelta  # type: ignore


def generate_partition_login_history(
        months_ahead: int = 12, start_months: int = 0
) -> str:
    statements = []
    now = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_date = now + relativedelta(months=start_months)

    for i in range(months_ahead):
        partition_start = start_date + relativedelta(months=i)
        partition_end = partition_start + relativedelta(months=1)
        name = f"login_history_{partition_start.year}_{str(partition_start.month).zfill(2)}"

        sql = f"""
        CREATE TABLE IF NOT EXISTS {name} PARTITION OF login_history
        FOR VALUES FROM ('{partition_start.strftime('%Y-%m-%d')}') TO ('{partition_end.strftime('%Y-%m-%d')}');
        
        CREATE INDEX IF NOT EXISTS idx_{name}_id ON {name} (id);
        CREATE INDEX IF NOT EXISTS idx_{name}_user_id ON {name} (user_id);
        CREATE INDEX IF NOT EXISTS idx_{name}_login_time ON {name} (login_time);
        CREATE INDEX IF NOT EXISTS idx_{name}_successful ON {name} (successful);
        """
        statements.append(sql.strip())

    return "\n".join(statements)
