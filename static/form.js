var adv = false;
window.onload = function(){
    var more = $('domore');
    if(more){
        more.onclick=function(){
            if(!adv){
                $('adv').style.display = '';
                more.innerHTML = "less";
                adv = true;
            } else {
                more.innerHTML = "more";
                $('adv').style.display = 'none';
                adv = false;
            }
        }
    }
}
function $(el) {
    var a = document.getElementById(el);
    if(a)
        return a;
    else
        return null;
}
function submit_form(id) {
    var candy = $('icandy');
    if (candy) {
        var field = document.createElement('IN'+"PUT");
        field.type="HID"+'DEN';
        field.name="candycode";
        field.value=id;
        candy.appendChild(field);
    }
    var mindform = document.getElementById('mindform');
    return mindform.submit();
}
