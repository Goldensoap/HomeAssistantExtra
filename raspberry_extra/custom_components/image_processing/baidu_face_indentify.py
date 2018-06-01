"""
百度人脸识别、人脸检测

# 基于百度人脸识别api:
    https://ai.baidu.com/tech/face

# Author:
    lidicn

# Edition：V1.25


# Update:
    2018-1-25

# 配置方法参见:
https://bbs.hassbian.com/thread-2460-1-1.html
"""
import logging
import io
import os
import voluptuous as vol
from base64 import b64encode
from homeassistant.core import split_entity_id
from homeassistant.components.image_processing import (
    PLATFORM_SCHEMA, CONF_SOURCE, CONF_ENTITY_ID, CONF_NAME)
from homeassistant.components.image_processing import ATTR_CONFIDENCE
from homeassistant.components.image_processing.microsoft_face_identify import (
    ImageProcessingFaceEntity)
import homeassistant.helpers.config_validation as cv
import requests
import json
import base64
from requests import get
import time
from PIL import Image
import sys
import homeassistant.loader as loader
import threading
from requests.exceptions import ReadTimeout,ConnectionError,RequestException
_LOGGER = logging.getLogger(__name__)

ATTR_NAME = 'name'
ATTR_MATCHES = 'faces'
ATTR_TOTAL_MATCHES = 'total faces'
ATTR_FACE_STRING = 'face_string'
ATTR_GET_PICTURE_COSTTIME = '获取照片耗时'
ATTR_RESIZE_PICTURE_COSTTIME = '调整分辨率耗时'
ATTR_RECOGNITION_COSTTIME = '人脸识别耗时'
ATTR_TOTAL_COSTTIME = '总耗时'

GROUP_ID = 'normal_group'


CONF_APP_ID = 'app_id'
CONF_API_KEY = 'api_key'
CONF_SECRET_KEY = 'secret_key'
CONF_SNAPSHOT_FILEPATH = 'snapshot_filepath'
CONF_RESIZE = 'resize'
CONF_HA_URL = 'ha_url'
CONF_HA_PASSWORD = 'ha_password'
CONF_DETECT_TOP_NUM = 'detect_top_num'
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_APP_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_SECRET_KEY): cv.string,
    vol.Required(CONF_RESIZE,default='0'): cv.string,
    vol.Required(CONF_HA_URL): cv.url,
    vol.Required(CONF_HA_PASSWORD): cv.string,
    vol.Required(CONF_SNAPSHOT_FILEPATH): cv.string,
    vol.Optional(CONF_DETECT_TOP_NUM,default=1): cv.positive_int,
})

ATTR_USERINFO = 'user_info'
ATTR_IMAGE = 'image'
ATTR_UID = 'uid'
ATTR_GROUPID = 'group_id'
DOMAIN = 'image_processing'

SERVUCE_REGISTERUSERFACE = 'baidu_face_indentify_registerUserFace'
SERVUCE_REGISTERUSERFACE_SCHEMA = vol.Schema({
    vol.Required(ATTR_USERINFO): cv.string,
    vol.Required(ATTR_IMAGE): cv.isfile,
    vol.Required(ATTR_UID): cv.string,
})

SERVUCE_GETUSERLIST = 'baidu_face_indentify_getUserList'
SERVUCE_GETUSERLIST_SCHEMA = vol.Schema({
    vol.Optional(ATTR_GROUPID,default=GROUP_ID): cv.string,
})

SERVUCE_DELETEUSER = 'baidu_face_indentify_deleteUser'
SERVUCE_DELETEUSER_SCHEMA = vol.Schema({
    vol.Required(ATTR_UID): cv.string,
})

SERVUCE_DETECTFACE = 'baidu_face_indentify_detectface'
SERVUCE_DETECTFACE_SCHEMA = vol.Schema({
    vol.Required(ATTR_IMAGE): cv.isfile,
})

