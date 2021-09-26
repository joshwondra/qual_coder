function show_filename(input_id, span_id) {
    var filename = document.getElementById(input_id).value;
    filename = filename.split('\\').pop().split('/').pop();
    if (filename) {
        document.getElementById(span_id).innerHTML = filename;
    }
}

function submit_codes(direction) {
    var direction = direction;
    document.code_form.submit_codes.value = direction;
    document.code_form.submit();
}