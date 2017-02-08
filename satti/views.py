# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import ChatMessage, ChatRoom, ChatUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.template import Context, loader
from django.template.loader import render_to_string
from .forms import ImageUploadForm, RoomCreationForm
from django.utils import timezone
import os.path
from datetime import datetime

def get_chatuser(user):
	return ChatUser.objects.get(user=user)

@login_required
def chat(request, id):
	"""
	Display individual chatroom

	**Context**

	``ìd``
		Primary key of the chatroom
		type: Int
	``room_name``
		Name of the room
		type: String
	``messages``
		Messages in the room to be rendered
		type: QuerySet[ChatMessage]

	**Template:**

	:template:`templates/chat.html`
	"""
	room = ChatRoom.objects.get(pk=id)
	return render(request, 'templates/chat.html', context = {
		'id': room.pk,
		'room_name': room.name,
		'messages': ChatMessage.objects.filter(room=room).order_by('created_at'),
		'users': room.users.all(),
		})

def json_messages(request, pk):
	chatuser = ChatUser.objects.get(user=request.user)
	room = ChatRoom.objects.get(pk=pk)
	content = {"data": []}
	if chatuser.in_room(room):
		messages = Message.objects.get(chatroom=room)
		for message in messages:
			content["data"].append({"user": message.author.user.username,
				"text": message.text, "time": iso_timestamp(message.created_at)})
	return JsonResponse(content)

def chat_list_json(request):
	chatuser = get_chatuser(request.user)
	chatrooms = chatuser.chatrooms.all()
	content = {"data": []}
	for chatroom in chatrooms:
		content["data"].append(chat_list_item(chatroom.pk, request.user))
	return JsonResponse(content)

def chat_info_json(request, id):
	return JsonResponse(chat_list_item(id, request.user))

def chat_list_item(pk, user):
	"""
	Helper function for getting contextual information about a chatroom.

	Arguments:
		pk -- room primary key (type: Int)
		user -- user (type django.auth.User)

	Return:
		A dict
	"""
	chatroom = ChatRoom.objects.get(pk=pk)
	time = list_timestamp(chatroom.modified)
	has_msg = chatroom.has_messages()
	if chatroom.is_private:
		other = chatroom.users.exclude(
			user__username=user.username).get()
		name = other.user.username
		img_url = other.image.url
		private = True
		if other.online:
			online = "online"
		else:
			online = "last seen {}".format(other.get_last_seen())
	else:
		private = False
		name = chatroom.name
		img_url = chatroom.image.url
		online_count = chatroom.users_online.count()
		if(online_count > 1):
			online = "{} users online (including you)".format(online_count)
		else:
			online = ""
	if has_msg:
		last_msg = chatroom.latest_message()
		notification = last_msg.notification
		data = {"name": name, 
			"last_msg_text": last_msg.text,
			"last_msg_time": time,
			"img_url": img_url,
			"has_msg": has_msg,
			"pk": pk,
			"online": online,
			"private": private
			}
		if notification:
			return data
		else:
			data['last_msg_author'] = last_msg.author.user.username
			return data
	else:
		return {"has_msg": has_msg, "img_url": img_url, "last_msg_time": time,
			"name": name, "online": online, "private": private, "pk": pk}

def chat_list_item_with_messages(chatroom, user):
	data = chat_list_item(chatroom.pk, user)
	data["messages"] = []
	messages = Message.objects.get(chatroom=chatroom).all()
	for message in messages:
		data["messages"].append({"user": message.author,
		"text": message.text, "time": iso_timestamp(message.created_at)})


def render_chat_list_item(request, pk):
	context = chat_list_item(pk, request.user)
	return render(request, "templates/chat_list_item.html", context)

def chat_list(request):
	chatuser = get_chatuser(request.user)
	chats = chatuser.chatrooms.all().order_by('-modified')
	chats = [chat_list_item(chat.pk, request.user) for chat in chats]
	
	return chats

def private_chat(request, username):
	names = ["Private chat between {} and {}".format(request.user.username, username),
			"Private chat between {} and {}".format(username, request.user.username)]
	if not ChatRoom.objects.filter(name__in=names).exists():
		create_private_chat(request, username)
	room = ChatRoom.objects.get(name=name)
	return render(request, 'templates/chat.html', context = {
		'id': room.pk,
		'room_name': username,
		'messages': ChatMessage.objects.filter(room=room),
		'users': room.users.all(),
		})

@login_required
def join_chatroom(request, id):
	room = ChatRoom.objects.get(pk=id)
	chatuser = get_chatuser(request.user)
	room.users.add(chatuser)
	chatuser.chatrooms.add(room)
	return HttpResponse(status=204)

@login_required
def leave_chatroom(request, id):
	room = ChatRoom.objects.get(pk=id)
	chatuser = get_chatuser(request.user)
	room.users.remove(chatuser)
	chatuser.chatrooms.remove(room)
	return HttpResponse(status=204)

