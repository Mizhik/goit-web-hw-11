import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


from src.dtos.user import UserSchema
from src.entity.models import User
from src.repository.users import get_user_by_email, create_user, update_token, update_avatar


class TestAsyncUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1, username='test_user', email="example@gmail.com", password="qwerty",
                         refresh_token="refresh_token", avatar="example_url", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_contact

        result = await get_user_by_email(self.user.email, self.session)
        self.assertEqual(result, self.user)
        self.session.execute.assert_called_once()
        self.assertEqual(self.user.email, result.email)

    async def test_create_user(self):
        body = UserSchema(username='test_user', email="example@gmail.com", password="12345678")
        result = await create_user(body, self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)

    async def test_update_token(self):
        token = "new_refresh_token"
        await update_token(self.user, token, self.session)
        self.assertEqual(self.user.refresh_token, token)

    @patch('src.repository.users.get_user_by_email')
    async def test_update_avatar(self, mock_get_user_by_email):
        avatar_url = 'http/test/avatar.png'
        mock_get_user_by_email.return_value = self.user

        updated_user = await update_avatar(self.user.email, avatar_url, self.session)

        self.assertEqual(updated_user.avatar, avatar_url)
        mock_get_user_by_email.assert_called_once_with(self.user.email, self.session)