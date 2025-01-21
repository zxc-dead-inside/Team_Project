import os
import json
from datetime import datetime


class StateStorage:
    def __init__(self, filename="state.json"):
        self.filename = filename

    def _read_state(self):
        if not os.path.exists(self.filename):
            return {"last_synced_time": datetime.min}

        with open(self.filename, 'r') as f:
            return json.load(f)

    def _write_state(self, state):
        with open(self.filename, 'w') as f:
            json.dump(state, f)

    def get_last_synced_time(self):
        state = self._read_state()
        if state and "last_synced_time" in state:
            last_synced_time_str = state.get("last_synced_time")
            if isinstance(last_synced_time_str, str):
                return datetime.fromisoformat(last_synced_time_str)
            return last_synced_time_str
        return None

    def set_last_synced_time(self, last_synced_time: datetime):
        state = {"last_synced_time": last_synced_time.isoformat()}
        self._write_state(state)
