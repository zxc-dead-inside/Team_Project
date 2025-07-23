import grpc
from concurrent import futures
import time

import user_pb2
import user_pb2_grpc

from app.auth_service.src.db.repositories.user_repository import UserRepository
from app.auth_service.src.core.config import get_settings
from app.auth_service.src.db.database import get_database


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    def GetUserInfo(self, request, context):
        settings = get_settings()
        db = get_database(str(settings.database_url))
        user_repo = UserRepository(db.session)
        user = user_repo.get_by_id(request.user_id)

        if user:
            return user_pb2.UserInfo(
                id=str(user.id),
                username=user.username,
                phone_number=user.phone_number,
                first_name=user.first_name,
                last_name=user.last_name,
                birth_date=str(user.birth_date),
                email=user.email,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=str(user.created_at),
                updated_at=str(user.updated_at),
            )
        else:
            context.set_details(f'User with ID {request.user_id} not found.')
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return user_pb2.UserInfo()


# Запуск gRPC сервера
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
