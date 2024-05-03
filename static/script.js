document.addEventListener("click", e => {

    let handle
    if (e.target.matches(".handle")) {
        handle = e.target
    } else {
        handle = e.target.closest(".handle")
    }
    if (handle != null) onHandleClick(handle)
})

const throttleProgressBar = throttle(() => {
  document.querySelectorAll(".progress-bar").forEach(calculateProgressBar)
}, 250)
window.addEventListener("resize", throttleProgressBar)

document.querySelectorAll(".progress-bar").forEach(calculateProgressBar)

function calculateProgressBar(progressBar) {

    progressBar.innerHTML = ""
    const slider = progressBar.closest(".row").querySelector(".slider")
    const itemCount = slider.children.length/3

    const itemsPerScreen = parseInt(
        getComputedStyle(slider).getPropertyValue("--items-per-screen")
    )
    let sliderIndex = parseInt(
        getComputedStyle(slider).getPropertyValue("--slider-index")
    )
    const progressBarItemCount = Math.ceil(itemCount / itemsPerScreen)

    if (sliderIndex >= progressBarItemCount) {
        slider.style.setProperty("--slider-index", progressBarItemCount - 1)
        sliderIndex = progressBarItemCount - 1
    }

    for (let i = 0; i < progressBarItemCount; i++) {
        const barItem = document.createElement("div")
        barItem.classList.add("progress-item")
        if (i === sliderIndex) {
          barItem.classList.add("active")
        }
        progressBar.append(barItem)
    }
}

function onHandleClick(handle) {

    const progressBar = handle.closest(".row").querySelector(".progress-bar")
    const slider = handle.closest(".container").querySelector(".slider")
    const sliderIndex = parseInt(
        getComputedStyle(slider).getPropertyValue("--slider-index")
    )

    const progressBarItemCount = progressBar.children.length

    if (handle.classList.contains("left-handle")) {
        if (sliderIndex - 1 < 0) {
            slider.style.setProperty("--slider-index", progressBarItemCount - 1)
            progressBar.children[sliderIndex].classList.remove("active")
            progressBar.children[progressBarItemCount - 1].classList.add("active")
        } else {
            slider.style.setProperty("--slider-index", sliderIndex - 1)
            progressBar.children[sliderIndex].classList.remove("active")
            progressBar.children[sliderIndex - 1].classList.add("active")
        }
    }

    if (handle.classList.contains("right-handle")) {

        if (sliderIndex + 1 >= progressBarItemCount) {
            slider.style.setProperty("--slider-index", 0)
            progressBar.children[sliderIndex].classList.remove("active")
            progressBar.children[0].classList.add("active")
        } else {
            slider.style.setProperty("--slider-index", sliderIndex + 1)
            progressBar.children[sliderIndex].classList.remove("active")
            progressBar.children[sliderIndex + 1].classList.add("active")
        }
    }
}

function throttle(cb, delay = 1000) {
  let shouldWait = false
  let waitingArgs
  const timeoutFunc = () => {
    if (waitingArgs == null) {
      shouldWait = false
    } else {
      cb(...waitingArgs)
      waitingArgs = null
      setTimeout(timeoutFunc, delay)
    }
  }

  return (...args) => {
    if (shouldWait) {
      waitingArgs = args
      return
    }

    cb(...args)
    shouldWait = true
    setTimeout(timeoutFunc, delay)
  }
}

function readTextFile(file)
{
    var rawFile = new XMLHttpRequest();
    rawFile.open("GET", file, false);
    rawFile.onreadystatechange = function ()
    {
        if(rawFile.readyState === 4)
        {
            if(rawFile.status === 200 || rawFile.status == 0)
            {
                var allText = rawFile.responseText;
                document.getElementById('sun_time').textContent = allText
            }
        }
    }
    rawFile.send(null);
}

function startTime(){
    var today = new Date();
    var hh = today.getHours();
    var mm = today.getMinutes();
    var ss = today.getSeconds();
    mm = checkTime(mm);
    ss = checkTime(ss);
    document.getElementById('clock').innerHTML = "Clock:\n" + hh + ":" + mm + ":" + ss;
    readTextFile("static/sun_time.dat")


    var timeoutId = setTimeout(startTime, 5000);
}

function checkTime(i){
    if(i < 10) {
        i = "0" + i;
    }
    return i;
}


