# Yatube
Cоциальная сеть, где можно публиковать посты, авторизоваться, ставить лайки и писать комментарии под постами, создавать и администрировать группы.

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/v-2841/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Для работы timezone потребуется [база данных](https://lite.ip2location.com/database/db11-ip-country-region-city-latitude-longitude-zipcode-timezone), которую надо поместить в yatube/ip_db.

## Стек технологий:
-   Python
-   Django
-   SQLite3
-   Pytest
