# Create a program that counts the days from a given date to the current date.

from datetime import datetime

def days_from_date(date):
    date_format = "%Y-%m-%d"
    date = datetime.strptime(date, date_format)
    current_date = datetime.strptime("2025-03-10", date_format)
    days = (current_date - date).days
    return days

date = input("Enter a date (YYYY-MM-DD): ")
print("Days from date: ", days_from_date(date))
print("Days mod 3: ", days_from_date(date) % 3)