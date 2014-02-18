function deleteCell(_key)
{
    d = document;
    DF = DeleteForm;
    DF.key.value = _key;
    requestData = jQuery(DF).serialize();
    var ajaxRequest = $.ajax({
        "url": "/delete/cell",
        "method": "POST",
        "data": requestData,
    })
        .done(function (data) {
            document.getElementById(_key).remove();

        })
        .fail(function () { alert("failed"); });
}

function updateCell()
{
    d = document;
    UF = UpdateForm;
    _key = UF.key;
    requestData = jQuery(UF).serialize();
    var ajaxRequest = $.ajax({
        "url": "/update/cell",
        "method": "POST",
        "data": requestData,
    })
        .done(function (data) {
            //alert("success!");
            //alert(data);
            d.getElementById(_key.value).getElementsByClassName("name")[0].innerHTML = data;

        })
        .fail(function () { alert("failed"); });
}

function showUpdateForm(_key)
{
    UF = UpdateForm; //the names are corresponding to the html
    UD = UpdateDiv;
    UF.key.value = _key;
    UD.style.visibility = "visible";

}