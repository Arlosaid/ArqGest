import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Add /app/arc_manager to sys.path so we can import apps
sys.path.append('/app/arc_manager')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.plans.models import Subscription

now = timezone.now()
five_days_from_now = now + timedelta(days=5)

print(f"Current time: {now}")
print(f"Five days from now: {five_days_from_now}")

subscriptions = Subscription.objects.all()
print(f"Total subscriptions: {subscriptions.count()}")

for sub in subscriptions:
    is_expiring = sub.end_date <= five_days_from_now
    is_active_status = sub.subscription_status in ['trial_active', 'basic_active']
    
    print(f"ID: {sub.id}, Org: {sub.organization.name}, Status: {sub.subscription_status}, End Date: {sub.end_date}")
    print(f"  - Expiring (<= 5 days): {is_expiring}")
    print(f"  - Active Status: {is_active_status}")
    print(f"  - Included in count: {is_expiring and is_active_status}")

expiring_count = Subscription.objects.filter(
    end_date__lte=five_days_from_now,
    subscription_status__in=['trial_active', 'basic_active']
).count()

print(f"Expiring soon count: {expiring_count}")
