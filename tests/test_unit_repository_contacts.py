import unittest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.dtos.contact import ContactSchema

from src.entity.models import User, Contact
from src.repository.contacts import get_contacts, get_contact, get_upcoming_birthdays, create_contact, update_contact, \
    delete_contact, search_contacts


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1, username='test_user', password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(id=1, first_name="Vlad", last_name="Mizhik", email="example@gmail.com", phone="+380682782854",
                    date_of_birth=date(2004, 10, 17), user=self.user),
            Contact(id=1, first_name="Oleg", last_name="Olegov", email="example123@gmail.com", phone="+380682782123",
                    date_of_birth=date(2004, 12, 13), user=self.user)]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.user, self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact(self):
        contact = Contact(id=1, first_name="Vlad", last_name="Mizhik", email="example@gmail.com",
                          phone="+380682782854",
                          date_of_birth=date(2004, 10, 17), user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await get_contact(self.user.id, self.user, self.session)
        self.assertEqual(result, contact)

    async def test_create_contact(self):
        body = ContactSchema(first_name="Vlad", last_name="Mizhik", email="example@gmail.com", phone="+380682782854",
                             date_of_birth=date(2004, 10, 17))
        result = await create_contact(body, self.user, self.session)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.date_of_birth, body.date_of_birth)

    async def test_update_contact(self):
        body = ContactSchema(first_name="Vlad", last_name="Mizhik", email="example@gmail.com", phone="+380682782854",
                             date_of_birth=date(2004, 10, 17))
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=1, first_name="Vlad", last_name="Mizhik",
                                                                 email="example@gmail.com",
                                                                 phone="+380682782854",
                                                                 date_of_birth=date(2004, 10, 17))
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, self.user, body, self.session)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.date_of_birth, body.date_of_birth)

    async def test_delete_contact(self):
        contact = Contact(id=1, first_name="Vlad", last_name="Mizhik", email="example@gmail.com",
                          phone="+380682782854",
                          date_of_birth=date(2004, 10, 17), user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await delete_contact(1, self.user, self.session)
        self.assertIsInstance(result, Contact)

    async def test_search_contacts(self):
        filter = {'first_name': 'Vlad',
                  'last_name': 'Mizhik',
                  'email': 'example@gmail.com'}
        limit = 10
        offset = 0
        contacts = [Contact(id=1, first_name="Vlad", last_name="Mizhik", email="example@gmail.com",
                            phone="+380682782854",
                            date_of_birth=date(2004, 10, 17), user=self.user),
                    Contact(id=2, first_name="Vlad", last_name="Mezhik", email="example123@gmail.com",
                            phone="+380682712854",
                            date_of_birth=date(2003, 12, 11), user=self.user)
                    ]

        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await search_contacts(filter, limit, offset, self.user, self.session)
        self.assertEqual(result, contacts)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].first_name, contacts[0].first_name)
        self.assertEqual(result[0].last_name, contacts[0].last_name)
        self.assertEqual(result[0].email, contacts[0].email)
        self.assertEqual(result[1].first_name, contacts[1].first_name)

    async def test_get_upcoming_birthdays(self):
        contacts = [
            Contact(id=1, first_name="Vlad", last_name="Mizhik", email="example@gmail.com",
                    phone="+380682782854", date_of_birth=date(2004, 10, 17), user=self.user),
            Contact(id=2, first_name="Oleg", last_name="Mezhik", email="example123@gmail.com",
                    phone="+380682712854", date_of_birth=date(2003, 6, 30), user=self.user)
        ]

        with patch('src.repository.contacts.datetime') as mock_datetime:
            mock_datetime.today.return_value.date.return_value = date(year=2024, month=6, day=29)
            mock_datetime.next_week.return_value.date.return_value = date(year=2024, month=7, day=6)

            mocked_result = MagicMock()
            mocked_result.scalars.return_value.all.return_value = [contacts[1]]
            self.session.execute.return_value = mocked_result

            result = await get_upcoming_birthdays(self.session, self.user)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].first_name, contacts[1].first_name)
            self.assertEqual(result[0].last_name, contacts[1].last_name)
            self.assertEqual(result[0].email, contacts[1].email)

            self.assertNotIn(contacts[0], result)
