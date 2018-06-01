"""
Baidu TTS　Developer by Charley
"""
import voluptuous as vol
from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG,ATTR_OPTIONS
import homeassistant.helpers.config_validation as cv
import os
import requests
import logging
import json

_Log=logging.getLogger(__name__)

# 默认语言
DEFAULT_LANG = 'zh'

# 支持的语言
SUPPORT_LANGUAGES = [
    'zh',
]

CONF_APIKEY = 'api_key'
CONF_SECRETKEY = 'secret_key'
CONF_SPEED =  'speed'
CONF_PITCH = 'pitch'
CONF_VOLUME = 'volume'
PERSON = 'person'

END_TAG = {
    'Han':{'speed':5,'pitch':5,'volume':9,'person':1,},
    'Si':{'speed':5,'pitch':5,'volume':9,'person':0,},
    'Bi':{'speed':3,'pitch':9,'volume':9,'person':0,},
    'An':{'speed':3,'pitch':9,'volume':9,'person':1,},
    'Xiaoyao':{'speed':5,'pitch':5,'volume':9,'person':3,},
    'Yaya':{'speed':5,'pitch':5,'volume':9,'person':4,},

}

TOKEN_INTERFACE = 'https://openapi.baidu.com/oauth/2.0/token'
TEXT2AUDIO_INTERFACE = 'http://tsn.baidu.com/text2audio'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_APIKEY): cv.string,
    vol.Optional(CONF_SECRETKEY):cv.string,
    vol.Optional(CONF_SPEED,default='5'): cv.string,
    vol.Optional(CONF_PITCH,default='5'): cv.string,
    vol.Optional(CONF_VOLUME,default='5'): cv.string,
    vol.Optional(PERSON,default='0'): cv.string,
})

def get_engine(hass, config):
    lang = config.get(CONF_LANG)
    apiKey = config.get(CONF_APIKEY)
    secretKey = config.get(CONF_SECRETKEY)
    speed = config.get(CONF_SPEED)
    pitch = config.get(CONF_PITCH)
    volume = config.get(CONF_VOLUME)
    person = config.get(PERSON)
    tts_path = hass.config.path('tts')

    if apiKey == None:
        _Log.error('Api Key is nil')
        return False
    if secretKey == None:
        _Log.error('secretKey is nil')
        return False

    return BaiduTTS(lang,apiKey,secretKey,speed,pitch,volume,person,tts_path)

class BaiduTTS (Provider):

    def __init__(self,lang,apiKey,secretKey,speed,pitch,volume,person,tts_path):
        self._lang = lang
        self._apiKey = apiKey
        self._secretKey = secretKey
        self._speed = speed
        self._pitch = pitch
        self._volume = volume
        self._person = person
        token = self.getToken()
        _Log.info("token =====>" + token)
        self._Token = token
        self._tts_path = tts_path

    def getToken(self):
        resp = requests.get(TOKEN_INTERFACE,params={'grant_type': 'client_credentials','client_id':self._apiKey,'client_secret':self._secretKey})
        if resp.status_code != 200:
            _Log.error('Get ToKen Http Error status_code:%s' % resp.status_code)
            return None
        resp.encoding = 'utf-8'
        # toKenjsonStr =  resp.text
        tokenJson =  resp.json()

        if not 'access_token' in tokenJson:
            _Log.error('Get ToKen Json Error!')
            return None
        return tokenJson['access_token']

    @property
    def default_language(self):
        """Default language."""
        return self._lang

    @property
    def supported_languages(self):
        """List of supported languages."""
        return SUPPORT_LANGUAGES

    @property
    def supported_options(self):
        """Return list of supported options like voice, emotionen."""
        return ['person','filename','speed','pitch','volume']

    def message_to_tts(self,message,language,speed,pitch,volume,person):
        resp = requests.get(TEXT2AUDIO_INTERFACE,params={'tex':message,'lan':language,'tok':self._Token,'ctp':'1','cuid':'HomeAssistant','spd':speed,'pit':pitch,'vol':volume,'per':person})

        if resp.status_code == 500:
            _Log.error('Text2Audio Error:500 Not Support.')
            return
        if resp.status_code == 501:
            _Log.error('Text2Audio Error:501 Params Error')
            return
        if resp.status_code == 502:
            _Log.error('Text2Audio Error:502 TokenVerificationError.')
            _Log.Info('Now Get Token!')
            self._Token = self.getToken()
            self.get_tts_audio(message,language,options)
            return
        if resp.status_code == 503:
            _Log.error('Text2Audio Error:503 Composite Error.')
            return

        if resp.status_code != 200:
            _Log.error('get_tts_audio Http Error status_code:%s' % resp.status_code)
            return
        data = resp.content
        return data

    #def tts_to_file(self,data,options=None):



    def get_tts_audio(self, message, language, options=None):
        if options == None:
            get_person = self._person
            get_speed = self._speed
            get_pitch = self._pitch
            get_volume = self._volume
            get_filename = "nofilename"
        else:
            if "person" in options:
                get_person = options.get("person",1)
            else:
                get_person = self._person
            if "speed" in options:
                get_speed = options.get("speed",5)
            else:
                get_speed = self._speed
            if "pitch" in options:
                get_pitch = options.get("pitch",5)
            else:
                get_pitch = self._pitch
            if "volume" in options:
                get_volume = options.get("volume",5)
            else:
                get_volume = self._volume
            if "filename" in options:
                get_filename = options.get("filename","demo.mp3")
            else:
                get_filename = "nofilename"



        if self._Token == None:
            self._Token = self.getToken()

        if self._Token == None:
            _Log.error('get_tts_audio Self.ToKen is nil')
            return




        if '#' in message:
            message_list = message.split('*#')
            data_list = []
            for message_ls in message_list:
                if message_ls != '':
                    message_character = message_ls.split('#')
                    character = message_character[1]
                    data_list.append(self.message_to_tts(message = message_character[0],language=language,
                                    speed = END_TAG[character]['speed'],
                                    pitch = END_TAG[character]['pitch'],
                                    volume = END_TAG[character]['volume'],
                                    person = END_TAG[character]['person']))

            data = b"".join(data_list)
        else:
            data = self.message_to_tts(message,language,get_speed,get_pitch,get_volume,get_person)

        if get_filename == "nofilename":
            return ('mp3',data)
        else:
            filename = get_filename

        path_name =  os.path.join(self._tts_path , filename)
        if os.path.isfile(path_name ):
            os.remove(path_name)
        try:
            with open(path_name, 'wb') as voice:
                voice.write(data)
        except OSError:
            _Log.error("os error baidu tts write file False")
            return (None, None)
        return ('mp3',data)
