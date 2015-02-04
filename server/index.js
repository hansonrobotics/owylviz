var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io');
io = io.listen(http);

__dirname += '/public';

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html')
});

app.get('/tree/*', function(req, res){
  res.sendFile(__dirname + '/tree.html');
});

var trees = {};

//Connection from owylviz
io.of('/accept').on('connection', function(socket) {
  var room;
  socket.on('introduce', function(_room, structure) {
    room = _room;
    trees[room] = structure;
    display.in(room).emit('tree', structure);
  });
  socket.on('step', function(id) {
    display.in(room).emit('step', id);
  });
  socket.on('disconnect', function() {
    delete trees[room];
  });
});

//Connection from browser
var display = io.of('/display').on('connection', function(socket){
  socket.on('join room', function(room) {
    socket.join(room);
    socket.emit('tree', trees[room]);
  });
});

app.set('port', (process.env.PORT || 3000))
http.listen(app.get('port'), function(){
  console.log('listening on *:' + app.get('port'));
});
