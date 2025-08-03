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

@router.post(
    "/templates/",
    response_model=MessageTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый шаблон сообщения",
    description="Создает новый шаблон сообщения с указанными параметрами.",
    response_description="Созданный шаблон сообщения"
)
def create_template(template: MessageTemplateCreate, db: Session = Depends(get_db)):
    """
    Создает новый шаблон сообщения.
    
    Параметры:
    - **name**: Название шаблона (обязательно)
    - **content**: Содержимое шаблона с поддерживаемыми переменными (обязательно)
    - **message_type**: Тип сообщения (email, sms, push) (обязательно)
    - **description**: Описание шаблона (опционально)
    
    Возвращает созданный шаблон с присвоенным ID.
    """
    return MessageTemplateService.create_template(db, template)

@router.get(
    "/templates/",
    response_model=list[MessageTemplate],
    summary="Получить список шаблонов сообщений",
    description="Возвращает список всех шаблонов сообщений с возможностью пагинации.",
    response_description="Список шаблонов сообщений"
)
def get_templates(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Получает список шаблонов сообщений с пагинацией.
    
    Параметры:
    - **skip**: Количество записей для пропуска (по умолчанию 0)
    - **limit**: Максимальное количество возвращаемых записей (по умолчанию 100)
    
    Возвращает список шаблонов.
    """
    return MessageTemplateService.get_templates(db, skip=skip, limit=limit)

@router.get(
    "/templates/{template_id}",
    response_model=MessageTemplate,
    summary="Получить шаблон по ID",
    description="Возвращает шаблон сообщения по указанному идентификатору.",
    response_description="Найденный шаблон сообщения",
    responses={
        404: {"description": "Шаблон не найден"}
    }
)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """
    Получает шаблон сообщения по его уникальному идентификатору.
    
    Параметры:
    - **template_id**: ID шаблона (обязательно)
    
    Возвращает объект шаблона или 404 ошибку, если шаблон не найден.
    """
    template = MessageTemplateService.get_template(db, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон с указанным ID не найден"
        )
    return template

@router.put(
    "/templates/{template_id}",
    response_model=MessageTemplate,
    summary="Обновить шаблон сообщения",
    description="Обновляет существующий шаблон сообщения по указанному ID.",
    response_description="Обновленный шаблон сообщения",
    responses={
        404: {"description": "Шаблон не найден"}
    }
)
def update_template(
    template_id: int, 
    template: MessageTemplateUpdate, 
    db: Session = Depends(get_db)
):
    """
    Обновляет существующий шаблон сообщения.
    
    Параметры:
    - **template_id**: ID обновляемого шаблона (обязательно)
    - **name**: Новое название шаблона (опционально)
    - **content**: Новое содержимое шаблона (опционально)
    - **message_type**: Новый тип сообщения (опционально)
    - **description**: Новое описание шаблона (опционально)
    
    Возвращает обновленный объект шаблона или 404 ошибку, если шаблон не найден.
    """
    updated_template = MessageTemplateService.update_template(db, template_id, template)
    if updated_template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон не найден"
        )
    return updated_template

@router.delete(
    "/templates/{template_id}",
    summary="Удалить шаблон сообщения",
    description="Удаляет шаблон сообщения по указанному ID.",
    response_description="Результат операции удаления",
    responses={
        200: {"description": "Шаблон успешно удален"},
        404: {"description": "Шаблон не найден"}
    }
)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """
    Удаляет шаблон сообщения по его ID.
    
    Параметры:
    - **template_id**: ID удаляемого шаблона (обязательно)
    
    Возвращает сообщение об успешном удалении или 404 ошибку, если шаблон не найден.
    """
    success = MessageTemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон не найден"
        )
    return {"message": "Шаблон успешно удален"}

@router.post(
    "/messages/",
    response_model=Message,
    status_code=status.HTTP_201_CREATED,
    summary="Создать и отправить сообщение",
    description="Создает новое сообщение и немедленно отправляет его.",
    response_description="Созданное и отправленное сообщение"
)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """
    Создает и немедленно отправляет новое сообщение.
    
    Параметры:
    - **recipient**: Адрес получателя (email/телефон и т.д.) (обязательно)
    - **template_id**: ID используемого шаблона (обязательно)
    - **context**: Контекстные данные для заполнения шаблона (в формате JSON)
    - **send_at**: Время отправки (если требуется отложенная отправка)
    
    Возвращает созданное сообщение с информацией о статусе отправки.
    """
    message_obj = MessageService.create_message(db, message)
    MessageService.send_message_immediately(db, message_obj)
    return message_obj

@router.get(
    "/messages/",
    response_model=list[Message],
    summary="Получить список сообщений",
    description="Возвращает список всех сообщений с возможностью пагинации.",
    response_description="Список сообщений"
)
def get_messages(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Получает список сообщений с пагинацией.
    
    Параметры:
    - **skip**: Количество записей для пропуска (по умолчанию 0)
    - **limit**: Максимальное количество возвращаемых записей (по умолчанию 100)
    
    Возвращает список сообщений с информацией о статусе отправки.
    """
    return MessageService.get_messages(db, skip=skip, limit=limit)

@router.get(
    "/messages/{message_id}",
    response_model=Message,
    summary="Получить сообщение по ID",
    description="Возвращает сообщение по указанному идентификатору.",
    response_description="Найденное сообщение",
    responses={
        404: {"description": "Сообщение не найдено"}
    }
)
def get_message(message_id: int, db: Session = Depends(get_db)):
    """
    Получает сообщение по его уникальному идентификатору.
    
    Параметры:
    - **message_id**: ID сообщения (обязательно)
    
    Возвращает объект сообщения или 404 ошибку, если сообщение не найдено.
    """
    message = MessageService.get_message(db, message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено"
        )
    return message

@router.post(
    "/scheduled-tasks/",
    response_model=ScheduledTask,
    status_code=status.HTTP_201_CREATED,
    summary="Создать запланированную задачу",
    description="Создает новую запланированную задачу для отложенной отправки сообщений.",
    response_description="Созданная запланированная задача"
)
def create_scheduled_task(task: ScheduledTaskCreate, db: Session = Depends(get_db)):
    """
    Создает новую запланированную задачу.
    
    Параметры:
    - **message_id**: ID сообщения для отправки (обязательно)
    - **scheduled_time**: Дата и время запланированной отправки (обязательно)
    - **status**: Статус задачи (по умолчанию 'pending')
    
    Возвращает созданную запланированную задачу.
    """
    return ScheduledTaskService.create_scheduled_task(db, task)

@router.get(
    "/scheduled-tasks/",
    response_model=list[ScheduledTask],
    summary="Получить список запланированных задач",
    description="Возвращает список всех запланированных задач с возможностью пагинации.",
    response_description="Список запланированных задач"
)
def get_scheduled_tasks(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Получает список запланированных задач с пагинацией.
    
    Параметры:
    - **skip**: Количество записей для пропуска (по умолчанию 0)
    - **limit**: Максимальное количество возвращаемых записей (по умолчанию 100)
    
    Возвращает список задач с их статусом и временем выполнения.
    """
    return ScheduledTaskService.get_scheduled_tasks(db, skip=skip, limit=limit)

@router.get(
    "/scheduled-tasks/{task_id}",
    response_model=ScheduledTask,
    summary="Получить запланированную задачу по ID",
    description="Возвращает запланированную задачу по указанному идентификатору.",
    response_description="Найденная запланированная задача",
    responses={
        404: {"description": "Запланированная задача не найдена"}
    }
)
def get_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """
    Получает запланированную задачу по ее уникальному идентификатору.
    
    Параметры:
    - **task_id**: ID задачи (обязательно)
    
    Возвращает объект задачи или 404 ошибку, если задача не найдена.
    """
    task = ScheduledTaskService.get_scheduled_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запланированная задача не найдена"
        )
    return task

@router.put(
    "/scheduled-tasks/{task_id}",
    response_model=ScheduledTask,
    summary="Обновить запланированную задачу",
    description="Обновляет существующую запланированную задачу по указанному ID.",
    response_description="Обновленная запланированная задача",
    responses={
        404: {"description": "Запланированная задача не найдена"}
    }
)
def update_scheduled_task(
    task_id: int, 
    task: ScheduledTaskUpdate, 
    db: Session = Depends(get_db)
):
    """
    Обновляет существующую запланированную задачу.
    
    Параметры:
    - **task_id**: ID обновляемой задачи (обязательно)
    - **scheduled_time**: Новое время выполнения задачи (опционально)
    - **status**: Новый статус задачи (опционально)
    
    Возвращает обновленный объект задачи или 404 ошибку, если задача не найдена.
    """
    updated_task = ScheduledTaskService.update_scheduled_task(db, task_id, task)
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запланированная задача не найдена"
        )
    return updated_task

@router.delete(
    "/scheduled-tasks/{task_id}",
    summary="Удалить запланированную задачу",
    description="Удаляет запланированную задачу по указанному ID.",
    response_description="Результат операции удаления",
    responses={
        200: {"description": "Задача успешно удалена"},
        404: {"description": "Задача не найдена"}
    }
)
def delete_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запланированную задачу по ее ID.
    
    Параметры:
    - **task_id**: ID удаляемой задачи (обязательно)
    
    Возвращает сообщение об успешном удалении или 404 ошибку, если задача не найдена.
    """
    success = ScheduledTaskService.delete_scheduled_task(db, task_id)
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
