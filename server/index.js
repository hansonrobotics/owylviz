//Copyright (c) 2013-2018 Hanson Robotics, Ltd.
var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io');
io = io.listen(http);

var trees = {};

//Connection from browser at home
var statusio = io.of('/status').on('connection', function(socket){
  socket.emit('rooms', Object.keys(trees));
});

//Connection from browser at some tree page
var displayio = io.of('/display').on('connection', function(socket){
  socket.on('join room', function(room) {
    socket.join(room);
    socket.emit('tree', trees[room]);
  });
});

//Connection from owylviz
io.of('/accept').on('connection', function(socket) {
  var room;

  socket.on('introduce', function(_room, structure) {
    room = _room;
    trees[room] = structure;
    displayio.in(room).emit('tree', structure);
    statusio.emit('rooms', Object.keys(trees));
  });

  socket.on('step', function(id, yieldval) {
    displayio.in(room).emit('step', id, yieldval);
  });

  socket.on('disconnect', function() {
    //delete trees[room];
    //statusio.emit('rooms', Object.keys(trees));
  });

});


__dirname += '/public';

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html')
});

app.get('/*.json', function(req, res){
  res.sendFile(__dirname + '/' + req.params[0] + '.json')
});

app.get('/*', function(req, res){
  res.sendFile(__dirname + '/tree.html');
});

app.set('port', (process.env.PORT || 3000))
http.listen(app.get('port'), function(){
  console.log('listening on *:' + app.get('port'));
});
