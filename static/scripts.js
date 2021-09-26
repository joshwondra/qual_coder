function show_filename(input_id, span_id) {
    var filename = document.getElementById(input_id).value;
    filename = filename.split('\\').pop().split('/').pop();
    if (filename) {
        document.getElementById(span_id).innerHTML = filename;
    }
}

function submit_form(form_id, submit_name, submit_value) {
    var my_form = document.getElementById(form_id);
    var my_submit = document.getElementById(submit_name);
    var submit_value = submit_value;
    my_submit.value = submit_value;
    my_form.submit();
}