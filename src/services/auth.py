import pickle
import redis

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.repository import users as repository_users

from src.conf.config import config


class Auth:
    """
    Authentication and authorization service using JWT and bcrypt for password hashing.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    SECRET_KEY = config.SECRET_KEY
    ALGORITHM = config.ALGORITHM

    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies a plain password against a hashed password.

        :param plain_password: The plain text password.
        :type plain_password: str
        :param hashed_password: The hashed password.
        :type hashed_password: str
        :return: True if the passwords match, False otherwise.
        :rtype: bool
            """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Verifies a plain password against a hashed password.

        :param plain_password: The plain text password.
        :type plain_password: str
        :param hashed_password: The hashed password.
        :type hashed_password: str
        :return: True if the passwords match, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.hash(password)

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates a JWT access token.

        :param data: The data to include in the token payload.
        :type data: dict
        :param expires_delta: The token expiry time in seconds. Defaults to 15 minutes if not provided.
        :type expires_delta: Optional[float]
        :return: The encoded JWT access token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.now(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates a JWT refresh token.

        :param data: The data to include in the token payload.
        :type data: dict
        :param expires_delta: The token expiry time in seconds. Defaults to 7 days if not provided.
        :type expires_delta: Optional[float]
        :return: The encoded JWT refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.now(), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decodes a JWT refresh token.

       :param refresh_token: The JWT refresh token.
       :type refresh_token: str
       :return: The email extracted from the token payload.
       :rtype: str
       :raises HTTPException: If the token is invalid or has an incorrect scope.
       """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ):
        """
        Retrieves the current authenticated user from the JWT access token.

        :param token: The JWT access token.
        :type token: str
        :param db: The asynchronous database session.
        :type db: AsyncSession
        :return: The authenticated user.
        :rtype: User
        :raises HTTPException: If the token is invalid or the user cannot be found.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user_hash = str(email)

        user = self.cache.get(user_hash)

        if user is None:
            print("User from database")
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            print("User from cache")
            user = pickle.loads(user)
        return user

    def create_email_token(self, data: dict):
        """
        Creates a JWT token for email verification.

        :param data: The data to include in the token payload.
        :type data: dict
        :return: The encoded JWT token for email verification.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=1)
        to_encode.update({"iat": datetime.now(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        Retrieves the email address from a JWT email verification token.

         :param token: The JWT email verification token.
         :type token: str
         :return: The email address extracted from the token payload.
         :rtype: str
         :raises HTTPException: If the token is invalid.
         """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )

auth_service = Auth()
