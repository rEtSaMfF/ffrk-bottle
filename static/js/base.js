var series_map = {
    200001: "Core",
    101001: "FF I",
    102001: "FF II",
    103001: "FF III",
    104001: "FF IV",
    105001: "FF V",
    106001: "FF VI",
    107001: "FF VII",
    108001: "FF VIII",
    109001: "FF IX",
    110001: "FF X",
    111001: "FF XI",
    112001: "FF XII",
    113001: "FF XIII",
    114001: "FF XIV",
    150001: "FFT",
};


function get_name_from_id(array, id) {
    var ret;
    $.each(array, function (i, o) {
        if (o["id"] == id) {
            ret = o["name"];
            return ret;
        }
    });
    return ret;
}

function init_abilities(u, t) {
    $.getJSON(u, function (d) {
        data = d;
        ability_costs = {}
        $.each(data["ability_costs"], function(i, o) {
            var ac = ability_costs[o["ability_id"]] || [];
            ac.push(String(o["material_id"]));
            ability_costs[o["ability_id"]] = ac;
        });

        change_rarity(current_rarity, t);
    })
        .success(function() {
            //$("#getSuccess").show();
            //window.setTimeout(function() { $("#getSuccess").hide(); }, 1500);
        })
        .error(function() {
            $("#getError").show()
        })
        .complete(function() {
            $("#getInfo").hide();
        });
}


function change_rarity(r, t) {
    current_rarity = r;

    columns = [{
        "field": "alt",
        "title": "",
    }];
    abilities = {};
    abilities_rows = [];

    // Get column names (material_name) and the correct fields by
    // material_id according to current_rarity
    $.each(data["materials"], function(i, material) {
        // If the material does not match our current_rarity continue
        if (current_rarity !== material["rarity"])
            return;

        columns.push({
            "field": material["id"],
            "title": material["name"],
            "footerFormatter": material["name"],
        });
        abilities[material["id"]] = [];
    });

    // Map the abilities to the correct column
    $.each(data["abilities"], function(i, ability) {
        // If the ability does not match our current_rarity continue
        if (current_rarity !== ability["rarity"])
            return;

        var ability_id = ability["id"];
        $.each(ability_costs[ability_id], function(j, material_id) {
            // Some 4* abilities require 5* materials
            // ie: Phoenix and Major Fire Orb
            // In that case material_id will not be in abilities
            if ($.inArray(material_id, Object.keys(abilities)) === -1)
                return;
            abilities[material_id].push(ability_id);
        });
    });

    // Convert the abilities to rows
    $.each(abilities, function(material_id1, NO) {
        row = {"alt": get_name_from_id(data["materials"], material_id1)};
        $.each(abilities, function(material_id2, ability_ids) {
            // cell is abilities which use material_id1 and material_id2
            var cell = []
            $.each(ability_ids, function(k, ability_id) {
                var ac = ability_costs[ability_id];
                if ($.inArray(material_id1, ac) != -1 && $.inArray(material_id2, ac) != -1)
                    cell.push(get_name_from_id(data["abilities"], ability_id));
            });
            row[material_id2] = cell;
        });
        abilities_rows.push(row);
    });

    // columns = [{field: material_id, title: material_name}, ]
    // abilities = {material_id1: [ability_names, ], }
    // abilities_rows = [{alt: material_name, material_id1: [], material_id2: []}, ]
    //console.log(abilities);
    //console.log(abilities_rows);

    if (!t.startsWith("#"))
        t = "#" + t;
    $(t).bootstrapTable("destroy").bootstrapTable({columns: columns, data: abilities_rows});
}


function cell_styler_ability(value, row, index) {
    console.log('1');
    var ret = {"css": {}};
    return ret;
}


function cell_formatter_ability(value, row, index) {
    console.log('2');
    return value;
}


