# -*- coding: utf-8 -*-
""" Emailer module used by LinuFy"""

import smtplib
from email.utils import formatdate
from flask import flash
from flask_mail import Message

from linufy.libs import configurations, crypto
from linufy.app import mail

from . import template


def send_with_action(title, message, button_text, button_link, toaddrs = []):
      try:
            msg = Message(title, sender = configurations.get('mail_username').value, recipients = toaddrs)
            msg.body = message
            msg.html = template.mail_with_action(title, message, button_text, button_link)
            mail.send(msg)
            return True
      except Exception as e:
            print(e)
            return False


def send_without_action(title, message, toaddrs = []):
      try:
            msg = Message(title, sender = configurations.get('mail_username').value, recipients = toaddrs)
            msg.body = message
            msg.html = template.mail_without_action(title, message)
            mail.send(msg)
            return True
      except Exception as e:
            print(e)
            return False