from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import ChatMessage, ChatRoom, ChatUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .forms import ImageUploadForm, RoomCreationForm
from django.utils import timezone
import os.path

def get_chatuser(user):
	return ChatUser.objects.get(user=user)

@login_required
def chat(request, id):
	room = ChatRoom.objects.get(pk=id)
	return render(request, 'templates/new_chat.html', context = {
		'id': room.pk,
		'room_name': room.name,
		'messages': ChatMessage.objects.filter(room=room),
		'users': room.users.all(),
		})

def private_chat(request, username):
	names = ["Private chat between {} and {}".format(request.user.username, username),
			"Private chat between {} and {}".format(username, request.user.username)]
	if not ChatRoom.objects.filter(name__in=names).exists():
		create_private_chat(request, username)
	room = ChatRoom.objects.get(name=name)
	return render(request, 'templates/new_chat.html', context = {
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
	return render(request, 'templates/newest_index.html', context = {
		"rooms": request.user.chatuser.chatrooms.all()
		})

def login(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if user is not None:
		auth_login(request, user)
	else:
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
		"in_room": in_room
		}
	return render(request, 'templates/chatroom.html', context = {**context, 
		**stats})

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
			creator = get_chatuser(request.user)
			new_room = ChatRoom.objects.create(name=form.cleaned_data['name'],
				description=form.cleaned_data['description'],
				creator=creator)
			new_room.users.add(creator)
			creator.chatrooms.add(new_room)
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
	joinable_rooms = ChatRoom.objects.exclude(users=request.user.chatuser)
	return render(request, "templates/join_chatroom.html", {"joinable_rooms": joinable_rooms})