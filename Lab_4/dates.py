from datetime import datetime, timedelta

# 1. Subtract five days from current date
today = datetime.now()
five_days_ago = today - timedelta(days=5)

print("1. Five days ago:")
print(five_days_ago)
print()

# 2. Print yesterday, today, tomorrow
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

print("2. Yesterday, Today, Tomorrow:")
print("Yesterday:", yesterday.date())
print("Today:", today.date())
print("Tomorrow:", tomorrow.date())
print()

# 3. Drop microseconds
no_microseconds = today.replace(microsecond=0)

print("3. Without microseconds:")
print(no_microseconds)
print()

# 4. Calculate difference between two dates in seconds
date1 = datetime(2025, 1, 1, 0, 0, 0)
date2 = datetime(2025, 1, 2, 0, 0, 0)

difference = date2 - date1

print("4. Difference in seconds:")
print(difference.total_seconds())