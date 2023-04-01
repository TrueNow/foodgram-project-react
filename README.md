[![foodgram_workflow](https://github.com/s3r3ga/foodgram-project-react/actions/workflows/workflow.yml/badge.svg)](https://github.com/s3r3ga/foodgram-project-react/actions/workflows/workflow.yml)
# FoodGram
Сайт доступен по ссылке: [Foodgram](http://158.160.17.113)

## Описание
Проект "Продуктовый помошник" (Foodgram) предоставляет пользователям следующие возможности:
  - создание своих рецептов и управление ими
  - просмотр рецептов других пользователей
  - добавление рецептов в "Избранное" и/или в "Список покупок"
  - подписываться на других пользователей
  - скачивание списка ингредиентов для рецептов, добавленных в "Список покупок"

---

## Установка Docker (на платформе Ubuntu)
Для запуска необходимо установить Docker и Docker Compose. 
Подробнее об установке на других платформах можно узнать на [официальном сайте](https://docs.docker.com/engine/install/).

Для начала необходимо скачать и выполнить скрипт:
```bash
apt install curl
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

При необходимости удалить старые версии Docker:
```bash
apt remove docker docker-engine docker.io containerd runc 
```

Установить пакеты для работы через протокол https:
```bash
apt update
```
```bash
apt install \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common -y 
```

Добавить ключ GPG для подтверждения подлинности в процессе установки:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

Добавить репозиторий Docker в пакеты apt и обновить индекс пакетов:
```bash
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" 
```
```bash
apt update
```

Установить Docker(CE) и Docker Compose:
```bash
apt install docker-ce docker-compose -y
```

Проверить что  Docker работает можно командой:
```bash
systemctl status docker
```
Подробнее об установке можно узнать по [ссылке](https://docs.docker.com/engine/install/ubuntu/).

---

## База данных и переменные окружения
Проект использует базу данных PostgreSQL. Для подключения и выполненя запросов к базе данных необходимо создать и заполнить файл ".env" с переменными окружения в папке "./infra/".

Шаблон для заполнения файла ".env":
```python
DB_ENGINE=django.db.backends.postgresql
DB_NAME='db_name'
POSTGRES_USER='postgres_user'
POSTGRES_PASSWORD='postgres_password'
DB_HOST='db'
DB_PORT=5432
SECRET_KEY='Здесь указать секретный ключ'
ALLOWED_HOSTS='Здесь указать имя или IP хоста'
```
---

## Команды для запуска

Необходимо склонировать проект. Cоздать и активировать виртуальное окружение:
```bash
python -m venv venv
```
```bash
Linux: source venv/bin/activate
Windows: source venv/Scripts/activate
```

И установить зависимости из файла requirements.txt:
```bash
python3 -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```

Далее необходимо собрать образы для фронтенда и бэкенда.  
Из папки "./infra/" выполнить команду:
```bash
docker-compose up
```

После успешного запуска контейнеров выполнить миграции:
```bash
docker-compose exec backend python manage.py migrate
```

Создать суперюзера (Администратора):
```bash
docker-compose exec backend python manage.py createsuperuser
```

Собрать статику:
```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

Теперь доступность проекта можно проверить по адресу [http://localhost/](http://localhost/)

---
## Заполнение базы данных

С проектом поставляются данные об ингредиентах. Заполнить базу данных ингредиентами можно выполнив следующую команду:
```bash
docker-compose exec backend python manage.py ingredients
```

Также необходимо заполнить базу данных тегами (или другими данными).  
Для этого требуется войти в [админку](http://localhost/admin/)
проекта под логином и паролем администратора (пользователя, созданного командой createsuperuser).

---
## Техническая информация

Стек технологий: Python 3, Django, DRF, Djoser, Docker, React,  PostgreSQL, nginx, gunicorn.

Веб-сервер: nginx (контейнер nginx)
Frontend фреймворк: React  
Backend фреймворк: Django  
API фреймворк: Django REST  
База данных: PostgreSQL

Веб-сервер nginx перенаправляет запросы клиентов к контейнерам frontend и backend, либо к хранилищам (volume) статики и файлов. Контейнер nginx взаимодействует с контейнером backend через gunicorn. Контейнер frontend взаимодействует с контейнером backend посредством API-запросов.

---