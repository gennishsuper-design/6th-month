# Blog REST API

REST API для блога на Django и Django REST Framework.

## Возможности

- посты с автором, датами, публикацией и пагинацией;
- гостям доступны только опубликованные посты;
- создание постов и комментариев только для авторизованных пользователей;
- изменять и удалять посты/комментарии может только их автор;
- новые комментарии создаются как неподтвержденные;
- автоматическая OpenAPI-документация в Swagger и ReDoc;
- PostgreSQL используется по умолчанию, параметры подключения берутся из `.env`.

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API будет доступен по адресу `http://127.0.0.1:8000/`.

### Запуск всего проекта в Docker

Создайте `.env` на основе `.env.example` и задайте локальные значения. Затем выполните:

```bash
docker compose up --build -d
docker compose ps
```

Compose запускает Django, PostgreSQL, Redis, Celery worker и Celery beat. Миграции
выполняются отдельным одноразовым сервисом до запуска приложения и Celery.
Логи сервисов доступны через `docker compose logs -f`; остановить контейнеры,
сохранив данные PostgreSQL, можно командой `docker compose down`.

Для скриншота всех работающих контейнеров выполните `docker compose ps` и сделайте
снимок экрана терминала средствами рабочего стола.

Для запуска на SQLite добавьте в `.env` строку `USE_SQLITE=true`.
Для обычного запуска PostgreSQL оставьте эту настройку выключенной или удалите ее.
Если SQLite база была создана до перехода на кастомную модель пользователя, сначала
сделайте резервную копию данных и укажите отдельный файл, например
`SQLITE_NAME=db-custom-user.sqlite3`: Django не поддерживает простую замену стандартной
модели пользователя после применения начальных миграций. Старый файл при этом сохранится.

## Аутентификация

Для регистрации отправьте email, пароль, имя и фамилию, при необходимости номер телефона и дату рождения. После регистрации аккаунт будет неактивен, а одноразовый код подтверждения придёт на email. Код хранится в Redis 5 минут и удаляется после успешного подтверждения:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com", "password":"your-password", "first_name":"Ada", "last_name":"Lovelace", "birthdate":"2000-01-31"}'
```

Подтвердите аккаунт запросом `POST /api/v1/auth/confirm/`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/confirm/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com", "code":"123456"}'
```

При локальном запуске с console email backend код отображается в выводе сервера; в Docker его можно посмотреть командой `docker compose logs -f web`.

Вход по email и паролю доступен через `POST /api/v1/auth/login/`. Ответ содержит JWT `access` и `refresh`; claim `birthdate` включён в оба токена.
Старый адрес `/api/v1/auth/token/` оставлен как alias входа. Передавайте access-токен
в защищенных запросах заголовком `Authorization: Bearer <access-token>`.

### Вход через Google OAuth 2.0

В Google Cloud Console создайте проект, настройте OAuth consent screen и создайте OAuth Client ID типа **Web application**. В Authorized redirect URIs добавьте точный адрес callback:
`http://127.0.0.1:8000/api/v1/auth/google/callback/`.

Перед запуском задайте значения из Google Cloud Console в `.env`:

```env
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/api/v1/auth/google/callback/
```

Откройте `GET /api/v1/auth/google/`, возьмите `authorization_url` из ответа и перенаправьте туда браузер. После согласия Google вернет браузер на callback; сервер проверит OAuth `state`, обменяет authorization code на access token и получит профиль от Google. Для нового пользователя сохраняются `given_name`, `family_name`, `registration_source=google`; аккаунт активируется и `last_login` устанавливается при каждом успешном входе. Google-пользователю задается unusable password. Callback возвращает JWT `access` и `refresh` в JSON.

Локальная регистрация сохраняет `registration_source=local`. Доступные значения поля: `local`, `google`, `facebook`.

Номер телефона необязателен для обычного аккаунта. Для суперпользователя он обязателен
и должен иметь код страны 996, например `+996555123456`.

Чтобы создать продукт, дата рождения из JWT должна показывать возраст не менее 18 лет.
Без даты рождения API вернёт сообщение `Укажите дату рождения, чтобы создать продукт.`

## Эндпоинты

- `GET /api/v1/posts/` - список опубликованных постов для гостя, список всех постов для пользователя;
- `POST /api/v1/auth/register/` - регистрация с email и паролем;
- `POST /api/v1/auth/confirm/` - подтверждение регистрации одноразовым кодом;
- `POST /api/v1/auth/login/` - вход по email и паролю и получение токена;
- `GET /api/v1/products/` - список продуктов;
- `POST /api/v1/products/` - создать продукт (для обычного авторизованного пользователя);
- `GET/PATCH/DELETE /api/v1/products/{id}/` - просмотреть, изменить или удалить продукт;
- `POST /api/v1/posts/` - создать пост;
- `GET /api/v1/posts/{id}/` - получить пост;
- `PUT/PATCH/DELETE /api/v1/posts/{id}/` - изменить или удалить свой пост;
- `GET /api/v1/posts/{id}/comments/` - список комментариев;
- `POST /api/v1/posts/{id}/comments/` - добавить комментарий;
- `GET /api/v1/posts/{id}/comments/{comment_id}/` - получить комментарий;
- `PUT/PATCH/DELETE /api/v1/posts/{id}/comments/{comment_id}/` - изменить или удалить свой комментарий.

Список постов и комментариев использует стандартную DRF-пагинацию с параметрами `page` и `page_size`.
Пользователь со `is_staff=True` может просматривать, изменять и удалять любые продукты, но не может создавать их. Обычный пользователь может создавать продукты и управлять только своими.

## Документация

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

## Тесты

```bash
python manage.py test
```
