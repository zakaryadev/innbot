# 🤖 INN Bot — Tashkilotlarni Qidirish Boti

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**O'zbekiston tashkilotlarini INN raqami, nomi yoki tartib raqami bo'yicha qidiruvchi Telegram bot.**

</div>

---

## ✨ Imkoniyatlar

| Qidiruv turi | Misol |
|---|---|
| 🔢 **INN raqami bo'yicha** | `123456789` |
| 🏢 **Tashkilot nomi bo'yicha** | `Maktab` |
| 🆔 **Tartib raqami bo'yicha** | `42` |

- ⚡ **Tezkor qidiruv** — SQLite indekslari bilan optimallashtirilgan
- 🔤 **Ko'p tilli qo'llab-quvvatlash** — Kirill va Lotin alifbosi
- 🐳 **Docker bilan ishlaydi** — bir buyruq bilan ishga tushirish
- 📊 **Excel-dan avtomatik import** — `.xlsx` fayllardan ma'lumot yuklash

---

## 📁 Loyiha tuzilishi

```
INN/
├── bot.py                          # Asosiy bot mantig'i (handler'lar)
├── database.py                     # SQLite qidiruv funksiyalari
├── db_setup_excel.py               # Excel → SQLite import skripti
├── config.py                       # Konfiguratsiya (env, yo'llar)
├── entrypoint.sh                   # Docker ishga tushirish skripti
├── Dockerfile                      # Docker image
├── docker-compose.yml              # Docker Compose konfiguratsiyasi
├── requirements.txt                # Python bog'liqliklar
├── .env.example                    # Muhit o'zgaruvchilar namunasi
└── *.xlsx                          # Tashkilotlar ma'lumot bazasi
```

---

## 🚀 Ishga Tushirish

### Docker orqali (tavsiya etiladi)

```bash
# 1. Loyihani klonlash
git clone <repo-url>
cd INN

# 2. Muhit o'zgaruvchilarini sozlash
cp .env.example .env
# .env faylini tahrirlang va BOT_TOKEN ni kiriting

# 3. Ishga tushirish
docker compose up -d

# 4. Loglarni ko'rish
docker compose logs -f
```

### Mahalliy ishga tushirish

```bash
# 1. Virtual muhit yaratish
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# 2. Bog'liqliklarni o'rnatish
pip install -r requirements.txt

# 3. .env faylini sozlash
cp .env.example .env
# BOT_TOKEN ni kiriting

# 4. Ma'lumot bazasini to'ldirish
python db_setup_excel.py

# 5. Botni ishga tushirish
python bot.py
```

---

## ⚙️ Konfiguratsiya

`.env` faylini yarating (`.env.example` asosida):

```env
BOT_TOKEN=your_telegram_bot_token_here
```

> **Token olish:** [@BotFather](https://t.me/BotFather) → `/newbot` → tokenni nusxalash

---

## 🗄️ Ma'lumot Bazasi

Bot `.xlsx` formatdagi Excel fayllardan ma'lumot import qiladi.

**Fayl ustunlari:**

| Ustun | Tavsif |
|---|---|
| `№` | Tartib raqami |
| `Tashkilot` | Tashkilot nomi |
| `INN` | Soliq to'lovchi identifikatsiya raqami |
| `Telefon` | Telefon raqami (ixtiyoriy) |

> Excel fayllarni loyiha papkasiga joylashtirsangiz, Docker ishga tushirilganda avtomatik import bo'ladi.

---

## 🐳 Docker Tafsilotlari

```yaml
# docker-compose.yml
services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
```

- 🔄 `restart: unless-stopped` — bot xatolikdan keyin avtomatik qayta ishga tushadi
- 📦 Har bir ishga tushirishda `db_setup_excel.py` avtomatik chaqiriladi

---

## 📦 Texnologiyalar

- **[aiogram 3.x](https://docs.aiogram.dev/)** — Telegram Bot API freymvorki
- **[pandas](https://pandas.pydata.org/)** — Excel fayllarni o'qish
- **[openpyxl](https://openpyxl.readthedocs.io/)** — `.xlsx` format qo'llab-quvvatlovchi
- **SQLite** — yengil, fayl-asosli ma'lumot bazasi
- **Docker** — konteynerizatsiya

---

## 🤝 Hissa Qo'shish

1. Loyihani fork qiling
2. Yangi branch yarating: `git checkout -b feature/yangi-xususiyat`
3. O'zgarishlarni commit qiling: `git commit -m "feat: yangi xususiyat"`
4. Push qiling: `git push origin feature/yangi-xususiyat`
5. Pull Request oching

---

<div align="center">

Made with ❤️ in Uzbekistan

</div>