@login_required
def main(request):
	chatuser = get_chatuser(request.user)
	chatuser.connect()
	chatuser.save()
	chats = chat_list(request)
	return render(request, 'templates/index.html', context = {
		"chats": chats,
		"in_chats": len(chats)>0
		})

def login(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if user is not None:
		auth_login(request, user)
	else:
		if User.objects.exists(username=username):
			return redirect('/')
		user = User.objects.create_user(username, '', password)
		chatuser = ChatUser.objects.create(user=user)
		auth_login(request, user)
	return redirect('/')

def logout(request):
	auth_logout(request)
	return redirect('/')

def profile(request, username):
	chatuser = get_chatuser(User.objects.get(username=username))
	return render(request, 'templates/profile.html', context = {
		"chatuser": chatuser,
		"username": username
		})

def chatroom(request, id):
	chatroom = ChatRoom.objects.get(pk=id)
	users = chatroom.users.all()
	chatuser = get_chatuser(request.user)
	if chatroom.is_private:
		other = chatroom.users.all().exclude(user=request.user).get()
		return profile(request, other.user.username)
	in_room = chatuser in users
	stats = chat_statistics(chatroom)
	context = {
		"is_admin": chatroom.is_admin(chatuser),
		"is_creator": chatroom.is_creator(chatuser),
		"chatroom": chatroom,
		"name": chatroom.name,
		"description": chatroom.description,
		"image": chatroom.image,
		"users": users,
		"pk": chatroom.pk,
		"in_room": in_room,
		"creator": chatroom.creator.user.username
		}
	return render(request, 'templates/chatroom.html', context = {**context, **stats})

def image(request, username):
	chatuser = get_chatuser(User.objects.get(username=username))
	image_data = open(chatuser.image.path, "rb").read()
	return HttpResponse(image_data, content_type="image/jpg")

def room_menu(request):
	return render(request, 'templates/room_menu.html', context = {
		"rooms": request.user.chatuser.chatrooms.all(),
		})

def upload_image(request):
	if request.method == "POST":
		form = ImageUploadForm(request.POST, request.FILES)
		if form.is_valid():
			chatuser = get_chatuser(request.user)
			chatuser.image = form.cleaned_data['image']
			chatuser.save()
	return HttpResponse(status=204)

def upload_chat_image(request, id):
	if request.method == "POST":
		form = ImageUploadForm(request.POST, request.FILES)
		if form.is_valid():
			chatroom = ChatRoom.objects.get(pk=id)
			chatroom.image = form.cleaned_data['image']
			chatroom.save()
	return HttpResponse(status=204)

def change_profile_text(request):
	if request.method =="POST":
		chatuser = get_chatuser(request.user)
		chatuser.profile_text = request.POST['text']
		chatuser.save()
	return HttpResponse(status=204)

def chat_statistics(chatroom):
	message_count =  ChatMessage.objects.filter(room=chatroom).count()
	user_count = chatroom.users.count()
	created_at = chatroom.created_at
	days = max((timezone.now() - created_at).days, 1)
	avg_daily_msgs = message_count / days
	return{
		"message_count": message_count,
		"chatroom_name": chatroom.name,
		"user_count": user_count,
		"created_at": created_at,
		"avg_daily_msgs": avg_daily_msgs
		}

def create_chatroom(request):
	if request.method=="POST":
		form = RoomCreationForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			creator = get_chatuser(request.user)
			new_room = ChatRoom.objects.get(name=form.cleaned_data['name'])
			new_room.users.add(creator)
			creator.chatrooms.add(new_room)
			new_room.creator = creator
			new_room.save()
			creator.save()
	return HttpResponse(status=204)

def create_private_chat(request, username):
	sender = get_chatuser(request.user)
	receiver = get_chatuser(User.objects.get(username=username))
	name = "Private chat between {} and {}".format(request.user.username, username)
	new_room = ChatRoom.objects.create(name=name)
	new_room.users.add(sender)
	new_room.users.add(receiver)
	sender.chatrooms.add(new_room)
	receiver.chatrooms.add(new_room)
	new_room.is_private = True
	new_room.save()
	sender.save()
	receiver.save()
	return HttpResponse(status=204)

def room_create_menu(request):
	form = RoomCreationForm()
	return render(request, "templates/create_chatroom.html", {"form": form})

def room_join_menu(request):
	chatuser = request.user.chatuser
	joinable_rooms = ChatRoom.objects.exclude(users=chatuser).exclude(is_private=True).exclude(banned=chatuser)
	return render(request, "templates/join_chatroom.html", {"joinable_rooms": joinable_rooms})

def iso_timestamp(time):
	return time.isoformat()[0:19].replace("T"," ")
	
def list_timestamp(time):
	today = datetime.now()
	days =(datetime.today().date() - time.date()).days
	#days = (today - time).days
	day_of_year = today.timetuple().tm_yday
	if days == 0:
		return "{}".format(time.strftime("%H:%M"))
	elif days == 1:
		return "yesterday at {}".format(time.strftime("%H:%M"))
	else:
		return time.strftime("%d.%m.%y")