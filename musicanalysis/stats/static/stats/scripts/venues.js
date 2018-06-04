var artist = document.getElementById('current-artist');
artist = artist.innerText;
artist = encodeURIComponent(artist);
$.get("/stats/" + artist + "/locations", function (data, status) {
    if (status === "success") {
        var response = JSON.parse(data);
        var locations = response["locations"];

        var map = new google.maps.Map(document.getElementById('venue-map'), {
            zoom: 3,
            center: new google.maps.LatLng(39.8333, -98.5855),
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });

        var infowindow = new google.maps.InfoWindow();
        var marker, i;
        var markers = [];
        for (i = 0; i < locations.length; i++) {
            marker = new google.maps.Marker({
                position: new google.maps.LatLng(locations[i][1], locations[i][2]), map: map
            });
            markers[i] = marker;

            google.maps.event.addListener(marker, 'click', (function (marker, i) {
                return function () {
                    infowindow.setContent(locations[i][0]);
                    infowindow.open(map, marker);
                }
            })(marker, i));
        }
        //var markerCluster = new MarkerClusterer(map, markers, {imagePath: '/stats/static/images/markers'});
        var markerCluster = new MarkerClusterer(map, markers,
            {imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'});
    }
});