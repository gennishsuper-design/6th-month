from celery import shared_task
from django.core.mail import send_mail

from common.redis_store import clear_product_cache
from product.models import Product


@shared_task(name='common.tasks.send_welcome_email')
def send_welcome_email(email_address: str, username: str = 'friend') -> str:
    subject = 'Welcome to Shop API'
    message = f'Hello {username}, thank you for registering in our shop!'
    send_mail(subject, message, None, [email_address], fail_silently=False)
    return f'Email sent to {email_address}'


@shared_task(name='common.tasks.clear_old_products_cache')
def clear_old_products_cache() -> str:
    clear_product_cache()
    return 'Product cache cleared'


@shared_task(name='common.tasks.generate_daily_report')
def generate_daily_report() -> str:
    total_products = Product.objects.count()
    report_text = f'Daily report: {total_products} products in the catalog.'
    return report_text
