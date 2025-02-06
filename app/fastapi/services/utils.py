import json
from uuid import UUID

class UUIDEncoder(json.JSONEncoder):
    """Converts UUID to str."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)