function inspect_formatter(value, row, index) {
    if ("search_id" in row) {
        return '<a href="/' + row["search_id"] + '"><span class="glyphicon glyphicon-zoom-in" aria-hidden="true"></span><span class="sr-only">Inspect</span></a>';
    }
}

function get_key(obj, value) {
    // Given a json object and a value, get the key.
    // Does not work for non-unique values.
    for (i in obj) {
        if (obj[i] == value)
            return i;
    }
    // value not found in obj
    return '';
}

function super_formatter(value, row, index) {
    if (value >= 1427328000)
        return '<abbr title="' + moment.tz(value, "X", "UTC").format("LLLL z") + '" data-livestamp="' + value + '"></abbr>';

    var key = get_key(row, value);

    if (key == "name" && "search_id" in row)
        return '<a href="/' + row["search_id"] + '">' + value + '</a>';

    if (["timestamp", "opened_at", "closed_at"].indexOf(key) != -1)
        return '<abbr title="' + moment.tz(value, "UTC").format("LLLL z") + '" data-livestamp="' + value + '"></abbr>';

    if (key == "max_hp") {
        var hp = row["max_hp"];
        hp = Math.min(hp, 9999);
        var atk = calculate_atk(hp, row["defense"], true);
        var mag = calculate_atk(hp, row["defense"], false);

        return value + ' <a tabindex="0" class="btn btn-xs btn-default" role="button" data-toggle="popover" title="Physical" data-content="You need ' + atk + ' ATK in order to do ' + hp + ' damage."><span data-container="body" data-toggle="tooltip" title="You need ' + atk + ' ATK in order to do ' + hp + ' damage." class="glyphicon glyphicon-info-sign" aria-hidden="true"></span></a> <a tabindex="0" class="btn btn-xs btn-default" role="button" data-toggle="popover" title="Magical" data-content="You need ' + mag + ' MAG/MND in order to do ' + hp + ' base damage."><span data-container="body" data-toggle="tooltip" title="You need ' + mag + ' MAG/MND in order to do ' + hp + ' base damage." class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></a>';
    }

    return value;
}

function calculate_atk(hp, def, physical) {
    var atk = 0;
    var tmp = 0;
    hp = Math.min(hp, 9999);
    if (physical) {
        tmp = hp * Math.pow(def, 0.5);
        atk = Math.pow(tmp, 1/1.8);
        if (Math.pow(atk, 1.3) > 2000)
            atk = Math.pow(tmp / 2000, 1/0.5);
        return Math.ceil(atk);
    }
    tmp = hp * Math.pow(def, 0.5);
    atk = Math.pow(tmp, 1/1.65);
    if (Math.pow(atk, 1.15) > 2000)
        atk = Math.pow(tmp / 2000, 1/0.5);
    return Math.ceil(atk);
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
    $('[data-toggle="tooltip"]').tooltip();
});
