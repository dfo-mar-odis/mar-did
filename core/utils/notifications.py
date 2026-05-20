from django.conf import settings
from django.core.mail import send_mail

from core.models import Datasets

import logging
logger = logging.getLogger('mardid')

def send_data_status_notification(dataset: Datasets):
    """
    Send a notification to the user when the status of their dataset changes.
    This is currently just a placeholder function that prints a message to the console.
    In a real implementation, this could be an email, an SMS, or a push notification.

    :param dataset: The dataset for which the status has changed.
    """
    message = f"Notification: The status of the dataset '{dataset.datatype.name}' has changed to '{dataset.status}'."
    logger.info(message)

    subject = f"MAR-DID Notification: {dataset.mission.name} dataset update"
    subscribers = dataset.subscribers.all()

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [sub.email for sub in subscribers], fail_silently=True)