import re
import json

# read the file
with open("raw.txt", "r", encoding="utf-8") as file:
    text = file.read()

# extract all prices
prices = re.findall(r"\d[\d\s]*,\d{2}", text)

# extract product names
products = re.findall(r"\d+\.\n(.+)", text)

# find total amount
total_match = re.search(r"ИТОГО:\n([\d\s]+,\d{2})", text)
total = total_match.group(1) if total_match else None

# extract date and time
datetime_match = re.search(r"\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}:\d{2}", text)
datetime = datetime_match.group() if datetime_match else None

# find payment method
payment_match = re.search(r"Банковская карта|Наличные", text)
payment = payment_match.group() if payment_match else None

# structured output
data = {
    "products": products,
    "prices": prices,
    "total": total,
    "datetime": datetime,
    "payment_method": payment
}

# print result in JSON format
print(json.dumps(data, indent=4, ensure_ascii=False))