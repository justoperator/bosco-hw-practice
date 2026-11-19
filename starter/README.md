# Стартовий код ПР №2.17.3

Окремого стартера ця робота **не має** — вона продовжує ПР №2.16.3.

## Якщо ПР №2.16.3 збереглась

Працюйте у тому самому проєкті. Моделі, адмінка і сид не змінюються, нові
файли додаються поряд із тими, що ви вже написали:

```
scoreboard/
├── models.py          ← не чіпаємо
├── serializers.py     ← доробляємо
├── views.py           ← доробляємо
├── urls.py            ← не змінюється
├── filters.py         ← новий
├── pagination.py      ← новий
└── renderers.py       ← новий
```

## Якщо проєкту немає

Візьміть стартер ПР №2.16.3 (`assignments/cw-2.16.3/student-files.zip`) і
спершу доведіть її контракт до зеленого — інакше немає що розширювати:

```bash
unzip student-files.zip -d pr-2.16.3
cp -r pr-2.16.3/starter/scoreboard/ /шлях/до/проєкту/
python manage.py makemigrations scoreboard && python manage.py migrate
python manage.py seed_tournament
```

## Нові пакети

```bash
pip install django-filter django-cors-headers
```

Що додати в `settings.py` — `settings-snippet.py` поряд із цим файлом.
