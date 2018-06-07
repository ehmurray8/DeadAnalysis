let numFinished = 0;

function progress() {
    $.get("/stats/status", function (data, status) {
        if (status === "success") {
            let response = JSON.parse(data);
            response = response["in_progress_artists"];
            response.forEach(function (percent, index) {
                index += numFinished;
                let elem = document.getElementById("add-musician-bar-" + index);
                percent = parseInt(percent);
                if (percent >= 100) {
                    elem.style.width = '100%';
                    elem.innerHTML = '100%';
                    let btn = document.getElementById("musician-button-" + index);
                    btn.style.display = "block";
                    numFinished += 1;
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
