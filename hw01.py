# У користувача буде адресна книга або книга контактів. Ця книга контактів містить записи. 
# Кожен запис містить деякий набір полів.
# Користувач взаємодіє з книгою контактів, додаючи, видаляючи та редагуючи записи. 
# Також користувач повинен мати можливість шукати в книзі контактів записи за одним або кількома критеріями (полями).
# Про поля також можна сказати, що вони можуть бути обов'язковими (ім'я) та необов'язковими (телефон або email, наприклад). 
# Також записи можуть містити декілька полів одного типу (декілька телефонів, наприклад). 
# Користувач повинен мати можливість додавати / видаляти / редагувати поля в будь-якому записі.
from collections import UserDict
from datetime import datetime, date, timedelta
from operator import itemgetter
from pathlib import Path
import pickle


# Обробка помилок
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command."
        except ValueError as error:
            return str(error)

    return inner

# Базовий клас для полів запису.
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Клас для зберігання імені контакту. Обов'язкове поле.
class Name(Field):
    pass

# Клас для зберігання номера телефону. Має валідацію формату (10 цифр).
class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain 10 digits")

        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")
    
# Клас для зберігання інформації про контакт, включно з іменем та списком телефонів.
# Додавання телефонів.
# Видалення телефонів.
# Редагування телефонів.
# Пошук телефону.
# Додайте поле birthday для дня народження в клас Record. 
# Це поле має бути класу Birthday. 
# Це поле не обов'язкове, але може бути тільки одне.
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_to_remove = self.find_phone(phone)

        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError("Phone number not found.")

    def edit_phone(self, old_phone, new_phone):
        phone_to_edit = self.find_phone(old_phone)

        if phone_to_edit is None:
            raise ValueError("Phone number not found.")

        # Створення Phone перевіряє правильність нового номера
        new_phone = Phone(new_phone)
        phone_to_edit.value = new_phone.value

    def find_phone(self, phone):
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj

        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(phone.value for phone in self.phones)

        result = f"Contact name: {self.name.value}"

        if phones:
            result += f", phones: {phones}"

        if self.birthday:
            result += f", birthday: {self.birthday}"

        return result

# Клас для зберігання записів та керування ними.
# Додавання записів.
# Пошук записів за іменем.
# Видалення записів за іменем.
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError(name)

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming_birthdays = []

        for record in self.data.values():

            if record.birthday is None:
                continue

            birthday = record.birthday.value

            # День народження в поточному році
            try:
                birthday_this_year = birthday.replace(year=today.year)
            except ValueError:
                # Для 29.02 у невисокосному році
                birthday_this_year = date(today.year, 2, 28)

            # Якщо день народження вже минув, беремо наступний рік
            if birthday_this_year < today:
                try:
                    birthday_this_year = birthday.replace(
                        year=today.year + 1
                    )
                except ValueError:
                    birthday_this_year = date(today.year + 1, 2, 28)

            # Наступні 7 днів, включаючи сьогодні
            if today <= birthday_this_year <= today + timedelta(days=7):

                # Якщо день народження припадає на вихідний, вітаємо в понеділок
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:  # Saturday
                    congratulation_date += timedelta(days=2)

                elif congratulation_date.weekday() == 6:  # Sunday
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date
                })

        upcoming_birthdays.sort(
            key=itemgetter("congratulation_date")
        )

        return upcoming_birthdays

# Парсер команд
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()

    return cmd, *args

# Обробники команд
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args

    record = book.find(name)

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."

    if phone:
        record.add_phone(phone)

    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise IndexError

    name, old_phone, new_phone = args

    record = book.find(name)

    if record is None:
        raise KeyError

    record.edit_phone(old_phone, new_phone)

    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]

    record = book.find(name)

    if record is None:
        raise KeyError(name)

    if not record.phones:
        return "No phone numbers."

    return "; ".join(phone.value for phone in record.phones)


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "No contacts."

    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError

    name, birthday = args

    record = book.find(name)

    if record is None:
        raise KeyError

    record.add_birthday(birthday)

    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]

    record = book.find(name)

    if record is None:
        raise KeyError(name)

    if record.birthday is None:
        return "Birthday not set."

    return str(record.birthday)


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No upcoming birthdays."

    result = []

    for item in upcoming:
        name = item["name"]
        congratulation_date = item["congratulation_date"]

        result.append(
            f"{name}: {congratulation_date.strftime('%d.%m.%Y')}"
        )

    return "\n".join(result)


DATA_FILE = Path(__file__).parent / "addressbook.pkl"


def save_data(book):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(book, f)


def load_data():
    try:
        with open(DATA_FILE, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

    

def main():
    # book = AddressBook()
    book = load_data()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")

        if not user_input.strip():
            print("Enter the command.")
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()

"""
бот повинен підтримувати такий список команд:
add [ім'я] [телефон]: Додати або новий контакт з іменем і телефонним номером, або телефонний номер до контакту, який уже існує.
change [ім'я] [старий телефон] [новий телефон]: Змінити телефонний номер для вказаного контакту.
phone [ім'я]: Показати телефонні номери для вказаного контакту.
all: Показати всі контакти в адресній книзі.
add-birthday [ім'я] [дата народження]: Додати дату народження для вказаного контакту.
show-birthday [ім'я]: Показати дату народження для вказаного контакту.
birthdays: Показати дні народження, які відбудуться протягом наступного тижня.
hello: Отримати вітання від бота.
close або exit: Закрити програму.
"""

"""
Приклад:
Welcome to the assistant bot!
Enter a command: add Alex 0661234567
Contact added.
Enter a command: change Alex 0661234567 0661234561
Contact updated.
Enter a command: phone Alex
0661234561
Enter a command: all
Contact name: Alex, phones: 0661234561
Enter a command: add-birthday Alex 26.06.1982
Birthday added.
Enter a command: show-birthday Alex
26.06.1982
Enter a command: birthdays
No upcoming birthdays.
Enter a command: hello
How can I help you?
Enter a command: exit
Good bye!
Welcome to the assistant bot!
Enter a command: all
Contact name: Alex, phones: 0661234561, birthday: 26.06.1982
"""