from bs4 import BeautifulSoup
from django.template.loader import render_to_string

from django.utils.translation import gettext as _

def get_alert(alert_id: str, alert_type: str, alert_message: str):
    context = {
        "alert_id": alert_id,
        "alert_type": alert_type,
        "message": alert_message
    }
    html = render_to_string("core/partial/template_alert.html", context=context)
    soup = BeautifulSoup(html, 'html.parser')

    return soup.find('div')