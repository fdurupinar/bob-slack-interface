import os
import sys

import json

import select

import datetime
import socket

from slackclient import SlackClient
from kqml import *


logger = logging.getLogger('bob_slack')

user_cache = {}
channel_cache = {}

CWC_CHANNEL_ID = 'GDR5M1A6N'
BOB_CHANNEL_ID = 'DDQMJE47R' # bob-funda channel id

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

        # self.channel = "cwc"
        self.channel = BOB_CHANNEL_ID # default channel when we startup bob
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

                        if res and res!= -1:
                            (self.channel, msg, self.user_id) = res
                            print("message " + msg + " " + self.user_id)
                            # if  self.channel == 'DDQMJE47R' and self.user_id != 'UDPH2QM27': # automatically sends to CwC channel
                            #     ts = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
                            #     self.logf.write('%s\t%s\t%s\t' % (msg, self.user_id, ts))
                            #     msg = msg.replace('<'+ self.user_id +'>', '').strip()
                            #     msg = msg.replace('’', '\'')
                            #     print(msg)
                            #     self.send_to_bob(msg)
                            # elif
                            if self.bob_slack_id in msg:
                                msg = msg.replace(self.bob_slack_id, '').strip()
                                # For some reason on Mac we get Mac quotes that we replace
                                msg = msg.replace('’', '\'')
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
        try:
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
        except:
            self.send_message(self.sc, self.channel, data)
            return

        if content.head().lower() == 'spoken':
            spoken_phrase = self.get_spoken_phrase(content)
            # self.bob_to_sbgn_say(spoken_phrase)
            self.send_message(self.sc, self.channel, spoken_phrase)

        elif content.head().lower() == 'display-image':
            image_type = content.gets('type')
            path = content.gets('path')
            self.bob_show_image(path, image_type)
        elif content.head().lower() == 'add-provenance':
            html = content.gets('html')
            self.send_message(self.sc, self.channel, html)

    def send_to_bob(self, comment):
        print("sending to bob " + comment)
        # Convert comment into kqml message format and send it to bob
        if comment == 'reset':
            msg = '(tell :content (start-conversation))'
            self.socket_b.sendall(msg.encode('utf-8'))
        elif comment == 'help':
            self.send_message(self.sc, self.channel, "Go to https://github.com/fdurupinar/bob-slack-interface/blob/master/README.md to see a list of questions you can ask me." )
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



            # user_name = self.get_user_name(sc, user)
            # channel_name = self.get_channel_name(sc, channel)


            logger.info('Message received : %s' %
                        (msg))

            return (channel, msg, user)

        return None


    def send_message(self, sc, channel, msg):
        # msg.replace('&','&amp;')
        # msg.replace('<', '&lt;')
        # msg.replace('>', '&gt;')


        msg = msg.replace("<ul>", "")
        msg = msg.replace("<li>", " (o) ")
        msg = msg.replace("</li>", "")
        msg = msg.replace("</ul>", "")


        sc.api_call("chat.postMessage",
                    channel=channel,
                    text=msg, as_user=True, mrkdwn=False,)
        logger.info('Message sent: %s' % msg)



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



bsi = BSI('localhost')
# bsi = BSI('35.192.108.199')

