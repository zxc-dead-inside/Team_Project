from datetime import datetime

from sqlalchemy.orm import Session
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
from notification_app.services.services import (MessageService,
                                                MessageTemplateService,
                                                ScheduledTaskService)

from fastapi import APIRouter, Depends, HTTPException


router = APIRouter()


# Шаблоны сообщений
@router.post("/templates/", response_model=MessageTemplate)
def create_template(template: MessageTemplateCreate, db: Session = Depends(get_db)):
    return MessageTemplateService.create_template(db, template)


@router.get("/templates/", response_model=list[MessageTemplate])
def get_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return MessageTemplateService.get_templates(db, skip=skip, limit=limit)


@router.get("/templates/{template_id}", response_model=MessageTemplate)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = MessageTemplateService.get_template(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template


@router.put("/templates/{template_id}", response_model=MessageTemplate)
def update_template(
    template_id: int, template: MessageTemplateUpdate, db: Session = Depends(get_db)
):
    updated_template = MessageTemplateService.update_template(db, template_id, template)
    if updated_template is None:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return updated_template


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    success = MessageTemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return {"message": "Шаблон удален"}


# Сообщения
@router.post("/messages/", response_model=Message)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    message_obj = MessageService.create_message(db, message)
    MessageService.send_message_immediately(db, message_obj)
    return message_obj


@router.get("/messages/", response_model=list[Message])
def get_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return MessageService.get_messages(db, skip=skip, limit=limit)


@router.get("/messages/{message_id}", response_model=Message)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = MessageService.get_message(db, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return message


# Запланированные задачи
@router.post("/scheduled-tasks/", response_model=ScheduledTask)
def create_scheduled_task(task: ScheduledTaskCreate, db: Session = Depends(get_db)):
    return ScheduledTaskService.create_scheduled_task(db, task)


@router.get("/scheduled-tasks/", response_model=list[ScheduledTask])
def get_scheduled_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ScheduledTaskService.get_scheduled_tasks(db, skip=skip, limit=limit)


@router.get("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
def get_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    task = ScheduledTaskService.get_scheduled_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Запланированная задача не найдена")
    return task


@router.put("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
def update_scheduled_task(task_id: int, task: ScheduledTaskUpdate, db: Session = Depends(get_db)):
    updated_task = ScheduledTaskService.update_scheduled_task(db, task_id, task)
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Запланированная задача не найдена")
    return updated_task


@router.delete("/scheduled-tasks/{task_id}")
def delete_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    success = ScheduledTaskService.delete_scheduled_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Запланированная задача не найдена")
    return {"message": "Запланированная задача удалена"}


# Утилиты
@router.get("/health/")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
