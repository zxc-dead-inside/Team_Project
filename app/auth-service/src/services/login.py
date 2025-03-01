class LoginService():
    def __init__(self, db_session, redis):
        self.db_session = db_session
        self.redis = redis
