from jinja2 import Template

from template_worker.db.repositories.template_repository import MessageTemplateRepository


class TemplateService:
    def __init__(self, repository: MessageTemplateRepository):
        self.repository = repository

    async def apply_template(self, template_id: int, keys: dict) -> str:
        template = await self.repository.get_template_by_id(template_id)

        if not template:
            raise ValueError(f"Template with ID {template_id} not found.")

        jinja_template = Template(template.content)
        message = jinja_template.render(keys)

        return message
