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

Для запуска на SQLite временно добавьте в `.env` строку `USE_SQLITE=true`.
Для обычного запуска PostgreSQL оставьте эту настройку выключенной или удалите ее.

## Аутентификация

Используется DRF Token Authentication. Получите токен:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin", "password":"your-password"}'
```

Передавайте его в запросах заголовком `Authorization: Token <token>`.

## Эндпоинты

- `GET /api/v1/posts/` - список опубликованных постов для гостя, список всех постов для пользователя;
- `POST /api/v1/posts/` - создать пост;
- `GET /api/v1/posts/{id}/` - получить пост;
- `PUT/PATCH/DELETE /api/v1/posts/{id}/` - изменить или удалить свой пост;
- `GET /api/v1/posts/{id}/comments/` - список комментариев;
- `POST /api/v1/posts/{id}/comments/` - добавить комментарий;
- `GET /api/v1/posts/{id}/comments/{comment_id}/` - получить комментарий;
- `PUT/PATCH/DELETE /api/v1/posts/{id}/comments/{comment_id}/` - изменить или удалить свой комментарий.

Список постов и комментариев использует стандартную DRF-пагинацию с параметрами `page` и `page_size`.

## Документация

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

## Тесты

```bash
python manage.py test
```
