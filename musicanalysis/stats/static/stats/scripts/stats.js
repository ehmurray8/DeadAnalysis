function progress() {
    $.get("/stats/status", function (data, status) {
        if (status === "success") {
            var response = JSON.parse(data);
            response = response["in_progress_artists"];
            response.forEach(function (percent, index) {
                let elem = document.getElementById("add-musician-bar-" + index);
                percent = parseInt(percent);
                if (percent >= 100) {
                    elem.style.width = '100%';
                    elem.innerHTML = '100%';
                    let btn = document.getElementById("musician-button-" + index);
                    btn.style.display = "block;";
                } else {
                    elem.style.width = percent + '%';
                    elem.innerHTML = percent + '%';
                }
            });
        }
        setTimeout('progress()', 3000);
    });
}
$(document).ready(function() {
    progress();
});