var cot=0;//設置一個計數器，初始值為0；作用是用來監聽點擊切換的時候哪一個圖片應該隱藏或者顯示
var max_cot=0;
function nex(){
    if(cot<=90){
        $('.inputs input').eq(cot).animate({'margin-left':'-95vw'},500);
        cot++;
    }
}

function pre(){
    if(cot>0){
        cot--;
        $('.inputs input').eq(cot).animate({'margin-left':'0'},500);
    }
}



function play(data){

    /*alert(data );*/
    var url = "/play/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function play_playlist(data){
    /*alert(data );*/
    var url = "/play_playlist/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function play_with_refresh_page(data){
    alert(data );
    var url = "/play/" + data;
    javascript:window.location.href = url;
}

function submit_text_content(data1, data2){
    /*alert("submit_text_content")*/
    var url = "/set_text_size/" + data2;
    $.post(url, {
        /*javascript_data: data2*/
        });
    var text_speed = document.getElementById("text_speed").value;
    var text_position = document.getElementById("text_position").value;
    var text_period = document.getElementById("text_period").value;
    var url = "/set_text_speed/" + text_speed;
    $.post(url, {
        /*javascript_data: text_speed*/
        });

    var url = "/set_text_position/" + text_position;
    $.post(url, {
        /*javascript_data: text_position*/
        });

    var url = "/set_text_period/" + text_period;
    $.post(url, {
        /*javascript_data: text_period*/
        });

    var url = "/play_text/" + data1;
    $.post(url, {
        /*javascript_data: data1*/
        });
}