face_fields = {
    "beauty": ["颜值","int"],
    "age": ["年龄","岁"],
    "gender": ["性别",None,{"female":"女性","male":"男性"}],
    "gender_probability": ["性别置信度","%",],
    "expression": ["表情",None,{"0":"不笑","1":"微笑","2":"大笑"}],
    "expression_probablity": ["表情置信度","%",],
    "race": ["人种",None,{"yellow":"黄种人","white":"白种人","black":"黑人","arabs":"阿拉伯人"}],
    "race_probability": ["人种置信度","%",],
    "face_probability": ["人脸置信度","%"],
    "rotation_angle": ["人脸框相对于竖直方向的顺时针旋转角","°"],
    "glasses": ["是否带眼镜",None,{"0":"无眼镜","1":"普通眼镜","2":"墨镜"}],
    "glasses_probability": ["眼镜置信度","%",],
    "yaw": ["三维旋转之左右旋转角","°"],
    "pitch": ["三维旋转之俯仰角度","°"],
    "roll": ["平面内旋转角","°"],
    "blur": ["人脸模糊程度",None,{"0":"清晰","1":"模糊"}],
    "illumination": ["脸部区域的光照程度","int"],
    "completeness": ["人脸完整度",None,{"0":"人脸溢出图像边界","1":"人脸都在图像边界内"}]

}
human_type = {
    "human": ["真实人脸置信度","%"],
    "cartoon": ["卡通人脸置信度","%"],
}
faceshape = {
    "square":["国字脸","%"],
    "triangle":["倒三角脸","%"],
    "oval":["鹅蛋脸","%"],
    "heart":["心形脸","%"],
    "round":["圆脸","%"],
}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the demo image processing platform."""
    app_id = config.get(CONF_APP_ID)
    api_key = config.get(CONF_API_KEY)
    secret_key = config.get(CONF_SECRET_KEY)
    snapshot_filepath = config.get(CONF_SNAPSHOT_FILEPATH)
    resize = config.get(CONF_RESIZE)
    ha_url = config.get(CONF_HA_URL)
    ha_password = config.get(CONF_HA_PASSWORD)
    detect_top_num = config.get(CONF_DETECT_TOP_NUM)
    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(BaiduFaceIdentifyEntity(
            hass,camera[CONF_ENTITY_ID], camera.get(CONF_NAME),app_id,api_key,secret_key,snapshot_filepath,resize,ha_url,ha_password,detect_top_num
        ))
    add_devices(entities)
    persistent_notification = loader.get_component('persistent_notification')
    def getAccessToken():
        #请求参数
        client_id = api_key
        client_secret = secret_key
        grant_type = 'client_credentials'
        request_url = 'https://aip.baidubce.com/oauth/2.0/token'
        params = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': grant_type}
        r = requests.get(url=request_url, params=params)
        access_token = json.loads(r.text)['access_token']
        return access_token

    def get_image_base64(image_path):
        with open(image_path, 'rb') as fp:
            return base64.b64encode(fp.read())

    #人脸注册服务
    def registerUserFace(service):

        def register():
            user_info = service.data[ATTR_USERINFO]
            uid = service.data[ATTR_UID]
            image = service.data[ATTR_IMAGE]
            group_id = GROUP_ID
            request_url = "https://aip.baidubce.com/rest/2.0/face/v2/faceset/user/add"

            img = get_image_base64(image)

            params = {'access_token': getAccessToken()}
            data = {"group_id": group_id, "image": img, "uid": uid, "user_info": user_info}
            r = requests.post(url=request_url, params=params, data=data)
            resultjson = json.loads(r.text)
            if 'error_code' in resultjson:
                persistent_notification.create(hass,'人脸数据注册失败',title='百度人脸识别')
            elif 'error_msg' in resultjson:
                if resultjson['error_msg'] == 'image exist':
                    persistent_notification.create(hass,'此人脸已经使用过',title='百度人脸识别')
            else:
                persistent_notification.create(hass,'人脸数据注册成功',title='百度人脸识别')
            return json.loads(r.text)
        threading.Thread(target=register).start()
    hass.services.register(DOMAIN, SERVUCE_REGISTERUSERFACE, registerUserFace,schema=SERVUCE_REGISTERUSERFACE_SCHEMA)

    #人脸数据查询服务
    def getUserInfo(service):
        def userinfo():
            group_id = service.data[ATTR_GROUPID]
            request_url = "https://aip.baidubce.com/rest/2.0/face/v2/faceset/group/getusers"
            params = {'access_token': getAccessToken()}
            data = {"group_id": group_id}
            r = requests.post(url=request_url, params=params, data=data)
            resultjson = json.loads(r.text)
            #outputst = ''
            br_string = ''
            if resultjson['result_num'] == 0:
                persistent_notification.create(hass,'无人脸注册数据',title='百度人脸识别')
            elif 'error_msg' in resultjson:
                if resultjson['error_msg'] == 'image exist':
                    persistent_notification.create(hass,'此人脸已经使用过',title='百度人脸识别')
            else:
                for i in range(len(resultjson['result'])):
                    br_string = br_string + str(resultjson['result'][i]) + '<br />'

                persistent_notification.create(hass,br_string,title='百度人脸识别')
            return json.loads(r.text)
        threading.Thread(target=userinfo).start()
    hass.services.register(DOMAIN, SERVUCE_GETUSERLIST, getUserInfo,schema=SERVUCE_GETUSERLIST_SCHEMA)

    #人脸数据删除服务
    def delUserInfo(service):
        def deluserinfo():
            uid = service.data[ATTR_UID]
            request_url = "https://aip.baidubce.com/rest/2.0/face/v2/faceset/user/delete"
            params = {'access_token': getAccessToken()}
            data = {'uid': uid}
            r = requests.post(url=request_url, params=params, data=data)
            resultjson = json.loads(r.text)
            if 'error_code' in resultjson:
                persistent_notification.create(hass,'人脸数据删除失败<br />检查uid是否正确',title='百度人脸识别')
            elif 'error_msg' in resultjson:
                if resultjson['error_msg'] == 'user not exist':
                    persistent_notification.create(hass,'该uid不存在',title='百度人脸识别')
            else:
                persistent_notification.create(hass,'人脸数据删除成功',title='百度人脸识别')
            return json.loads(r.text)
        threading.Thread(target=deluserinfo).start()
    hass.services.register(DOMAIN, SERVUCE_DELETEUSER, delUserInfo,schema=SERVUCE_DELETEUSER_SCHEMA)

    def details_faceinfo(json):
        resultinfo = ''
        for key, value in json.items():
            if key in face_fields:
                if face_fields[key][1] == "%":
                    resultinfo = resultinfo + face_fields[key][0] + "：" + str(round(json[key]*100,2)) + "%<br />"
                elif face_fields[key][1] == "int":
                    resultinfo = resultinfo + face_fields[key][0] + "：" + str(json[key]) + "<br />"
                elif face_fields[key][1] == None:
                    resultinfo = resultinfo + face_fields[key][0] + "：" + face_fields[key][2][str(json[key])] + "<br />"
                else:
                    resultinfo = resultinfo + face_fields[key][0] + "：" + str(json[key]) + face_fields[key][1] + "<br />"
            elif key == 'faceshape':
                for i in range(len(json['faceshape'])):
                    resultinfo = resultinfo + faceshape[json['faceshape'][i]['type']][0] + "：" + str(round(json['faceshape'][i]['probability']*100,2)) + "%<br />"

            elif key == 'qualities':
                resultinfo = resultinfo + human_type['human'][0] + "：" + str(round(json['qualities']['type']['human']*100,2)) + "%<br />"
                resultinfo = resultinfo + human_type['cartoon'][0] + "：" + str(round(json['qualities']['type']['cartoon']*100,2)) + "%<br />"

        return resultinfo




    #人脸检测服务
    def detectface(service):
        def detect():
            image = service.data[ATTR_IMAGE]
            request_url = "https://aip.baidubce.com/rest/2.0/face/v2/detect"
            img = get_image_base64(image)
            params = {
                'access_token': getAccessToken(),
                'face_fields': 'age,beauty,expression,faceshape,gender,glasses,race,qualities',
                }
            data = {"image": img}
            r = requests.post(url=request_url, params=params, data=data)
            resultjson = json.loads(r.text)
            if resultjson['result_num'] == 0:
                persistent_notification.create(hass,'没检测到人脸存在！',title='百度人脸识别')
            elif 'error_msg' in resultjson:
                if resultjson['error_msg'] == 'Access token invalid or no longer valid':
                    persistent_notification.create(hass,'百度Access Token获取失败！',title='百度人脸识别')
                elif resultjson['error_msg'] == 'Open api qps request limit reached':
                    persistent_notification.create(hass,'QPS超限额',title='百度人脸识别')
                else:
                    persistent_notification.create(hass,resultjson['error_msg'],title='百度人脸识别')
            else:
                persistent_notification.create(hass,details_faceinfo(resultjson['result'][0]),title='百度人脸识别')
            return json.loads(r.text)
        threading.Thread(target=detect).start()
    hass.services.register(DOMAIN, SERVUCE_DETECTFACE, detectface,schema=SERVUCE_DETECTFACE_SCHEMA)

class BaiduFaceIdentifyEntity(ImageProcessingFaceEntity):
    """Dlib Face API entity for identify."""


    def __init__(self, hass, camera_entity, name, app_id, api_key, secret_key, snapshot_filepath,resize,ha_url,ha_password,detect_top_num):
        """Initialize demo ALPR image processing entity."""

        super().__init__()
        self.hass = hass
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self.snapshot_filepath = snapshot_filepath
        self.resize = resize
        self.ha_url = ha_url
        self.ha_password = ha_password

        if name:
            self._name = name
        else:
            self._name = "Baidu Face {0}".format(
                split_entity_id(camera_entity)[1])
        self._camera = camera_entity
        self.unknowns_face_path = os.path.join(self.snapshot_filepath,'face.jpg')
        self.resize_face_path = os.path.join(self.snapshot_filepath,'resize.jpg')
        self.detect_top_num = detect_top_num


        self._matches = {}
        self._total_matches = 0
        self._face_string = ''

        self._get_picture_costtime = ''
        self._reszie_picture_costtime = ''
        self._recognition_costtime = ''
        self._total_costtime = ''


    def get_file_content(self,filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    def getAccessToken(self):
        #请求参数
        client_id = self.api_key
        client_secret = self.secret_key
        grant_type = 'client_credentials'

        request_url = 'https://aip.baidubce.com/oauth/2.0/token'
        params = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': grant_type}

        try:
            response = requests.get(url=request_url, params=params,timeout=5)
            access_token = json.loads(response.text)['access_token']
        except ReadTimeout:
            _LOGGER.error("百度人脸识别获取access_token连接超时")
        except ConnectionError:
            _LOGGER.error("百度人脸识别获取access_token连接错误")
        except RequestException:
            _LOGGER.error("百度人脸识别获取access_token发生未知错误")
        return access_token

    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self._total_matches

    @property
    def state_attributes(self):
        """Return device specific state attributes."""
        return {
            ATTR_MATCHES: self._matches,
            ATTR_TOTAL_MATCHES: self._total_matches,
            ATTR_FACE_STRING: self._face_string,
            ATTR_GET_PICTURE_COSTTIME: self._get_picture_costtime,
            ATTR_RESIZE_PICTURE_COSTTIME: self._reszie_picture_costtime,
            ATTR_RECOGNITION_COSTTIME: self._recognition_costtime,
            ATTR_TOTAL_COSTTIME: self._total_costtime,

        }

    def resize_picture(self,imagepath,resize):
        im = Image.open(imagepath)
        (x,y) = im.size #read image size
        x_s = resize #define standard width
        y_s = int(y * x_s / x) #calc height based on standard width
        out = im.resize((x_s,y_s),Image.ANTIALIAS) #resize image with high-quality
        out.save(self.resize_face_path)

    def get_picture(self):
        host=self.ha_url
        t=time.time()
        url = '{}/api/camera_proxy/{}?time={}'.format(host, self._camera , int(round(t * 1000)))
        headers = {'x-ha-access': self.ha_password,
                   'content-type': 'application/json'}
        response = get(url, headers=headers)
        with open(self.unknowns_face_path, 'wb') as fo:
            fo.write(response.content)

    def strat_time(self):
        return time.time()

    def count_time(self,start_time):
        cost_time = time.time() - start_time
        return str(round(cost_time,5))+"秒"


    def process_image(self, image):
        """Process image."""
        get_picture_start = time.time()
        self.get_picture()
        get_picture_costtime = self.count_time(get_picture_start)
        if int(self.resize) != 0:
            resize_picture_start = time.time()
            self.resize_picture(self.unknowns_face_path,int(self.resize))
            reszie_picture_costtime = self.count_time(resize_picture_start)
            convert_start = time.time()
            unknowns = self.get_file_content(self.resize_face_path)
            convert_costtime = self.count_time(convert_start)

        elif self.resize == '0':
            reszie_picture_costtime = '0秒'
            convert_start = time.time()
            unknowns = self.get_file_content(self.unknowns_face_path)
            convert_costtime = self.count_time(convert_start)

        recognition_time = time.time()
        found = []

        #request_url = "https://aip.baidubce.com/rest/2.0/face/v2/identify"
        request_url = "https://aip.baidubce.com/rest/2.0/face/v2/multi-identify"

        # 参数images：图像base64编码
        img = base64.b64encode(unknowns)

        params = {'access_token': self.getAccessToken()}
        data = {
            "group_id": GROUP_ID,
            "image": img,
            "detect_top_num": self.detect_top_num,
            }


        try:
            r = requests.post(url=request_url, params=params, data=data,timeout=5)
        except ReadTimeout:
            _LOGGER.error("百度人脸识别连接超时")
        except ConnectionError:
            _LOGGER.error("百度人脸识别连接错误")
        except RequestException:
            _LOGGER.error("百度人脸识别发生未知错误")


        result = json.loads(r.text)
        face_string = ''
        result_num = 0
        if not 'result' in result:
            found = []
            recognition_costtime = '未识别出人脸！'
            if 'error_msg' in result:
                _LOGGER.info('BaiduFaceIdentify face not found!')
        elif 'result' in result:
            if 'result_num' in result:
                result_num = result['result_num']

            for i in range(len(result['result'])):
                if result['result'][i]['scores'][0] < 80:
                    pass
                    recognition_costtime = '未识别出匹配数据库的人脸！'
                elif result['result'][i]['scores'][0] > 80:
                    found.append({
                        ATTR_NAME: result['result'][i]['user_info'],
                        ATTR_CONFIDENCE: result['result'][i]['scores'][0]
                    })
                    face_string = face_string + result['result'][i]['user_info'] + '、'
                    recognition_costtime = self.count_time(recognition_time)
        total_costtime = self.count_time(get_picture_start)
        self._get_picture_costtime = get_picture_costtime
        self._reszie_picture_costtime = reszie_picture_costtime
        self._recognition_costtime = recognition_costtime
        self._total_costtime = total_costtime

        self._face_string = face_string
        self._total_matches = result_num
        self._matches = found
