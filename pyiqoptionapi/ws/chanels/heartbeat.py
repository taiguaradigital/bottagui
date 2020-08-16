import datetime
from pyiqoptionapi.ws.chanels.base import Base


class Heartbeat(Base):

    name = "heartbeat"
    
    def __call__(self, heart_beat_time):
  
        data = {
                    "msg": {
                              "heartbeatTime": int(heart_beat_time),
                              "userTime": int(self.api.timesync.server_timestamp * 1000)
                           }
           
               }
        self.send_websocket_request(self.name, data, no_force_send=False)
