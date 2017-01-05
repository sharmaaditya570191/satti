var socket = new Backbone.WS("ws://" + window.location.host);

var ChatRoom = Backbone.Model.extend({
	urlRoot: '/chat'
	defaults: {
		id: -1,
		name: '',
		messages: new MessageList(),
		typed : ''
	}
})

var ChatRoomList = Backbone.Collection.extend({
	model: Chatroom
})

var Message = Backbone.Model.extend({
	defaults: {
		text: '',
		author: '',
		time: ''
	}
})

var MessageList = Backbone.Collection.extend({
	model: Message
})

// View for items in the sidebar chat list
var ChatRoomView = Backbone.View.extend({

})

// View for rendering messages
var MessageView = Backbone.View.extend({

})
// The dispatcher listens to WS, works out message type and content,
// and triggers the right event on the corresponding ChatRoom
var Dispatcher = Backbone.Model.extend({
	defaults: {
		rooms = new ChatRoomList();
	}
})

// Main view
var App = Backbone.View.extend({
	el: $("#content"),

	initialize: function(){

	}
})