function init_characters(u, t) {
    $.getJSON(u, function (d) {
        data = d;

        for (var i = 0; i < data.length; i++) {
            for (var j in data[i]['Abilities']) {
                for (var key in data[i]['Abilities'][j]) {
                    min_stats[key] = Math.min(min_stats[key] || Math.min(), data[i]['Abilities'][j][key]);
                    max_stats[key] = Math.max(max_stats[key] || Math.max(), data[i]['Abilities'][j][key]);
                }
            }
            data[i]["series_level"] = data[i]["level"] + 10;
            data[i]["series_defense"] = data[i]["series_def"];
            data[i]["def"] = data[i]["defense"];
            for (var j = 0; j < data[i]['Equipment'].length; j++)
                $.extend(data[i], data[i]['Equipment'][j]);
            for (var j = 0; j < data[i]['Abilities'].length; j++) {
                $.extend(data[i], data[i]['Abilities'][j]);
            }
            for (var key in data[i]) {
                if (data[i][key].constructor === Array)
                    continue;
                min_stats[key] = Math.min(min_stats[key] || Math.min(), data[i][key]);
                max_stats[key] = Math.max(max_stats[key] || Math.max(), data[i][key]);
                //if (data[i][key].constructor === Number)
                data[i]["sort-"+key] = data[i][key];
                var o = {};
                o[key] = data[i][key];
                data[i][key] = $.extend({}, o);
            }
            data[i]["sort-name"] = data[i]["name"]["name"];
            data[i]["sort-image_path"] = data[i]["buddy_id"]["buddy_id"];
        }

        if (!t.startsWith("#"))
            t = "#" + t;
        $(t).bootstrapTable("load", {data: data});
    })
        .success(function() {
            //$("#getSuccess").show();
            //window.setTimeout(function() { $("#getSuccess").hide(); }, 1500);
        })
        .error(function() {
            $("#getError").show()
        })
        .complete(function() {
            $("#getInfo").hide();
        });
}


function change_realm(r, t) {
    current_realm = r;

    // Set/reset the sort-key
    for (var i = 0; i < data.length; i++) {
        for (key in data[i]) {
            if (key.startsWith("sort-"))
                continue;
            if (key.startsWith("series_"))
                continue;
            if (!data[i][key].constructor === Number)
                continue;
            if (get_value(data[i], "series_id") === current_realm)
                data[i]["sort-"+key] = get_value(data[i], "series_"+key) || get_value(data[i], key);
            else
                data[i]["sort-"+key] = get_value(data[i], key);
        }
    }

    if (!t.startsWith("#"))
        t = "#" + t;
    $(t).bootstrapTable("load", {data: data});
}


function fraction_to_rgb(f) {
    // https://stackoverflow.com/questions/340209/generate-colors-between-red-and-green-for-a-power-meter
    // https://en.wikipedia.org/wiki/HSL_and_HSV
    f = Math.min(f, .99);
    f = Math.max(f, 0);
    var r, g, b;

    if (f < .5) {
        // red to yellow
        r = 255;
        g = Math.floor(255 * (f / .5));
    }
    else {
        // yellow to green
        r = Math.floor(255 * ((.5 - f % .5) / .5));
        g = 255;
    }
    b = 0;

    return "rgb(" + r + "," + g + "," + b + ")";
}


// m is a fraction
function rlerp(l, h, m) {
    return (m - l) / (h - l);
}

// m is a fraction
function lerp(l, h, m) {
    return (1 - m)*l + m*h;
}


function inspect_formatter(value, row, index) {
    if ("search_id" in row) {
        return '<a href="/' + get_value(row, "search_id") + '"><span class="glyphicon glyphicon-zoom-in" aria-hidden="true"></span><span class="sr-only">Inspect</span></a>';
    }
}


function get_key(obj, value) {
    // Given an Object and a value, get the key.
    // Check if the value is an Object where I have included the key
    //  as a work around.
    // TODO 2016-06-06
    // Re-factor this for the improved thing.
    // Check series_map if the value is undefined.
    if (value && value.constructor === Object) {
        var keys = Object.keys(value);
        if (keys.length === 1)
            return keys[0];
    }

    // This does not work for non-unique values.
    for (i in obj) {
        if (obj[i] === value)
            return i;
        // This might work for my work around
        if (obj[i] && obj[i].constructor === Object) {
            if (i in obj[i] && obj[i][i] === value)
                return i;
        }
    }

    // value not found in obj
    return '';
}

