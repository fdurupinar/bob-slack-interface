import os
import sys
import time
import json
import base64
import pickle
import select

import datetime
import socket
import logging
from slackclient import SlackClient
from kqml import *

from indra.statements import stmts_from_json, stmts_to_json


logger = logging.getLogger('bob_slack')

user_cache = {}
channel_cache = {}

class BSI:

    def __init__(self, host, bob_port=6200):

        self.bob_slack_id = '<@UDPH2QM27>'

        # connect to slack
        self.start_slack()

        # connect to bob
        self.socket_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_b.connect((host, bob_port))
        # Startup sequences to let bob know about this connection
        self.bob_startup()

        self.channel = "cwc"
        self.logf = open('slack_bot_log.txt', 'a', 1)

        self.listen_to_sockets()




    def listen_to_sockets(self):
        while True:
            try:
                socks = [self.socket_b, self.sc.server.websocket]
                ready_socks, _, _ = select.select(socks, [], [])
                for sock in ready_socks:
                    if sock == self.socket_b:
                        data, addr = sock.recvfrom(1000000)
                        if data:
                            txt = data.decode('utf-8')

                            parts = txt.split('\n')
                            for part in parts:
                                if part:
                                    self.on_bob_message(part)
                    else:
                        res = self.read_message(self.sc)

                        if res:
                            (self.channel, username, msg, self.user_id) = res

                            if self.bob_slack_id in msg:
                                msg = msg.replace(self.bob_slack_id, '').strip()
                                # For some reason on Mac we get Mac quotes that we replace
                                msg = msg.replace('’', '\'')
                                print(msg)
                                ts = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
                                self.logf.write('%s\t%s\t%s\t' % (msg, self.user_id, ts))

                                self.send_to_bob(msg)

            except KeyboardInterrupt:
                break


    def bob_startup(self):

        logger.info('Initializing Bob connection...')

        self.bob_uttnum = 1

        msg = '(register :name bsb)'
        self.socket_b.sendall(msg.encode('utf-8'))
        msg = '(subscribe :content (tell &key :content (spoken . *)))'
        self.socket_b.sendall(msg.encode('utf-8'))
        msg = '(subscribe :content (tell &key :content (display-model . *)))'
        self.socket_b.sendall(msg.encode('utf-8'))
        msg = '(subscribe :content (tell &key :content (display-image . *)))'
        self.socket_b.sendall(msg.encode('utf-8'))
        msg = '(tell :content (module-status ready))'
        self.socket_b.sendall(msg.encode('utf-8'))
        msg = '(tell :content (start-conversation))'
        self.socket_b.sendall(msg.encode('utf-8'))


    def get_spoken_phrase(self, content):
        say_what = content.gets('what')
        return say_what

    def on_bob_message(self, data):
        logger.debug('data: ' + data)
        # Check what kind of message it is
        kl = KQMLPerformative.from_string(data)
        head = kl.head()
        content = kl.get('content')
        if head == 'tell' and content.head().lower() == 'display-model':
            parts = data.split('\n')
            if len(parts) > 1:
                logger.error('!!!!!!!!!!!!\nMessage with multiple parts\n ' +
                             '!!!!!!!!!!!')
                logger.error(parts)
        logger.info('Got message with head: %s' % head)
        logger.info('Got message with content: %s' % content)
        if not content:
            return
        if content.head().lower() == 'spoken':
            spoken_phrase = self.get_spoken_phrase(content)
            # self.bob_to_sbgn_say(spoken_phrase)
            self.send_message(self.sc, self.channel, spoken_phrase)

        elif content.head().lower() == 'display-image':
            image_type = content.gets('type')
            path = content.gets('path')

            self.bob_show_image(path, image_type)

    def send_to_bob(self, comment):
        # Convert comment into kqml message format and send it to bob
        if comment == 'reset':
            msg = '(tell :content (start-conversation))'
            self.socket_b.sendall(msg.encode('utf-8'))

        else:
            msg = '(tell :content (started-speaking :mode text :uttnum 1 ' + \
                    ':channel Desktop :direction input))'
            self.socket_b.sendall(msg.encode('utf-8'))
            msg = '(tell :content (stopped-speaking :mode text :uttnum 1 ' + \
                    ':channel Desktop :direction input))'
            self.socket_b.sendall(msg.encode('utf-8'))
            msg = '(tell :content (word "%s" :uttnum %d :index 1 ' % (comment, self.bob_uttnum) + \
                    ':channel Desktop :direction input))'
            self.socket_b.sendall(msg.encode('utf-8'))
            msg = '(tell :content (utterance :mode text :uttnum %d ' % self.bob_uttnum + \
                    ':text "%s" ' % comment + \
                    ':channel Desktop :direction input))'
            self.socket_b.sendall(msg.encode('utf-8'))
            self.bob_uttnum += 1

    def start_slack(self):

        self.token = read_slack_token()

        if not self.token:
            sys.exit()
        self.sc = SlackClient(self.token)
        conn = self.sc.rtm_connect()
        if not conn:
            logger.error('Could not connect to Slack.')
            sys.exit()

    def bob_show_image(self, file_name, image_type):
        logger.info('showing image')

        self.sc.api_call("files.upload",
                                        channels=self.channel,
                                        filename=file_name,
                                        filetype="png",
                                        file=open(file_name, 'rb'),
                                        text=image_type)


    def get_user_name(self, sc, user_id):
        user_name = user_cache.get(user_id)
        if user_name:
            return user_name
        res = sc.server.api_call('users.info', users=user_id)
        user_info = json.loads(res)
        for user in user_info['users']:
            if user['id'] == user_id:
                user_cache[user_id] = user['name']
                return user['name']
        return None


    def get_channel_name(self, sc, channel_id):
        channel_name = channel_cache.get(channel_id)
        if channel_name:
            return channel_name
        res = sc.server.api_call('channels.info', channel=channel_id)
        channel_info = json.loads(res)
        channel = channel_info['channel']
        if channel['id'] == channel_id:
            channel_cache[channel_id] = channel['name']
            return channel['name']
        return None


    def read_message(self, sc):
        events = sc.rtm_read()
        if not events:
            print('.', end='', flush=True)
            return None
        logger.info('%s events happened' % len(events))
        event = events[0]
        event_type = event.get('type')
        if not event_type:
            return
        if event_type == 'message':
            try:
                msg = event['text']
            except Exception:
                logger.info('Could not get message text, skipping')
                logger.info(event)
                return -1
            try:
                user = event['user']
            except Exception:
                logger.info('Message not from user, skipping')
                #logger.info(msg)
                return -1
            channel = event['channel']

            user_name = self.get_user_name(sc, user)
            # channel_name = get_channel_name(sc, channel)
            logger.info('Message received - [%s]: %s' %
                        (user_name, msg))
            return (channel, user_name, msg, user)

        return None


    def send_message(self, sc, channel, msg):
        sc.api_call("chat.postMessage",
                    channel=channel,
                    text=msg, as_user=True)
        logger.info('Message sent: %s' % msg)


