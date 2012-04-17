function showGenericRelatedObjectLookupPopup(link) {
    var select_id = link.id.replace(/^lookup_/, '').replace(/_1$/, '_0');
    var select = document.getElementById(select_id);
    var select_text = select.options[select.selectedIndex].text; 
    var app_module = select_text.match(/(^\w+|\w+$)/g);
    if (app_module == null) { return false; }
    var url = "../../../" + app_module[0] +'/'+ app_module[1] + '/';
    if (url != undefined) { 
        link.href = url; 
        return showRelatedObjectLookupPopup(link); 
    } 
    return false; 
} 
