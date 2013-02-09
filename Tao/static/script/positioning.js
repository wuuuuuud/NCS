
function getPosition(eventObj, contentObj, docObj, winObj)
{
    
    var timestamp = (new Date()).valueOf();
    var event = eventObj;
    var eventY = event.clientY;
    var eventX = event.clientX;
    var t = event.target;
    var r = docObj.createRange();
    var s;
    if (t.nodeName == "DIV") return { "offset": null, "object": null };
    while (t.nodeName != "P") {
        t = t.parentNode;
    }
    t.normalize();
    last = new Array(0, 0);
    var outOfRange = false;
    var tl = t.textContent.length;//text length
    var jjdown = 0;
    var jup = new Array();
    var jdown = new Array();
    var jjup = tl;
    {
        var q = insertAfterText(t, 0);
        jdown.push(getAbsoluteLeft(q));
        jdown.push(getAbsoluteTop(q));
        if (event.clientY <= jdown[1] && event.clientX <= jdown[0]) outOfRange = true;
        cleanning(q);
    }
    {
        var q = insertAfterText(t, tl);
        jup.push(getAbsoluteLeft(q));
        jup.push(getAbsoluteTop(q));
        if (event.clientY > jup[1]) outOfRange = true;
        cleanning(q);
    }

    if (DEBUG) {
        $DEBUG.innerHTML = "循环开始前<br />";
        $DEBUG.innerHTML += "cursor's position<br />X:" + eventX;
        $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + eventY + "<br />";

        $DEBUG.innerHTML += "former's position:<br />X:" + (jdown[0]);
        $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + (jdown[1]);
        $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Num:" + jjdown + "<br />";


        $DEBUG.innerHTML += "latter's position:<br />X:" + (jup[0]);
        $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + (jup[1]);
        $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Num:" + jjup + "<br />";
    }

    direction = 0.7;
    var baseline = jup[1]; //baseline ,if the marker span's Y on screen is larger than baseline,the marker is beyond the cursor 
    if (!outOfRange)//if the cursor is in front of the top marker or behind the aftermost marker ,just jump out
    {
        var loopCount = 0;
        for (j = Math.floor(tl / 2) ; ;) {
            var q = insertAfterText(t, j);
            if (DEBUG)//clean the output div every loop
            {
                $DEBUG.innerHTML = "第" + loopCount + "次循环<br />";
                $DEBUG.innerHTML += "cursor's position<br />X:" + eventX;
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + eventY + "<br />";

                $DEBUG.innerHTML += "marker's position:<br />X:" + (getAbsoluteLeft(q));
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + (getAbsoluteTop(q));
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Num:" + j + "<br />";


                $DEBUG.innerHTML += "former's position:<br />X:" + (jdown[0]);
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + (jdown[1]);
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Num:" + jjdown + "<br />";


                $DEBUG.innerHTML += "latter's position:<br />X:" + (jup[0]);
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Y:" + (jup[1]);
                $DEBUG.innerHTML += "&nbsp;&nbsp;&nbsp;&nbsp;Num:" + jjup + "<br />";
            }
            loopCount++;
            if ((getAbsoluteTop(q)) >= eventY)//更新baseline
            {
                baseline = (baseline < (getAbsoluteTop(q))) ? baseline : getAbsoluteTop(q);
                if (DEBUG) $DEBUG.innerHTML += "baseline:" + baseline.toString() + "<br />";
            }


            if (((getAbsoluteLeft(q) > event.clientX && ((getAbsoluteTop(q) >= eventY) || jup[1] == jdown[1])) || getAbsoluteTop(q) > baseline)) {
                if (j <= (tl)) {
                    jjup = j;
                    jup[0] = getAbsoluteLeft(q);
                    jup[1] = getAbsoluteTop(q);
                    j = Math.floor((jjdown + j) / 2);
                    if (DEBUG) $DEBUG.innerHTML += "判定超出<br />";

                }
                else {
                    outOfRange = true;
                    if (DEBUG) $DEBUG.innerHTML += "超出最大值<br />";
                    break;
                }

            }
            else if ((((getAbsoluteLeft(q) < event.clientX) && (jup[1] == jdown[1]))) || (getAbsoluteTop(q) < event.clientY)) {
                if (j == 0) {
                    if (DEBUG) $DEBUG.innerHTML += "marker before cursor yet j=0<br />";
                }
                else {
                    jjdown = j;
                    jdown[0] = getAbsoluteLeft(q);
                    jdown[1] = getAbsoluteTop(q);
                    j = Math.ceil((j + jjup) / 2);
                    if (DEBUG) $DEBUG.innerHTML += "marker before cursor j!=0<br />next j's num:" + j + "<br />";
                }
            }

            else {
                if ((getAbsoluteTop(q)) == jdown[1]) {
                    jjdown = j;
                    jdown[0] = getAbsoluteLeft(q);
                    jdown[1] = getAbsoluteTop(q);
                    j = Math.ceil((j + jjup) / 2);
                    if (DEBUG) $DEBUG.innerHTML += "position cannot be decided,yet marker and latter are in the same line <br />";
                }


                else {
                    if (direction > 0.5) {
                        j = Math.floor((j * 0.3 + jjdown * 1.7) / 2);
                    }
                    else {
                        j = Math.ceil((j * 0.3 + jjup * 1.7) / 2);
                    }
                }

            }

            last[0] = getAbsoluteLeft(q);
            last[1] = getAbsoluteTop(q);
            cleanning(q);
            if ((jjup - j) <= 0 && (jjup - jjdown) > 1) {
                jjdown = Math.floor((jjdown + jjup) / 2);

                var q = insertAfterText(t, jjdown);
                jdown[0] = getAbsoluteLeft(q);
                jdown[1] = getAbsoluteTop(q);
                cleanning(q);
                j = Math.floor((jjup + jjdown) / 2);
                direction = 1 - direction;
                var q = insertAfterText(t, j);
                if (DEBUG) $DEBUG.innerHTML += "turn around+<br/>";
            }
            if ((jjup - jjdown) <= 1) {
                if (jjup == 1 || jjdown == (tl - 1)) {
                    var q = insertAfterText(t, 0);
                    if (getAbsoluteLeft(q) > event.clientX && jjup == 1) {
                        outOfRange = 1;

                        break;
                    }
                    cleanning(q);
                    var q = insertAfterText(t, jjup);
                    if (getAbsoluteLeft(q) < event.clientX && jjup == tl) {
                        outOfRange = 1;
                        if (DEBUG) alert("right out");
                        break;
                    }
                    cleanning(q)
                }


                j = jjup;
                var q = insertAfterText(t, j - 1);
                last[0] = getAbsoluteLeft(q);
                last[1] = getAbsoluteTop(q);
                cleanning(q);
                var q = insertAfterText(t, j);
                break;
            }
            if ((j - jjdown) <= 0 || (jjup - j) <= 0) {
                direction = 1 - direction;

            }
            if (DEBUG) alert("continue");
            if ((new Date()).valueOf() - timestamp > 2000) {
                alert("time out");
                outOfRange = true;
                break;
            }
        }
    }
    else {
        q = insertAfterText(t, 0);
        if (DEBUG) $DEBUG.innerHTML += "before first or after last<br />";
    }
    if ((getAbsoluteTop(q)) > baseline) outOfRange = 1;
    if (outOfRange)
    {
        cleanning(q);
        return {"offset":null,"object":null}
    }
    else
    {
        cleanning(q);
        return { "offset": jjup, "object": t }
    }
}