def format_stmts_str( stmts):
    msg = ''
    for stmt in stmts:
        txt = stmt.evidence[0].text
        if txt is None:
            line = '`%s`\n' % stmt
        else:
            line = '`%s`, %s\n' % (stmt, txt)
        msg += line

    return msg


def format_stmts( stmts, output_format):
    if output_format == 'tsv':
        msg = ''
        for stmt in stmts:
            if not stmt.evidence:
                logger.warning('Statement %s without evidence' % stmt.uuid)
                txt = ''
                pmid = ''
            else:
                txt = stmt.evidence[0].text if stmt.evidence[0].text else ''
                pmid = stmt.evidence[0].pmid if stmt.evidence[0].pmid else ''
            line = '%s\t%s\t%s\n' % (stmt, txt, pmid)
            msg += line
        return msg
    elif output_format == 'pkl':
        fname = 'indrabot.pkl'
        with open(fname, 'wb') as fh:
            pickle.dump(stmts, fh)
        return fname
    # elif output_format == 'pdf':
    #     fname = 'indrabot.pdf'
    #     ga = GraphAssembler(stmts)
    #     ga.make_model()
    #     ga.save_pdf(fname)
    #     return fname
    elif output_format == 'json':
        msg = json.dumps(stmts_to_json(stmts), indent=1)
        return msg

    return None

def read_slack_token(fname=None):
    if fname is None:
        here = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(here, 'slack_bot_token')
    try:
        with open(fname, 'rt') as fh:
            token = fh.read().strip()
        return token
    except IOError:
        logger.error('Could not read Slack token from %s.' % fname)
        return None


def decode_indra_stmts(stmts_json_str):
        stmts_json = json.loads(stmts_json_str)
        stmts = stmts_from_json(stmts_json)
        return stmts

def print_json(js):
        s = json.dumps(js, indent=1)
        print(s)


bsi = BSI('localhost')

