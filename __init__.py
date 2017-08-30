'''
Created on Aug 30, 2017

@author: kirk
'''
from websocket import WebSocketApp
import thread
import time
import json

from mycroft.configuration import ConfigurationManager
from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

logger = getLogger(__name__)

class HassSkill(MycroftSkill):
    def __init__(self, name):
        super(HassSkill, self).__init__(name)
        config = ConfigurationManager.get()
        self.base_conf = config.get('HassSkill')
        self.ha_ws = WebSocketApp("ws://voyager.local:8123/api/websocket",
                                on_error = self.on_error,
                                on_close = self.on_close)
        self.ha_events={}
        self.ha_handlers={}
              

    def initialize(self):
        logger.info('Initializing HassSkill commons')
#        self._register_common_intents()
#        self._register_event_handlers()
        self.run()
        
        
    def _do_register(self):
        self._register_event('8001','hello',handler=self._print_data)
        
    def _register_event(self,event_id,event_type,handler):
        event={event_type:event_id}
        handler={event_type:handler}
        self.ha_events.update(event)
        self.ha_handlers.update(handler)
        self.ha_ws.send(json.dumps({
            'id': event_id,
            'type': 'subscribe_events',
            'event_type': event_type                                     
            }))

    
    def _print_data(self,event_message):
        print(event_message)
        ha_utterance=event_message.get("utterance")
        if not ha_utterance==None:
            mycroft_message={"lang": "en-us", "utterances": [ha_utterance]}
            self.emitter.emit(Message('recognizer_loop:utterance',mycroft_message))
            
    def on_message(self,ws, message):
        print message
        message_data=json.loads(message)
        if message_data.get('type') == 'event':
            event_type=message_data.get('event').get('event_type') 
            if event_type in self.ha_events:            
                event_data=message_data.get('event').get('data')   
                try:
                    self.ha_handlers[event_type](event_data)
                except:
                    logger.error("handler not defined for event %s" % event_type)
        elif message_data.get('type')=='auth_ok':
            self._do_register()
            
    def on_error(self,ws, error):
        print error
    
    def on_close(self,ws):
        print "### closed ###"
    
    def on_open(self,ws):
### TODO : no password!!!!!
        ws.send(json.dumps(
               {"type": "auth", "api_password": ""}))
        ws.on_message = self.on_message


    def run(self):
        self.ha_ws.on_open = self.on_open
        self.ha_ws.run_forever()

def create_skill():
    return HassSkill('HassSkill')
