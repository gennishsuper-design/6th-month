from datetime import date

from django.utils.dateparse import parse_date
from django.utils.timezone import localdate
from rest_framework.exceptions import ValidationError


def validate_product_creator_age(request):
    token = request.auth
    try:
        birthdate_claim = token['birthdate'] if token is not None else None
    except (KeyError, TypeError):
        birthdate_claim = None

    birthdate = (
        birthdate_claim
        if isinstance(birthdate_claim, date)
        else parse_date(birthdate_claim) if isinstance(birthdate_claim, str) else None
    )
    if birthdate is None:
        raise ValidationError('Укажите дату рождения, чтобы создать продукт.')

    today = localdate()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    if age < 18:
        raise ValidationError('Вам должно быть 18 лет, чтобы создать продукт.')