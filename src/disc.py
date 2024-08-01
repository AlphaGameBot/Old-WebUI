import requests
import json

class DiscordException(Exception):
    pass
    
class ShittyDiscordHandler:
    def __init__(self, token: str, http_headers:dict={}):
        self.CONSTRUCT_AVATAR_URL = "https://cdn.discordapp.com/avatars/%s/%s.png"
        self.CONSTRUCT_USER_URL = "https://discord.com/api/users/%s"
        self.BOT_USER_TOKEN = token

        self.REQUEST_HEADERS = {
            "Authorization": "Bot %s" % self.BOT_USER_TOKEN
        }
        self.REQUEST_HEADERS.update(http_headers)

    def getUserInformation(self, userid) -> dict:
        r = requests.get(self.CONSTRUCT_USER_URL % str(userid), headers=self.REQUEST_HEADERS)
        d = json.loads(r.text)

        if r.status_code != 200:
            raise DiscordException(
                d["message"])

        return d
                            
    def getAvatarFromUser(self, userid, size=128, rc=False):
        d = self.getUserInformation(userid)        
        avatar_hash = user_data["avatar"]

        u = self.CONSTRUCT_AVATAR_URL % (str(userid), avatar_hash) + "?size=%s" % str(size)
        if rc == False:
            return u
        else:
            return u, user_data
