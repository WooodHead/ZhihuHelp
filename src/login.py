# -*- coding: utf-8 -*-
import os
import re
import sys
import platform
import webbrowser
import json
import time

from src.lib.oauth.zhihu_oauth import ZhihuClient
from src.lib.oauth.zhihu_oauth.exception import NeedCaptchaException

from src.tools.config import Config
from src.tools.db import DB
from src.tools.debug import Debug
from src.tools.extra_tools import ExtraTools
from src.tools.http import Http
from src.tools.match import Match
from src.tools.path import Path


class Login(object):
    u"""
    登录部分，登录完成后返回一个可用的client对象，用于进一步获取知乎网对应信息
    """

    def __init__(self):
        self.client = ZhihuClient()

    def get_login_client(self):
        self.hello_world()

        if Config.remember_account:
            account = Config.account
            password = Config.password
        else:
            account, password = self.get_account()
        captcha = ''
        while not self.login(account, password, captcha):
            print u'啊哦，登录失败，可能需要输入验证码'
            print u'输入『yes』按回车更换其他账号'
            print u'直接敲击回车获取验证码'
            confirm = raw_input()
            if confirm == 'yes':
                account, password = self.get_account()
            captcha = self.get_captcha()
        Config.picture_quality = self.set_picture_quality()
        Config._save()
        return self.client

    def login(self, account, password, captcha=None):
        try:
            is_login_success, reason = self.client.login(account, password, captcha)
        except NeedCaptchaException:
            # 保存验证码并提示输入，重新登录
            print u'登录失败，需要输入验证码'
            return False
        if not is_login_success:
            print u'登陆失败'
            print u"失败原因 => " + str(reason)
            return False

        print u'登陆成功！'
        print u'登陆账号:', account
        print u'请问是否需要记住帐号密码？输入yes记住，输入其它任意字符跳过，回车确认'
        if raw_input() == 'yes':
            Config.account, Config.password, Config.remember_account = account, password, True
            print u'帐号密码已保存,可通过修改config.json修改设置'
        else:
            Config.account, Config.password, Config.remember_account = '', '', False
            print u'跳过保存环节，进入下一流程'
        Config._save()
        return True

    def get_captcha(self):
        captcha_path = Path.base_path + u'/我是登陆知乎时的验证码.gif'

        image = open(captcha_path, 'wb')
        image.write(self.client.get_captcha())
        image.close()

        print u'请输入您所看到的验证码'
        print u'验证码在助手所处的文件夹中'
        print u'验证码位置:'
        print captcha_path
        # 尝试自动打开验证码
        webbrowser.get().open_new_tab(u'file:///' + captcha_path)

        print u'如果不需要输入验证码可点按回车跳过此步'
        captcha = raw_input()
        return captcha

    @staticmethod
    def hello_world():
        print u'您好，欢迎使用知乎助手'
        print u''
        print u''
        print u'本版内置了公共账号『孟晴雪』，默认使用内置账号进行登陆'
        print u''
        print u''
        print u'全部代码均已开源，github地址:https://github.com/YaoZeyuan/ZhihuHelp__Python'
        print u'Tips：只有在获取私人收藏夹的内容时，助手才需要使用您的账号登陆，日常使用时直接用内置账号登陆即可'
        print u'现在开始登陆流程，请根据提示输入您的账号密码'
        print u''
        print u''
        return

    @staticmethod
    def get_account():
        print u'请输入您的知乎注册邮箱，回车确认'
        print u'####################################'
        account = raw_input()
        while not re.search(r'\w+@[\w\.]{3,}', account):
            print u'抱歉，输入的账号不规范...\n请输入正确的知乎登录邮箱\n'
            print u'范例：mengqingxue2014@qq.com\n5719abc@sina.cn'
            print u'请重新输入账号，回车确认'
            account = raw_input()
        print u'请输入密码，回车确认'
        password = raw_input()
        while len(password) < 6:
            print u'密码长度不正确，密码至少6位'
            print u'请重新输入密码，回车确认'
            password = raw_input()
        return account, password

    @staticmethod
    def set_picture_quality():
        print u'请选择电子书内的图片质量'
        print u'输入0为无图模式，生成电子书体积最小'
        print u'输入1为标准模式，图片清晰度能满足绝大多数答案的需要'
        print u'输入2为高清模式，图片为知乎原图，清晰度最高，但电子书体积是标准模式的4倍，只有答案条目小于100条时才可以考虑使用'
        print u'请输入图片模式(0、1或2)，回车确认'
        try:
            quality = int(raw_input())
        except ValueError as error:
            print error
            print u'数字转换错误。。。'
            print u'图片模式重置为标准模式，点击回车继续'
            quality = 1
            raw_input()
        if not (quality in [0, 1, 2]):
            print u'输入数值非法'
            print u'图片模式重置为标准模式，点击回车继续'
            quality = 1
            raw_input()
        return quality
