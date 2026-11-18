"""
Shaharlar va tumanlarni PostgreSQL bazasiga qo'shadi.
build.sh orqali avtomatik ishlatiladi.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import City, District

CITIES_DATA = {
    "Toshkent": [
        "Yunusobod", "Chilonzor", "Yakkasaroy", "Mirzo Ulug'bek",
        "Shayxontohur", "Uchtepa", "Olmazor", "Bektemir",
        "Sergeli", "Yangihayot", "Mirobod", "Hamza"
    ],
    "Samarqand": [
        "Samarqand shahri", "Urgut", "Bulungur", "Kattaqo'rg'on",
        "Narpay", "Paxtachi", "Payariq", "Pastdarg'om",
    ],
    "Buxoro": [
        "Buxoro shahri", "G'ijduvon", "Kogon", "Qorovulbozor",
        "Romitan", "Shofirkon", "Vobkent",
    ],
    "Andijon": [
        "Andijon shahri", "Asaka", "Baliqchi", "Bo'z",
        "Jalaquduq", "Marhamat", "Oltinkul", "Paxtaobod",
        "Qo'rg'ontepa", "Shahrixon", "Xo'jaobod",
    ],
    "Namangan": [
        "Namangan shahri", "Chortoq", "Chust", "Kosonsoy",
        "Mingbuloq", "Norin", "Pop", "To'raqo'rg'on",
        "Uchqo'rg'on", "Uychi", "Yangiqo'rg'on",
    ],
    "Farg'ona": [
        "Farg'ona shahri", "Beshariq", "Bog'dod", "Buvayda",
        "Dang'ara", "Furqat", "Qo'shtepa", "Quva",
        "Rishton", "So'x", "Toshloq", "Uchko'prik", "Yozyovon",
    ],
    "Qashqadaryo": [
        "Qarshi", "Chiroqchi", "Dehqonobod", "G'uzor",
        "Kamashi", "Kasbi", "Kitob", "Koson",
        "Mirishkor", "Muborak", "Nishon", "Shahrisabz",
    ],
    "Surxondaryo": [
        "Termiz", "Angor", "Bandixon", "Boysun",
        "Denov", "Jarqo'rg'on", "Qiziriq", "Qumqo'rg'on",
        "Muzrabot", "Oltinsoy", "Sariosiyo", "Sherobod", "Uzun",
    ],
    "Xorazm": [
        "Urganch", "Bog'ot", "Gurlan", "Xonqa",
        "Xiva", "Hazorasp", "Shovot", "Tuproqqal'a", "Yangiariq", "Yangibozor",
    ],
    "Jizzax": [
        "Jizzax shahri", "Arnasoy", "Baxmal", "Do'stlik",
        "Forish", "G'allaorol", "Mirzacho'l", "Paxtakor",
        "Sharof Rashidov", "Yangiobod", "Zafarobod",
    ],
    "Sirdaryo": [
        "Guliston", "Boyovut", "Mirzaobod", "Oqoltin",
        "Sardoba", "Sayxunobod", "Shirin", "Xovos",
    ],
    "Navoiy": [
        "Navoiy shahri", "Karmana", "Konimex", "Navbahor",
        "Nurota", "Tomdi", "Uchquduq", "Xatirchi", "Zarafshon",
    ],
    "Qoraqalpog'iston": [
        "Nukus", "Amudaryo", "Beruniy", "Chimboy",
        "Ellikkala", "Kegeyli", "Mo'ynoq", "Nukus tumani",
        "Qanliko'l", "Qo'ng'irot", "Shumanay", "Taxtako'pir",
        "To'rtko'l", "Xo'jayli",
    ],
}

created_cities = 0
created_districts = 0

for city_name, districts in CITIES_DATA.items():
    city, city_created = City.objects.get_or_create(name=city_name)
    if city_created:
        created_cities += 1

    for district_name in districts:
        _, dist_created = District.objects.get_or_create(city=city, name=district_name)
        if dist_created:
            created_districts += 1

print(f">>> Shaharlar: {created_cities} ta yangi, {created_districts} ta tuman qo'shildi.")
print(f">>> Jami DB da: {City.objects.count()} shahar, {District.objects.count()} tuman.")
