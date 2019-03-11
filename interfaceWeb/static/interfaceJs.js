

$(document).ready(function(){
	namespace = '/interface'; // change to an empty string to use the global namespace

            // the socket.io documentation recommends sending an explicit package upon connection
            // this is specially important when using the global namespace
            var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

            // manejador de mensajes respuesta
            socket.on('my response', function(msg) {
                $('#log').text(msg.data).html();
                $('#mensaje-info').removeClass('alert-off');
                $('#mensaje-info').fadeIn(200).addClass('alert-on');
                $('input[type="submit"]').prop('disabled', true);
                //$('#mensaje-info').animate('alert-on');
                $( "#mensaje-info" ).animate({
                    opacity: 0,
                    /*position:
                    top: "-=50",
                    display: "block",*/
                  }, 1800, function() {
                    // Animation complete.
                    $('#mensaje-info').removeClass('alert-on');
                    $('#mensaje-info').addClass('alert-off');
                    $('#mensaje-info').css("opacity","1");
                    $('input[type="submit"]').prop('disabled', false);
                  });
                if (msg.data.substring(0, 2) == "El"){
                    location.reload(true);
                }
            });

            /*$('form .boton-funciones').submit(function() {
                //socket.emit('my event', {data: {idPadreFun : $('[name=idPadreFun]').val(), nomFun : $('[name=nomFun]').val()}});
                return false;
            });
            $('form .').submit(function(){return false;});*/


            $('form#emit').submit( function(event) {
                socket.emit('my event', {data: {idPadreFun:$(this).find("[name=idPadreFun]").val(),nomFun:$(this).find("[name=nomFun]").val()}});
                return false;
            });

        });