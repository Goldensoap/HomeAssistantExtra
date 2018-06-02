# HomeAssistantExtra
The custom components that I do it myself and collect. And the configuration file now running in Ubuntu and raspberry
## Deemo
  <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/front.png" width=50% height=50% />

### The front page has integrated the following platform
 - environment sensor 
  
    - Including PM1.0/2.5/10 temp,lightlevel and humidity.thoes sensor can provide basic informations of room.

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/ESPenvironment.png" width=50% height=50% />

    - It base on **MQTT** + **ESPEasy** + **NodeMcu(ESP8266)**

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/nodemcu.jpg" width=50% height=50% />

 - Hefeng weather

    - weekly forcast can show today's details and next five day's weather

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/hefengweather.png" width=50% height=50% />

    - The hourly forcast shows next per 3 hour

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/heweather02.png" width=50% height=50% />

    - The outdoor environment  
    
        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/heweather01.png" width=50% height=50% />

    - quality life can tell you some advice for today's weather

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/heweather03.png" width=50% height=50% />

 - XiaoMiGateWay

    - Xiaomi GateWay can make you control the XiaoMi hardware(if it can connected gateway......)

 - sonoff

    - Buy a sonoff hardware in **taobao** or **itead** .Most of it used to control relay(such like controling curtain like me).But now the firmware update and you can use sensor in sonoff's GPIO
    
        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/sonoff1.jpg" width=50% height=50% />

    - sonoff also use ESP8266 as core,so the process is same as NodeMcu.

 - IPCamera

    - you can see the real-time situation on the web

 - baidu or dilb face_identify 
 
    - you can use the identification from major technology companies .If you concerned about your own photos, you may choose local face reconition based on dilb or opencv.

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/face_rec.png" width=50% height=50% />

 - Dingdong smart speaker

    - By HAbridge you can link to your dear smart speaker sunch as Echo then the bridge will let your speaker become more powerful(control device in HA not only in instructions)

    - BTW the interaction with Dingdong looks so stupid ,maybe i should select a smarter one.
 - node_red

    - this webpage just for people with Internet of Things experience.of course after clear the functions of it,you can easily make highly controllable automation strategy instead of HA's editor.

 - vlc for tts

    - the vlc platform is for wired speaker,For stable i give up to choose wiredless speakers.The TTS platform is baidu.

        <img src="https://github.com/Goldensoap/MarkdownPicture-/raw/master/HA/media.png" width=50% height=50% />

## The whole HA and HAbridge and node-red is running on the docker. 


