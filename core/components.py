from typing import Any

from bs4 import BeautifulSoup
from django.template.loader import render_to_string

from django.utils.translation import gettext as _

class AlertDialog(BeautifulSoup):

    def get_content_area(self) -> BeautifulSoup:
        return self.find("div", id=f"{self.alert_id}_content_area")

    def set_border(self, border: str):
        self.find('div').attrs['class'].append(f'border-{border}')

    def __init__(self, alert_id: str, alert_type: str = "info", alert_title: str = ""):
        super().__init__("", "html.parser")
        context = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "title": alert_title
        }

        html = render_to_string("core/partials/components/template_alert.html", context=context)
        self.append(BeautifulSoup(html, 'html.parser'))

        self.alert_id = alert_id
        self.alert_type = alert_type
        self.alert_title = alert_title


def get_alert(alert_id: str, alert_type: str, alert_title: str, message: Any = None):
    context = {
        "alert_id": alert_id,
        "alert_type": alert_type,
        "title": alert_title
    }
    html = render_to_string("core/partials/components/template_alert.html", context=context)
    soup = BeautifulSoup(html, 'html.parser')

    return soup.find('div')


def get_notification_alert(logger, swap_oob=False):
    context = {
        'alert_id': "notification_alert",
        'logger': logger.name,
        'alert_type': "info",
        'message': _("Loading")
    }
    if swap_oob:
        context['hx-swap-oob'] = 'true'

    html = render_to_string('core/partials/components/template_channels_notifications.html', context=context)
    notification = BeautifulSoup(html, 'html.parser')

    return notification
