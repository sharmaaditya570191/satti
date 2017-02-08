/*!
 * Backbone.WS
 * @version 0.4.0
 * @license BSD License (c) copyright Yehonatan Daniv
 * https://raw.github.com/ydaniv/backbone-ws/master/LICENSE
 */
(function (root, factory) {
    if ( typeof define === 'function' && define.amd ) {
        // AMD
        define(['backbone', 'underscore'], function (Backbone, underscore) {
            return factory(root, Backbone, underscore);
        });
    }
    else if ( typeof exports === 'object' ) {
        // CommonJS
        return factory(root, require('backbone'), require('underscore'));
    }
    else {
        // Browser globals
        factory(root, root.Backbone, root._);
    }
}(this, function (root, Backbone, _) {

    var ajaxSync = Backbone.sync;

    function WS (url, options) {
        if ( ! url ) {
            throw new Error('URL not provided.');
        }
        if ( ! (this instanceof WS) ) {
            return new WS(url, options);
        }

        this.options = options = options || {};
        this.routes = options.routes || {};
        this.url = url;
        this.isOpen = false;

        this.prefix = options.prefix === void 0 ?
                      'ws:' :
                      options.prefix ? options.prefix + ':' : '';
        this.typeAttribute = 'typeAttribute' in options ? options.typeAttribute : 'type';
        this.dataAttribute = 'dataAttribute' in options ? options.dataAttribute : 'data';
        this.sendAttribute = options.sendAttribute || 'send';
        this.keepOpen = ! ! options.keepOpen;
        this.debug = ! ! options.debug;
        this.useSync = ! ! options.sync;
        this.reopen = 'reopen' in options ? options.reopen : true;
        this.retries = 'retries' in options ? options.retries : 3;
        this.reopenTimeout = options.reopenTimeout ? options.reopenTimeout : 3000;
        this.expectSeconds = (options.expectSeconds || 7) * 1000;
        this.expectation = 'expect' in options ? options.expect : null;
        this.resources = [];
        this.defaultEvents = {};
        this.reopenTry = null;

        // cache retries
        this.options.retries = this.retries;

        ['open', 'message', 'close', 'error', 'noretries'].forEach(function (event) {
            this.defaultEvents[this.prefix + event] = true
        }, this);

        var resources = Array.isArray(options.resources) ? options.resources : [];

        resources.forEach(function (resource) {
            if ( Array.isArray(resource) ) {
                this.bind.apply(this, resource);
            }
            else if ( resource && resource.resource && resource.events ) {
                this.bind(resource.resource, resource.events);
            }
        }, this);

        this.open();
    }

    function Expectation (ws, expect, seconds) {
        this.instance = ws;
        this.expectation = expect === true || expect === void 0 ? ws.expectation : expect;
        this.interval = seconds ? seconds * 1000 : ws.expectSeconds;
        this._topic = ws.prefix + 'message';

        this.promise = new WS.Promise(function (resolve, reject) {
            this._handler = function (data, type) {
                if ( this.assert(data, type) ) {
                    this.kill();
                    resolve(data);
                }
            };

            ws.on(this._topic, this._handler, this);

            this.timeout_id = root.setTimeout(function () {
                reject(new Error('Timeout'));
            }, this.interval);

        }.bind(this));
    }

    Expectation.prototype.kill = function () {
        root.clearTimeout(this.timeout_id);
        this.instance.off(this._topic, this._handler);
    };

    Expectation.prototype.assert = function (data, type) {
        var exp = this.expectation,
            exp_type;

        if ( exp ) {
            exp_type = typeof exp;

            if ( exp_type == 'function' ) {
                return exp.call(this, data, type);
            }
            else if ( exp_type == 'string' ) {
                return type ? type == exp :
                       typeof data == 'string' ?
                       data == exp :
                       data[this.instance.typeAttribute] == exp;
            }

            return Object.keys(this.expectation).every(function (key) {
                return exp_type[key] === data[key];
            });
        }
        return true;
    };

    _.extend(WS.prototype, Backbone.Events, {
        open     : function () {
            this.socket = this.options.protocol ?
                          new root.WebSocket(this.url, this.options.protocol) :
                          new root.WebSocket(this.url);

            this.ready = new WS.Promise(function (resolve, reject) {
                this.socket.onopen = function () {
                    resolve(this);
                    this.onopen();
                }.bind(this);

                this.socket.onerror = function (error) {
                    reject(error);
                    this.onerror(error);
                }.bind(this);
            }.bind(this));

            this.socket.onmessage = this.onmessage.bind(this);
            this.socket.onclose = this.onclose.bind(this);
        },
        onopen   : function () {
            this.isOpen = true;
            this.retries = this.options.retries;

            if ( this.debug ) {
                console.info('$$$ OPEN');
            }

            this.trigger(this.prefix + 'open');
        },
        onmessage: function (event) {
            var base_topic = this.prefix + 'message',
                data, type;

            try {
                data = root.JSON.parse(event.data);
                type = this.typeAttribute && data[this.typeAttribute];
            }
            catch (e) {
                data = event.data;
            }

            if ( this.debug ) {
                var debug_data;
                try {
                    debug_data = root.JSON.parse(event.data);
                }
                catch (e) {
                    debug_data = event.data;
                }
                console.log('<<< RECEIVED ', debug_data);
            }

            if ( type ) {
                data = this.dataAttribute ? data[this.dataAttribute] : data;
                this.trigger(this.route(base_topic + ':' + type, data), data);
            }

            this.trigger(base_topic, data, type);
        },
        onerror  : function (error) {
            if ( this.debug ) {
                console.error('!!! ERROR ', error, this.isOpen);
            }

            this.trigger(this.prefix + 'error', error, this.isOpen);
        },
        onclose  : function (event) {
            this.isOpen = false;

            if ( this.debug ) {
                console.info('!!! CLOSED ', event);
            }

            this.trigger(this.prefix + 'close', event);

            if ( this.reopen && this.socket ) {
                if ( this.retries ) {
                    this.retries -= 1;

                    if ( this.reopenTry ) {
                        root.clearTimeout(this.reopenTry);
                    }

                    this.reopenTry = root.setTimeout(this.open.bind(this), this.reopenTimeout);
                }
                else {
                    this.trigger(this.prefix + 'noretries', event);
                }
            }
        },
        destroy  : function () {
            if ( this.reopenTry ) {
                root.clearTimeout(this.reopenTry);
            }
            this.socket && this.socket.close();
            this.socket = null;
            this.resources = [];
            this.ready = null;
        },
        send     : function (data) {
            if ( this.socket ) {
                if ( this.debug ) {
                    console.log('>>> SENT ', data);
                }

                this.socket.send(root.JSON.stringify(data));
            }
            else {
                throw new Error('WebSocket not open yet!');
            }
        },
        expect   : function (expectation, seconds) {
            return new Expectation(this, expectation, seconds);
        },
        sync     : function (method, model, options) {
            if ( options.xhr ) {
                return ajaxSync.call(Backbone, method, model, options);
            }

            var data;

            data = options.data || options.attrs || model.toJSON(options);

            if ( ! data.method ) {
                data.method = method;
            }

            if ( typeof options.beforeSend == 'function' ) {
                options.beforeSend.apply(model, arguments);
            }

            this.send(data);

            model.trigger('request', model, this.socket, options);
            // returns nothing!
        },
        route    : function (topic, data) {
            var route = this.routes[topic] || this.routes['*'];
            if ( route ) {
                return typeof route == 'function' ? route(topic, data) : route;
            }
            return topic;
        },
        bind     : function (resource, events) {
            if ( resource instanceof Backbone.Model ) {
                resource.on('destroy', this.unbind, this);
            }

            this.resources.push(resource);

            resource[this.sendAttribute] = this.send.bind(this);

            if ( this.useSync ) {
                resource.sync = this.sync.bind(this);
            }

            events = events || this.defaultEvents;

            Object.keys(events).forEach(function (event) {
                var handler = events[event];

                if ( handler === true ) {
                    handler = event;
                }
                if ( typeof handler == 'string' && typeof resource[handler] != 'function' ) {
                    handler = resource.trigger.bind(resource, handler)
                }

                resource.listenTo(this, event, handler);
            }, this);

            return this;
        },
        unbind   : function (resource) {
            resource.stopListening(this);

            resource[this.sendAttribute] = null;

            if ( this.useSync ) {
                resource.sync = ajaxSync;
            }

            this.resources.splice(this.resources.indexOf(resource), 1);

            if ( ! this.keepOpen && ! this.resources.length ) {
                this.destroy();
            }

            return this;
        }
    });

    if ( root.Promise ) {
        WS.Promise = root.Promise;
    }

    WS.Expectation = Expectation;

    Backbone.WS = WS;

    return WS;
}));
