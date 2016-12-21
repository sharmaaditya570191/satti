from channels import Group
from .models import ChatMessage, ChatRoom, ChatUser
import json
from channels.sessions import channel_session
from channels.auth import channel_session_user, channel_session_user_from_http

# Connected to websocket.connect
@channel_session_user_from_http
def ws_add(message):
    room_id = message.content['path'].split('/')[2]
    Group("chat-%s" % room_id).add(message.reply_channel)

# Connected to websocket.receive
@channel_session_user
def ws_message(message):
    read = json.loads(message.content['text'])
    room_id = read['room']
    ChatMessage.objects.create(
    	room=ChatRoom.objects.get(pk=room_id),
    	text=read['msg'],
        author=ChatUser.objects.get(user=message.user)
    	)
    Group("chat-%s" % room_id).send({
        "text": json.dumps({
            "content": read['msg'],
            "user": message.user.username
            })
        })

@channel_session
def ws_disconnect(message):
    id = message.content['path'].split('/')[2]
    Group("chat-%s" % id).discard(message.reply_channel)