function get_value(obj, key, value) {
    // Given an Object and a key, get the value.
    // To work around some stuff.
    if (key === "")
        return value;

    if (!key in obj)
        return value;

    if (Object.keys(obj).indexOf(key) == -1)
        return value;

    if (obj[key].constructor === Object && key in obj[key])
        return obj[key][key];

    return obj[key];
}


function cell_styler(value, row, index) {
    // This value is what is returned by super_formatter
    var key = get_key(row, value).replace("series_", "");
    var ret = {"css":{}};

    if (current_realm === get_value(row, "series_id")) {
        ret["css"]["color"] = "cyan";
        ret["css"]["font-size"] = "110%";
        var k = "series_" + key;
        if (k in row)
            value = get_value(row, k);
    }

    if (value && value.constructor === Number) {
        var m = rlerp(min_stats[key], max_stats[key], value);
        var c = fraction_to_rgb(m);
        ret["css"]["background-color"] = c;
        ret["css"]["color"] = "black";
    }

    return ret;
}


function super_formatter(value, row, index) {
    if (value === undefined || value === null)
        return '';

    if (value >= 1427328000)
        return '<abbr title="' + moment.tz(value, "X", "UTC").format("LLLL z") + '" data-livestamp="' + value + '"></abbr>';

    var key;
    if (value.constructor === Object) {
        key = Object.keys(value)[0];
        value = value[key];
    }
    else
        key = get_key(row, value);

    // This fails for "Core" characters because "name" === "job_name"
    if ((key === "name" || key === "title") && "search_id" in row)
        return '<a href="/' + get_value(row, "search_id") + '">' + value + '</a>';

    if (key === "image_path") {
        ret = '<img src="' + value + '" alt="' + get_value(row, "name") + '" title="' + get_value(row, "name") + '" class="img-responsive center-block" style="height: 2em; width: 2em;">';
        if ("search_id" in row)
            ret = '<a href="/' + get_value(row, "search_id") + '">' + ret + '</a>';
        return ret;
    }

    if (key === "series_id")
        return series_map[value];

    // I do not know why "in" does not work here
    if (["timestamp", "opened_at", "closed_at", "kept_out_at"].indexOf(key) !== -1)
        return '<abbr title="' + moment.tz(value, "UTC").format("LLLL z") + '" data-livestamp="' + value + '"></abbr>';

    if (key === "max_hp") {
        var hp = row["max_hp"];
        hp = Math.min(hp, 9999);
        var atk = calculate_atk(hp, row["defense"], true);
        var mag = calculate_atk(hp, row["defense"], false);

        return value + ' <a tabindex="0" class="btn btn-xs btn-default" role="button" data-toggle="popover" title="Physical" data-content="You need ' + atk + ' ATK in order to do ' + hp + ' damage."><span data-container="body" data-toggle="tooltip" title="You need ' + atk + ' ATK in order to do ' + hp + ' damage." class="glyphicon glyphicon-info-sign" aria-hidden="true"></span></a> <a tabindex="0" class="btn btn-xs btn-default" role="button" data-toggle="popover" title="Magical" data-content="You need ' + mag + ' MAG/MND in order to do ' + hp + ' base damage."><span data-container="body" data-toggle="tooltip" title="You need ' + mag + ' MAG/MND in order to do ' + hp + ' base damage." class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></a>';
    }

    // We are not doing a RS comparison so just return here
    if (!window.hasOwnProperty("current_realm"))
        return value;

    // We are doing RS so set var value to the series_key
    if (current_realm === get_value(row, "series_id")) {
        var k = "series_" + key;
        if (k in row)
            return get_value(row, k);
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
    if (boost)
        atk = atk * 1.25;
    if (physical) {
        tmp = Math.pow(atk, 1.3);
        if (tmp > 2000)
            damage = 2000 * Math.pow(atk, 0.5) / Math.pow(def, 0.5);
        else
            damage = Math.pow(atk, 1.8) / Math.pow(def, 0.5);
        return Math.floor(damage);
    }
    tmp = Math.pow(atk, 1.15);
    if (tmp > 2000)
        damage = 2000 * Math.pow(atk, 0.5) / Math.pow(def, 0.5);
    else
        damage = Math.pow(atk, 1.65) / Math.pow(def, 0.5);
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