function submit_hdmi_in(data){
    /*var data = "hdmi_in_start"*/
    /*alert(data);*/
    var url = "/play_hdmi_in/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_cms_start(data){
    /*var data = "hdmi_in_start"*/
    /*alert(data);*/
    var url = "/play_cms/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_wifi_configure(){
    console.log(document.getElementById("wifi_bands"))
    var bands_data = document.getElementById("wifi_bands").value;
    var channels_data = document.getElementById("wifi_channels").value;
    var data = "band=" + bands_data + "_" + "channel=" + channels_data
    /*alert(data);*/
    var url = "/configure_wifi/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}


function submit_ledserver_reboot(){

    var url = "/set_ledserver_reboot_option/";
    $.post(url, {
        });
}

function submit_ledclients_reboot(){

    var url = "/set_ledclients_reboot_option/";
    $.post(url, {
        });
}

function submit_aio_reboot(){

    var url = "/set_ledserver_reboot_option/";
    $.post(url, {
        });
}

function submit_frame_brightness_option(){

    var f_br = document.getElementById("frame_brightness").value;
    var url = "/set_frame_brightness_option/" + f_br;
    $.post(url, {
        /*javascript_data: f_br*/
        });
}

function submit_repeat_option(data){
    /*alert(data);*/
    var option;
    if (data.includes("All") == true){
        option="Repeat_Random";
        /*alert(option);*/
    } else if (data.includes("Random") == true){
        option="Repeat_None";
        /*alert(option);*/
    } else if (data.includes("None") == true){
        option="Repeat_One";
    } else if (data.includes("One") == true){
        option="Repeat_All";
    }
    document.getElementById("btn_repeat").value=option;
    var url = "/set_repeat_option/" + option;
    $.post(url, {
        /*javascript_data: option*/
        });
}



function rightClick(e) {
    e.preventDefault();


    if (document.getElementById("contextMenu") .style.display == "block"){
        hideMenu();
    }else{
        var menu = document.getElementById("contextMenu")
        menu.style.display = 'block';
        menu.style.left = e.pageX + "px";
        menu.style.top = e.pageY + "px";
    }
}

function create_new_playlist(file) {
    var playlist_name=prompt('Enter new playlist name');
    if(playlist_name){
        /*alert("create new playlist :" + playlist_name);*/
        var data = "playlist_name:"+playlist_name+";file_name:"+file;
        var url = "/create_new_playlist/" + data;
        $.post(url, {
            /*javascript_data: data*/
            });
    }
}

function remove_media_file(data) {
    var url = "/remove_media_file/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}


function add_to_playlist(file, playlist) {
    var data = "playlist_name:"+playlist+";file_name:"+file;
    var url = "/add_to_playlist/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function remove_playlist(playlist) {
    /*alert("remove playlist:" + playlist)*/
    var url = "/remove_playlist/" + playlist;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function remove_file_from_playlist(playlist, file ) {
    data = "playlist:" + playlist + ";file:" + file
    /*alert("data :" + data);*/
    var url = "/remove_file_from_playlist/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_default_play_mode_option(){
    var data = document.querySelector('input[name="launch_type_switcher"]:checked').value;
}

function submit_frame_brightness_mode_option(){
    /*var frame_brightness_mode = document.querySelector('input[name="brightness_mode_switcher"]:checked').value;
    alert(frame_brightness_mode);*/

    var data = document.querySelector('input[name="brightness_mode_switcher"]:checked').value;

    /* alert("data:" + data)*/
    var url = "/set_brightness_algo/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_sleep_mode_option(){

    /*var sleep_mode = document.querySelector('input[name="sleep_mode_switcher"]:checked').value;
    alert(sleep_mode)*/

    var data = document.querySelector('input[name="sleep_mode_switcher"]:checked').value;
    alert(data);
    /* alert("data:" + data)*/
    var url = "/set_sleep_mode/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}


function submit_frame_brightness_values_option(){
    var fr_br = document.getElementById("frame_brightness").value;
    var day_mode_fr_br = document.getElementById("day_mode_frame_brightness").value;
    var night_mode_fr_br = document.getElementById("night_mode_frame_brightness").value;
    var sleep_mode_fr_br = document.getElementById("sleep_mode_frame_brightness").value;
    var data = "fr_br:" + fr_br + ";day_mode_fr_br:" + day_mode_fr_br +";night_mode_fr_br:" + night_mode_fr_br + ";sleep_mode_fr_br:" + sleep_mode_fr_br;
    /*alert("data : " + data)*/
    var url = "/set_brightness_values/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_aio_frame_brightness_values_option(){
    var fr_br = document.getElementById("frame_brightness").value;

    var data = "fr_br:" + fr_br + ";day_mode_fr_br:" + fr_br +";night_mode_fr_br:" + fr_br + ";sleep_mode_fr_br:" + fr_br;

    var url = "/set_brightness_values/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}


function submit_default_play_mode(){
    // Swal.fire('Any fool can use a computer')
    var mode = document.querySelector('input[name="launch_type_switcher"]:checked').value;
    var param = "";
    if(mode == "single_file_mode"){
        param = document.getElementById("single_file_selected").value;

        Swal.fire({
                  title: 'Single File Mode with ' + param,
                  showConfirmButton: false,
                  timer: 1500
                })
    }else if(mode == "playlist_mode"){
        param = document.getElementById("playlist_selected").value;
        if(param == ""){
            Swal.fire({
                      title: 'No Playlist Selected',
                      showConfirmButton: false,
                      timer: 1500
                    })
        }else{
            Swal.fire({
                      title: 'Playlist Mode with ' + param,
                      showConfirmButton: false,
                      timer: 1500
                    })
        }
    }

    data = mode + ":" + param
    var url = "/set_default_play_mode/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_single_file_seclectfield_option(){
    var single_file_select = document.getElementById("single_file_selected").value;

}

function submit_playlist_seclectfield_option(){
    var single_file_select = document.getElementById("playlist_selected").value;

}

function submit_target_city_option(){
    var city_select = document.getElementById("city_selected").value;
    alert(city_select);
    var url = "/set_target_city/" + city_select;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_reboot_option(){
    var data = document.querySelector('input[name="reboot_mode_switcher"]:checked').value;
    alert("Reboot Mode : " + data);
    var url = "/set_reboot_mode/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_reboot_time_option(){
    var data = document.getElementById("appt-time").value;
    alert("Reboot Time : " + data);
    var url = "/set_reboot_time/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}

function submit_sleep_time_option(){
    var sleep_start_time = document.getElementById("app-sleep-start-time").value;
    var sleep_end_time = document.getElementById("app-sleep-end-time").value;
    alert("Sleep Start Time : " + sleep_start_time);
    alert("Sleep End Time : " + sleep_end_time);
    data = sleep_start_time + ";" + sleep_end_time
    alert("data : " + data);
    var url = "/set_sleep_time/" + data;
    $.post(url, {
        /*javascript_data: data*/
        });
}
