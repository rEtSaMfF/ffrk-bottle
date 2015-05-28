function inspect_formatter(value, row, index) {
    if ("search_id" in row) {
        return '<a href="/'+row["search_id"]+'"><span class="glyphicon glyphicon-zoom-in" aria-hidden="true"></span><span class="sr-only">Inspect</span></a>';
    }
}

function calculate_damage(atk, def, physical, boost) {
    var damage = 0;
    var tmp = 0;
    if (physical) {
        tmp = Math.pow(atk, 1.3);
        if (tmp > 2000)
            damage = 2000 * Math.pow(atk, 0.5) / Math.pow(def, 0.5);
        else
            damage = Math.pow(atk, 1.8) / Math.pow(def, 0.5);
        if (boost)
            damage *= 1.5;
        return Math.floor(damage);
    }
    tmp = Math.pow(atk, 1.15);
    if (tmp > 2000)
        damage = 2000 * Math.pow(atk, 0.5) / Math.pow(def, 0.5);
    else
        damage = Math.pow(atk, 1.65) / Math.pow(def, 0.5);
    if (boost)
        damage *= 1.5;
    return Math.floor(damage);
}

function set_damage() {
    var atk = $("#attack").val();
    var def = $("#defense").val();
    $("#p-damage").val(calculate_damage(atk, def, true));
    $("#b-damage").val(calculate_damage(atk, def, true, true));
    $("#m-damage").val(calculate_damage(atk, def, false));
}

$(function () {
    $('[data-toggle="tooltip"]').tooltip()
});