function treelize(object) {
    
    //alert(object.getAttribute("id"));
    if (!object.getAttribute("id"))
    {
        object.setAttribute("id", "C"+Math.round(Math.random("1")*10000000));
    }
    if (treelizeCache.hasOwnProperty(object.getAttribute("id")) && NEW) {
        return treelizeCache[object.getAttribute("id")];
    }
    else {
        var ch = object.childNodes;
        var l = ch.length;
        var array = new Array();
        for (i = 0; i <= l - 1; i++) {
            array.push(ch[i]);
        }
        for (i = 0; i <= (array.length - 1) ; i++) {
            if (array[i].nodeName != "#text") {
                var tarray = new Array();
                for (k = 0; k <= (array[i].childNodes.length - 1) ; k++) {
                    tarray.push(array[i].childNodes[k]);
                }
                var farray = new Array();
                var barray = new Array();
                if (i != 0) {
                    farray = array.slice(0, i);
                }
                if (i <= (array.length - 2)) {
                    barray = array.slice(i + 1);
                }
                array = farray.concat(tarray.concat(barray));
                i--;
            }
        }
        var array_d = new Array();
        for (t = 0; t <= array.length-1; t++)
        {
            array_d.push(array[t]);
        }
        treelizeCache[object.getAttribute("id")]=array_d;
        return array;
    }
}
function lenlize(a) {
    var b = new Array();
    for (i = 0; i <= a.length - 1; i++) {
        b.push(a[i].length);
    }
    return b;
}
function insertAfterText(object, offset) {
    while ($(".marker").length != 0) cleanning($(".marker")[0]);
    var a = treelize(object);
    var alength = lenlize(a);
    var accumlatedLength = 0;
    var j = 0;
    var spann = document.createElement("SPAN");
    spann.setAttribute("class", "marker");
    spann.setAttribute("style", "display:inline-block;height:0 px;");

    //var hl2 = document.getElementById("highlighter2");
    var totalLength=0;
    for (var i=0;i<=alength.length-1;i++)
    {
        totalLength+=alength[i];
    }
    while ((accumlatedLength + alength[j]) <= offset && (accumlatedLength + alength[j])!=totalLength) {
        accumlatedLength += alength[j];
        j++;

    }
    var newOffset = offset - accumlatedLength;
    var latterText = a[j].splitText(newOffset);
    latterText.parentNode.insertBefore(spann, latterText);
    //alert(spann.offsetLeft);
    //hl2.style.left = spann.offsetLeft.toString() + "px";
    //hl2.style.top = (spann.offsetTop - window.scrollY).toString() + "px";
    //if (!DEBUG) hl2.style.visibility = "hidden";
    if (newOffset == 0) treelize(object)[j] = spann.nextSibling;
    return spann;
}
function cleanning(o) {
    var op = o.parentNode;
    op.removeChild(o);
    
    o.remove();
    op.normalize();
}
function initialize()
{
    contentDOM = $(content)[0];
    if (DEBUG) {
        $DEBUG = document.createElement("DIV");
        document.body.insertBefore($DEBUG);
        $DEBUG.setAttribute("id", "debug");
        $DEBUG.setAttribute("style", "position:fixed;width:500px;top:200px;right:0%;border:1px solid gold;");
    }

    var d = document;
    var direction = 0.7;
    
    


    //contentDOM.addEventListener("mouseup", f, false);

    contentDOM.addEventListener(DEBUG ? "click" : "mousemove", onContentMouseMove
    , false);

    contentDOM.addEventListener("mousedown", function (event) {
        contentDOM.removeEventListener("mousemove", onContentMouseMove);
    });
    contentDOM.addEventListener("mouseup", onContentMouseUp);
    
    contentDOM.addEventListener("click", onContentClick);
    paragraphs=contentDOM.firstChild.getAttribute("id");
    for (i = 1;i<=contentDOM.childNodes.length-1;i++)
    {
        paragraphs+="#_#"+contentDOM.childNodes[i].getAttribute("id");
    }
    json = $.ajax({
        "url": "/get/multiply/comment/",
        "type": "POST",
        "data":"paragraphList="+paragraphs,
    })
        .done(function (data) {
        commentList = jQuery.parseJSON(data);
        ajaxData = data;
    });

}
function onContentMouseMove(event)
{
    if (document.getSelection(0).toString() == "") {
        var timestamp = (new Date()).valueOf();//time record;
        var result = getPosition(event, $(content)[0], document, window);
        if (result["offset"] != null) {
            var offset = result["offset"];
            var paraid = result["object"].getAttribute("id");

            $(indicator)[0].innerHTML = offset + "<br/>" + paraid;
            commentList.forEach(function (value, key) {
                if (value.relatedNodes.hasObject(paraid)) {
                    if (value.firstNode == paraid) {
                        if (value.lastNode == paraid) {
                            if (offset > value.startOffset && offset < value.endOffset) {
                                showComment(value);
                            }
                        }
                        else {
                            if (offset > value.startOffset) {
                                showComment(value);
                            }
                        }
                    }
                    else if (value.lastNode == paraid) {
                        if (offset < value.endOffset) {
                            showComment(value);
                        }
                    }
                    else {
                        showComment(value);
                    }
                }
            });

            $(indicator)[0].innerHTML += "<br />" + ((new Date()).valueOf() - timestamp) + "<br />"; //time
        }
        
    }

}
function showComment(value)
{
    indicator.innerHTML += value.content + "<br />";
    value["show"] = true;
    //value["beginning"] = document.createElement("DIV");
    //_b = value.beginning;
    //_b.setAttribute("style","position:absolute;")

}
function getAbsoluteLeft(o)
{
    var _r = 0;
    do {
        _r += o.offsetLeft;
        var o = o.offsetParent;
    } while (o != document.body);
    return _r - window.scrollX;
}
function getAbsoluteTop(o)
{
    var _r = o.offsetHeight;
    do {
        _r += o.offsetTop;
        var o = o.offsetParent;
    } while (o != document.body);
    return _r - window.scrollY;
}
function onContentMouseUp(event)
{
    contentDOM = $(content)[0];
    contentDOM.addEventListener("mousemove", onContentMouseMove);
    
    var c = document.getSelection().getRangeAt(0);
    var g = document.getSelection().getRangeAt(0);
    var p = document.getElementById("indicator");
    var sc = c.startContainer;
    var ec = c.endContainer;
    Adc = $(AddComment)[0];

    p.innerHTML = c.toString() + "<br />length:" + c.toString().length;
    var j = c.startContainer;
    while (j.nodeName != "P" && j.nodeName!="DIV") {
        j = j.parentNode;
    }
    var i = j;
    c.collapse(true);
    c.setStart(j, 0);
    Adc.startOffset.value = c.toString().length;
    Adc.startNode.value = j.getAttribute("id");
    p.innerHTML = p.innerHTML + "<br/> start true offset:" + c.toString().length;
    g.collapse(false);
    j = ec;
    while (j.nodeName != "P" && j.nodeName != "DIV") {
        j = j.parentNode;
    }
    g.setStart(j, 0);
    Adc.endOffset.value = g.toString().length;
    Adc.endNode.value = j.getAttribute("id");
    p.innerHTML = p.innerHTML + "<br/>end true offset:" + g.toString().length;
    Adc.relatedNodes.value = i.getAttribute("id")
    
    while(i!=j)
    {
        i = i.nextSibling;
        Adc.relatedNodes.value += "#_#" + i.getAttribute("id");
        
    }
    
}
function onContentClick(event)
{
    var t = event.target;
    while (t.nodeName != "P") t = t.parentNode;
    var key = t.id;
    DivUP.style.visibility = "visible";
    DivUP.style.left = "0 px";
    DivUP.style.top = (100 + window.scrollY) + "px";
    UpdateParagraph.key.value = key;
    UpdateParagraph.content.innerHTML = t.innerHTML;


}
function sendComment(self)
{
    var ajaxBody;
    var requestData="";
    var data=AddComment.childNodes;
    for (var i=0;i<=data.length-1;i++)
    {
        if (data[i].nodeName == "#text")
        {
            ;
        }
        else if (data[i].getAttribute("type") == "hidden")
        {
            requestData+=data[i].getAttribute("name")+"="+data[i].getAttribute("value")+"&";
        }
        else if(data[i].nodeName=="TEXTAREA")
        {
            requestData+=data[i].getAttribute("name")+"="+data[i].value+"&";
        }
    }
    //alert(requestData);
    var ajaxRequest=$.ajax({
        "url": "/add/comment",
        "method": "POST",
        "data": requestData,
    })
        .done(function (data) {
            alert("批注成功");
            commentList.push(jQuery.parseJSON(data));

        })
        .fail(function () { alert("failed"); });
}
function updateParagraph(self)
{
    var ajaxBody;
    var requestData = "";
    var data = UpdateParagraph.childNodes;

    requestData = jQuery(UpdateParagraph).serialize();
    //alert(requestData);
    var ajaxRequest = $.ajax({
        "url": "/update/paragraph",
        "method": "POST",
        "data": requestData,
    })
        .done(function (data) {
            document.getElementById(UpdateParagraph.key.value).innerHTML = data;
            NEW = true;
            treelize(document.getElementById(UpdateParagraph.key.value));
            NEW = false;
        })
        .fail(function () { alert("failed"); });
}
Array.prototype.hasObject = (
  !Array.indexOf ? function (o)
  {
      var l = this.length + 1;
      while (l -= 1)
      {
          if (this[l - 1] === o)
          {
              return true;
          }
      }
      return false;
  } : function (o)
  {
      return (this.indexOf(o) !== -1);
  }
);
var DEBUG = false;
var commentList = [];
var paragraphs;
var ajaxData;
var json;
var GLOBAL = {};
var contentDOM;
var treelizeCache = {};
var NEW = true;
$(document).ready(initialize)