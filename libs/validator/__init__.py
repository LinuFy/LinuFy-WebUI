# -*- coding: utf-8 -*-

from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse, urljoin
from flask import request
import re


def email(email):
    try:
        validate_email(email).email
        return True
    except EmailNotValidError:
        return False


def vlan(vlan_id):
    if isinstance(vlan_id, int) and 1 <= vlan_id  <= 4094:
        return True
    return False


def network_port(port):
    if not isinstance(port, int):
        return False

    if 1 <= port <= 65535:
        return True
    return False


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def is_valid_ssh_private_key(text):
    startPattern = re.compile("^-----BEGIN [A-Z]+ PRIVATE KEY-----")
    optionPattern = re.compile("^.+: .+")
    contentPattern = re.compile("^([a-zA-Z0-9+/]{64}|[a-zA-Z0-9+/]{1,64}[=]{0,2})$")
    endPattern = re.compile("^-----END [A-Z]+ PRIVATE KEY-----")

    def contentState(text):
        for i in range(0, len(text)):
            line = text[i]

            if endPattern.match(line):
                if i == len(text)-1 or len(text[i+1]) == 0:
                    return True
                else:
                    return False

            elif not contentPattern.match(line):
                return False

        return False


    def optionState(text):
        for i in range(0,len(text)):
            line = text[i]

            if line[-1:] == '\\':
                return optionState(text[i+2:])

            if not optionPattern.match(line):
                return contentState(text[i+1:])

        return False


    def startState(text):
        if len(text) == 0 or not startPattern.match(text[0]):
            return False
        return optionState(text[1:])


    return startState([n.strip() for n in text.split("\n")])

