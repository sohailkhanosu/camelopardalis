document.addEventListener('DOMContentLoaded', function(evt) {
    var textArea = document.getElementById('ws-messages');      
    var ws = new WebSocket('ws://' + location.host);
    ws.addEventListener('open', function () {
        ws.addEventListener('message', function (evt) {
            var data = evt.data;
            textArea.value += '\n' + evt.data;
        });
    });
});
