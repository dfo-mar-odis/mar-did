import json
import logging

from asgiref.sync import async_to_sync

from bs4 import BeautifulSoup
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger('mardid')

class LoggerConsumer(WebsocketConsumer, logging.Handler):

    GROUP_NAME = "logger"

    def connect(self):
        logger.info(self.channel_name)

        async_to_sync(self.channel_layer.group_add)(
            self.GROUP_NAME, self.channel_name
        )
        self.accept()
        logger_to_listen_to = self.scope['url_route']['kwargs']['logger']
        logger.info(f"connecting logger: {logger_to_listen_to}")
        logging.getLogger(f'{logger_to_listen_to}').addHandler(self)

    def disconnect(self, code):
        logger_to_listen_to = self.scope['url_route']['kwargs']['logger']
        logging.getLogger(f'{logger_to_listen_to}').removeHandler(self)
        async_to_sync(self.channel_layer.group_discard)(
            self.GROUP_NAME, self.channel_name
        )

    def process_render_queue(self, component_id, event) -> None:
        soup = BeautifulSoup(f'<div id="{component_id}">{event["message"]}</div>', 'html.parser')
        progress_bar = soup.new_tag("div")
        progress_bar.attrs = {
            'class': "progress-bar progress-bar-striped progress-bar-animated",
            'role': "progressbar",
        }

        progress_bar_div = soup.new_tag("div", attrs={'class': "progress", 'id': 'progress_bar'})
        progress_bar_div.append(progress_bar)

        if event['queue']:
            progress_bar.attrs['style'] = f'width: {event["queue"]}%'
            progress_bar.string = f"{event['queue']}%"
            progress_bar_div.attrs['aria-valuenow'] = str(event["queue"])
            progress_bar_div.attrs['aria-valuemin'] = "0"
            progress_bar_div.attrs['aria-valuemax'] = "100"
        else:
            progress_bar.attrs['style'] = f'width: 100%'
            progress_bar.string = _("Working")

        soup.append(progress_bar_div)
        self.send(soup)

    def emit(self, record: logging.LogRecord) -> None:
        component = self.scope['url_route']['kwargs']['component']

        if len(record.args) > 0:
            event = {
                'message': record.getMessage(),
                'queue': int((record.args[0]/record.args[1])*100)
            }
            self.process_render_queue(component, event)
        else:
            html = BeautifulSoup(f'<div id="{component}">{record.getMessage()}</div>', 'html.parser')
            self.send(html)

    def __init__(self):
        logging.Handler.__init__(self, level=logging.INFO)
        WebsocketConsumer.__init__(self)
