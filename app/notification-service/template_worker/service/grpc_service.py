import grpc

from template_worker import user_pb2_grpc, user_pb2


async def get_user_info_rpc(user_id: str):
    channel = grpc.aio.insecure_channel('localhost:50051')
    stub = user_pb2_grpc.UserServiceStub(channel)

    request = user_pb2.UserRequest(user_id=user_id)

    response = await stub.GetUserInfo(request)

    await channel.close()

    user_info = {
        "id": response.id,
        "username": response.username,
        "phone_number": response.phone_number,
        "first_name": response.first_name,
        "last_name": response.last_name,
        "birth_date": response.birth_date,
        "email": response.email,
        "is_active": response.is_active,
        "is_superuser": response.is_superuser,
        "created_at": response.created_at,
        "updated_at": response.updated_at
    }

    return user_info
