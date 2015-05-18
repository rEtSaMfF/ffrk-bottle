function inspect_formatter(value, row, index) {
    if ("search_id" in row) {
        return '<a href="/'+row["search_id"]+'"><span class="glyphicon glyphicon-zoom-in" aria-hidden="true"></span><span class="sr-only">Inspect</span></a>';
    }
}
