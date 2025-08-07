from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from notification_app.core.database import get_db
from notification_app.schemas.schemas import (
    Message,
    MessageCreate,
    MessageTemplate,
    MessageTemplateCreate,
    MessageTemplateUpdate,
    ScheduledTask,
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
)
from notification_app.services.services import (
    MessageService,
    MessageTemplateService,
    ScheduledTaskService
)
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/api/v1",
    tags=["Notification Service"],
    responses={404: {"description": "Not found"}},
)

router = APIRouter()


# Шаблоны сообщений
@router.post("/templates/", response_model=MessageTemplate)
async def create_template(template: MessageTemplateCreate, db: AsyncSession = Depends(get_db)):
    return await MessageTemplateService.create_template(db, template)


@router.get("/templates/", response_model=list[MessageTemplate])
async def get_templates(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await MessageTemplateService.get_templates(db, skip=skip, limit=limit)


@router.get("/templates/{template_id}", response_model=MessageTemplate)
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    template = await MessageTemplateService.get_template(db, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон с указанным ID не найден"
        )
    return template


@router.put("/templates/{template_id}", response_model=MessageTemplate)
async def update_template(
    template_id: int, template: MessageTemplateUpdate, db: AsyncSession = Depends(get_db)
):
    updated_template = await MessageTemplateService.update_template(db, template_id, template)
    if updated_template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон не найден"
        )
    return updated_template


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    success = await MessageTemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон не найден"
        )
    return {"message": "Шаблон успешно удален"}


# Сообщения
@router.post("/messages/", response_model=Message)
async def create_message(message: MessageCreate, db: AsyncSession = Depends(get_db)):
    message_obj = await MessageService.create_message(db, message)
    await MessageService.send_message_immediately(db, message_obj)
    return message_obj


@router.get("/messages/", response_model=list[Message])
async def get_messages(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await MessageService.get_messages(db, skip=skip, limit=limit)


@router.get("/messages/{message_id}", response_model=Message)
async def get_message(message_id: int, db: AsyncSession = Depends(get_db)):
    message = await MessageService.get_message(db, message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено"
        )
    return message


# Запланированные задачи
@router.post("/scheduled-tasks/", response_model=ScheduledTask)
async def create_scheduled_task(task: ScheduledTaskCreate, db: AsyncSession = Depends(get_db)):
    return await ScheduledTaskService.create_scheduled_task(db, task)


@router.get("/scheduled-tasks/", response_model=list[ScheduledTask])
async def get_scheduled_tasks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await ScheduledTaskService.get_scheduled_tasks(db, skip=skip, limit=limit)


@router.get("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
async def get_scheduled_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await ScheduledTaskService.get_scheduled_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запланированная задача не найдена"
        )
    return task


@router.put("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
async def update_scheduled_task(task_id: int, task: ScheduledTaskUpdate, db: AsyncSession = Depends(get_db)):
    updated_task = await ScheduledTaskService.update_scheduled_task(db, task_id, task)
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запланированная задача не найдена"
        )
    return updated_task


@router.delete("/scheduled-tasks/{task_id}")
async def delete_scheduled_task(task_id: int, db: AsyncSession = Depends(get_db)):
    success = await ScheduledTaskService.delete_scheduled_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запланированная задача не найдена"
        )
    return {"message": "Запланированная задача успешно удалена"}

@router.get(
    "/health/",
    summary="Проверка работоспособности сервиса",
    description="Возвращает текущий статус сервиса уведомлений.",
    response_description="Статус сервиса и временная метка"
)
def health_check():
    """
    Проверка работоспособности сервиса.
    
    Возвращает:
    - **status**: Текущий статус сервиса ('healthy' или 'unhealthy')
    - **timestamp**: Временная метка проверки в UTC
    
    Используется для мониторинга и балансировки нагрузки.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}
