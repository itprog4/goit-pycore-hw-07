import calendar
import re
from collections import UserDict
from datetime import datetime, date, timedelta
from functools import wraps
from typing import Any, Self

PHONE_PATTERN = re.compile(r'^\d+$')


class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value: str):
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError('Invalid data type. Expected type is string only.')
        try:
            _ = datetime.strptime(value, '%d.%m.%Y')
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Phone(Field):
    def __init__(self, value: str):
        match = re.match(r'^\d{10}$', value)
        if not match:
            raise ValueError("Invalid phone number format")
        super().__init__(value)

    def __eq__(self, other: Any):
        if isinstance(other, Phone):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        else:
            return False

class Record:
    def __init__(self, _name: str) -> None:
        self.name = Name(_name)
        self.phones = list[Phone]()
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> Self:
        if Phone(phone) in self.phones:
            return self
        self.phones.append(Phone(phone))
        return self

    def edit_phone(self, old_phone: str, new_phone: str) -> Self:
        counter: int = 0
        while counter < len(self.phones):
            if self.phones[counter].value == old_phone:
                self.phones[counter] = Phone(new_phone)
                return self
            counter += 1
        return self

    def find_phone(self, phone: str) -> Phone | None:
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def remove_phone(self, phone: str) -> Self:
        counter: int = 0
        while counter < len(self.phones):
            if self.phones[counter].value == phone:
                del self.phones[counter]
                return self
            counter += 1
        return self

    def add_birthday(self, birthday: str) -> Self:
        if self.birthday is not None:
            raise ValueError("Birthday already exists")
        self.birthday = Birthday(birthday)
        return self

    def __str__(self) -> str:
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

class AddressBook(UserDict):
    def __init__(self):
        super().__init__()

    def add_record(self, _record: Record):
        self.data[_record.name.value] = _record

    def find(self, _name: str) -> Record | None:
        return self.data.get(_name)

    def delete(self, _name: str):
        if _name in self.data:
            del self.data[_name]

    def get_upcoming_birthdays(self) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        now: date = date.today()
        seven_days_later: date = date.today() + timedelta(days=7)

        for user in self.data.values():
            users_birthday: date = datetime.strptime(user["birthday"], "%Y.%m.%d").date()
            coming_birthday: date = date(
                year=seven_days_later.year,
                month=users_birthday.month,
                day=users_birthday.day
            ) if not (users_birthday.month == 2 and users_birthday.day == 29 and calendar.isleap(
                seven_days_later.year)) else date(
                # leap year case
                year=seven_days_later.year,
                month=users_birthday.month,
                day=users_birthday.day - 1 if not calendar.isleap(seven_days_later.year) else users_birthday.day
            )

            if now <= coming_birthday < seven_days_later:
                if coming_birthday.weekday() in [5, 6]:
                    birthday_celebration_day = coming_birthday + timedelta(
                        days=1 if coming_birthday.weekday() == 6 else 2,
                    )
                else:
                    birthday_celebration_day = coming_birthday

                result.append(
                    {
                        'name': user["name"],
                        'congratulation_date': birthday_celebration_day.strftime("%Y.%m.%d"),
                    }
                )

        return result

def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError, KeyError) as e:
            return str(e)

    return inner

@input_error
def parse_input(user_input: str) -> tuple[str, list[str]]:
    parts = user_input.strip().split()
    if len(parts) == 0:
        return '', []
    return parts[0].lower(), parts[1:]

@input_error
def add_contact(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 2 or not PHONE_PATTERN.match(args[1]):
        raise ValueError('Invalid input format. Please use "add <name> <phone>".')
    name, phone = args
    if name in contacts:
        raise KeyError('Contact {name} already exists. Use "change <name> <phone>" to update the phone number.')
    contacts.add_record(
        Record(name)
            .add_phone(phone)
    )
    return f'Contact {name} with phone {phone} added successfully.'

@input_error
def change_contact(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 3 or not PHONE_PATTERN.match(args[1]):
        raise ValueError('Invalid input format. Please use "change <name> <phone>".')
    name, old_phone, new_phone = args
    if name not in contacts:
        raise KeyError(f'Contact {name} does not exist. Use "add <name> <phone>" to add a new contact.')
    contacts[name].edit_phone(old_phone, new_phone)
    return f'Contact {name} with phone {new_phone} updated successfully.'

@input_error
def show_phone(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 1:
        raise ValueError('Invalid input format. Please use "phone <name>".')
    name = args[0]
    if name not in contacts:
        raise KeyError(f'Contact {name} does not exist. Use "add <name> <phone>" to add a new contact.')
    return f'{contacts[name]}'

@input_error
def show_all(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 0:
        raise ValueError('Invalid input format. Please use "all".')
    if not contacts:
        raise KeyError('No contacts found.')
    return '\n'.join(f'{name}: {item}' for name, item in contacts.items())

@input_error
def hello(args: list[str], contacts: AddressBook) -> str:
    return 'How can I help you?'

@input_error
def add_birthday(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 2:
        raise ValueError('Invalid input format. Please use "add-birthday <name> <birthday>".')
    name, birthday = args
    if name not in contacts:
        raise KeyError(f'Contact {name} does not exist. Use "add <name> <phone>" to add a new contact.')
    contacts[name].birthday = birthday
    return f'Birthday for {name} updated successfully.'

@input_error
def show_birthday(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 1:
        raise ValueError('Invalid input format. Please use "show-birthday <name>".')
    name = args[0]
    if name not in contacts:
        raise KeyError(f'Contact {name} does not exist.')
    birthday = contacts[name].birthday
    if birthday is not None:
        return f'Birthday for {name}: {birthday}'
    else:
        return f'Birthday for {name} is not set.'

@input_error
def birthdays(args: list[str], contacts: AddressBook) -> str:
    if len(args) != 0:
        raise ValueError('Invalid input format. Please use "birthdays".')
    birthdays_list = []
    for name, contact in contacts.items():
        birthday = contact.birthday
        if birthday is not None:
            birthdays_list.append(f'{name}: {birthday}')
    if birthdays_list:
        return '\n'.join(birthdays_list)
    else:
        return 'No birthdays set for any contacts.'

HANDLERS = {
    'hello': hello,
    'add': add_contact,
    'change': change_contact,
    'phone': show_phone,
    'all': show_all,
    'add-birthday': add_birthday,
    'show-birthday': show_birthday,
    'birthdays': birthdays
}

def main() -> None:
    contacts: AddressBook = AddressBook()
    print('Welcome to the assistant bot!')
    while True:
        try:
            user_input = input('Enter a command: ')
        except SystemExit, KeyboardInterrupt, EOFError:
            print('\nGood bye!')
            break

        command, args = parse_input(user_input)
        if command in ('close', 'exit'):
            print('Good bye!')
            break
        if not command:
            continue
        handler = HANDLERS.get(command)
        if handler is None:
            print('Invalid command. Please try again.')
        else:
            print(handler(args, contacts))

if __name__ == "__main__":
    main()