from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static


PROFILE_TEXT = "This is my profile text. Isn't it fun?"

CHATROOM_TEXT = "This is the default chatroom description. It is a bit longe"\
                "r than the default text for profiles, and that's intentional."

class ChatRoom(models.Model):
	def __str__(self):
		return self.name

	name = models.CharField(max_length=100)
	image = models.ImageField(upload_to='images/', default='images/default.jpg')
	max_users = models.PositiveSmallIntegerField(default=50)
	description = models.TextField(max_length=200, blank=True, default=CHATROOM_TEXT)
	created_at = models.DateTimeField(auto_now_add=True)
	creator = models.ForeignKey('ChatUser', null=True, related_name="created_rooms")
	admins = models.ManyToManyField('ChatUser', related_name="admin_in")
	is_private = models.BooleanField(default=False)
	users = models.ManyToManyField('ChatUser', related_name="user_in")

	def is_creator(self, chatuser):
		return self.creator == chatuser

	def is_admin(self, chatuser):
		 return self.admins.filter(pk=chatuser.pk).exists()

	def has_messages(self):
		return ChatMessage.objects.filter(room=self).exists()

	def latest_message(self):
		return ChatMessage.objects.filter(room=self).latest('created_at')

class ChatUser(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	chatrooms = models.ManyToManyField(ChatRoom, blank=True)
	image = models.ImageField(upload_to='images/', default='default.jpg')
	profile_text = models.CharField(default=PROFILE_TEXT, max_length=200)
	contacts = models.ManyToManyField("self", blank=True, related_name="contacts")

	def __str__(self):
		return self.user.username


class ChatMessage(models.Model):
	author = models.ForeignKey('ChatUser')
	room = models.ForeignKey('ChatRoom')
	text = models.TextField(max_length = 1000)
	created_at = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(blank=True)

