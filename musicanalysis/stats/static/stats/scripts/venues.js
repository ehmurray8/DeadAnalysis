let artist = document.getElementById('current-artist');
artist = artist.innerText;
artist = encodeURIComponent(artist);
$.get("/stats/" + artist + "/venue-locations", function (data, status) {
    if (status === "success") {
        let response = JSON.parse(data);
        let locations = response["locations"];

        let map = new google.maps.Map(document.getElementById('venue-map'), {
            zoom: 3,
            center: new google.maps.LatLng(39.8333, -98.5855),
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });

        let infoWindow = new google.maps.InfoWindow();
        let marker, i;
        let markers = [];
        for (i = 0; i < locations.length; i++) {
            marker = new google.maps.Marker({
                position: new google.maps.LatLng(locations[i][1], locations[i][2]), map: map
            });
            markers[i] = marker;

            google.maps.event.addListener(marker, 'click', (function (marker, i) {
                return function () {
                    infoWindow.setContent(locations[i][0]);
                    infoWindow.open(map, marker);
                }
            })(marker, i));
        }
        //var markerCluster = new MarkerClusterer(map, markers, {imagePath: '/stats/static/images/markers'});
        new MarkerClusterer(map, markers,
                {
                    imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
                    maxZoom: 7
                });
    }
});