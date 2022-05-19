/* Get lang */
let language = "TR";
$.get("https://ipinfo.io", function(response) {
    const _temp_lan = response.country;
    if (_temp_lan) {
        language = response.country;
    }
});


const login_form_values = {
    "Kayıt ol": {
        "attr": {
            "#login-form-button-right": ["value", "Kayıt ol"]
        },
        "html": {
            "#login-form-button-left": "Geri",
            "#login-form-label-type": "Kayıt"
        }
    },
    "Geri": {
        "attr": {
            "#login-form-button-right": ["value", "Giriş yap"]
        },
        "html": {
            "#login-form-button-left": "Kayıt ol",
            "#login-form-label-type": "Giriş"
        }
    }
};

$(document).on('click', "[id=login-form-button-left]", function(btn) {

    const new_val_inside = login_form_values[btn.currentTarget.innerText];

    for (const [key, func_inside] of Object.entries(new_val_inside)) {

        if (key == "attr") {
            for (const [key, value] of Object.entries(func_inside)) {
                $(key).attr(value[0], value[1])
            };
        } else if (key == "html") {
            for (const [key, value] of Object.entries(func_inside)) {
                $(key).html(value);
            };
        };
    };

    /* Hatayı sil */
    $('#login-form-label-error').hide();

    /* Formu boşalt */
    $('#login-entry-pwd').val("");
    $('#login-entry-username').val("");
    $('#login-entry-pass').val("");

    /* Gözü kapat */
    $('#pass-eye').html("<i class='fa-solid fa-eye-slash'></i>");
    $('#login-entry-pass').attr("type", "password");

    /* PWD toggle */
    $('#login-entry-pwd').toggle();
});

$(document).on('click', "[id=pass-eye]", function() {
    if ($('#login-entry-pass').attr("type") == "password") {

        /* Gözü aç */
        $('#pass-eye').html("<i class='fa-solid fa-eye'></i>");
        $('#login-entry-pass').attr("type", "text");
    } else {
        /* Gözü kapat */
        $('#pass-eye').html("<i class='fa-solid fa-eye-slash'></i>");
        $('#login-entry-pass').attr("type", "password");
    };


});

/* Pasta dilimli yüzdelik */
$('.dynamicsparkline').sparkline([6, 18], {
    type: 'pie',
    sliceColors: ['#d00000', '#33b864'],
    width: '75px',
    height: '75px'
});

/* test amaçlı coin list yükleme */

$(window).on('load', function() {

    $.getJSON("../assets/test-assets/exchange-info.json", function(jsonDat) {
        var black_list = new Set(["BTCUSDT"])
        var istenen_hacim = 500

        var jsonData = jsonDat["symbols"].reverse()
        $.each(jsonData, function(col, insde) {
            if (insde["contractType"] == "PERPETUAL" & insde["status"] == "TRADING" & insde["symbol"] == insde["pair"] & insde["underlyingType"] == "COIN" & insde["quoteAsset"] == "USDT") {
                var a = new Date(insde["onboardDate"]);
                var a_ = a.toLocaleDateString(language, { year: "numeric", month: "2-digit", day: "2-digit" });
                var price = Math.random() * 1010
                var price_change = Math.random() * (Math.random() < 0.5 ? -1 : 1)
                var hacim = Math.random() * 10100
                var volume_change = Math.random() * (Math.random() < 0.5 ? -1 : 1)

                $('table > tbody#coin-info-table-body:last-child').append(`<tr ${black_list.has(insde["symbol"]) ? 'deactive-coin="Karalistede olduğu için devredışı bırakıldı"' :  hacim < istenen_hacim ? 'deactive-coin="Hacim miktarı istenilenden az olduğu için devredışı bırakıldı"' : ""}>
			<td value="${insde["symbol"]}">${insde["symbol"]}</td>
			<td value="${(price)}">${(price).toString().match(/^-?\d+(?:\.\d{0,2})?/)[0]}</td>
			<td value="${price_change}" ${price_change < 0 ? 'class="fall"' : 'class="raise"'}>% ${price_change.toString().match(/^-?\d+(?:\.\d{0,2})?/)[0]}</td>
			<td value="${hacim}">${hacim.toString().match(/^-?\d+(?:\.\d{0,2})?/)[0]}</td>
			<td value="${volume_change}" ${volume_change < 0 ? 'class="fall"' : 'class="raise"'}>% ${volume_change.toString().match(/^-?\d+(?:\.\d{0,2})?/)[0]}</td>
			<td value="${insde["underlyingSubType"].join(", ")}">${insde["underlyingSubType"].join(", ")}</td>
			<td value="${insde["onboardDate"]}">${a_}</td>
			</tr>`);
            };
        });
    });
});

/* Coin listesi arama */

$(document).ready(function() {

    $('[id="coin-info-search"]').on("keyup change", function() {
        var inputs = [];
        $('input[id="coin-info-search"]').each(function() {
            var li = [$(this).val().toUpperCase(), $(this).attr("type")]
            if ($(this).parent("th").children().length > 1) {
                li.push($(this).parent("th").children("select").val())
            }
            inputs.push(li)
        });
        $("#coin-info-table-body tr").filter(function() {
            var $row = $(this)
            var matchedIndexes = [];
            $.each(inputs, function(col, insde) {
                var type = insde[1]
                var value = insde[0]
                var $tdElement = $row.find(`td:eq(${col})`)
                var element_val = $tdElement.attr("value")
                if (type == "text") {
                    matchedIndexes.push(element_val.toUpperCase().indexOf(value))
                    editHighlighting($tdElement, value);
                } else if (value != "" & type == "number") {
                    if (parseFloat(element_val) < parseFloat(value)) {
                        matchedIndexes.push(-parseInt(insde[2]))
                    } else {
                        matchedIndexes.push(parseInt(insde[2]))
                    }

                } else if (value != "" & type == "date") {
                    if (parseInt(element_val) < parseInt((new Date(value)).getTime())) {
                        matchedIndexes.push(-parseInt(insde[2]))
                    } else {
                        matchedIndexes.push(parseInt(insde[2]))
                    }

                }
            });
            var matchedIndex = Math.min.apply(null, matchedIndexes);
            $row.toggle(matchedIndex > -1);
        });
    });

    /* sort table coin-list */
    $('#inp-headers th').click(function() {
        var table = $(this).parents('table').eq(0)
        var rows = table.find('tbody tr').toArray().sort(comparer($(this).index()))
        this.asc = !this.asc
        if (!this.asc) { rows = rows.reverse() }
        for (var i = 0; i < rows.length; i++) { table.append(rows[i]) }
    })

    function comparer(index) {
        return function(a, b) {
            var valA = getCellValue(a, index),
                valB = getCellValue(b, index)
            return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB)
        }
    }

    function getCellValue(row, index) {
        var valu = $(row).children('td').eq(index).attr("value")
        if (valu) {
            return valu
        }
        return $(row).children('td').eq(index).text()
    }



});

/* Coin listesi renklendirme ekleme */

function editHighlighting(element, textToHighlight) {
    var text = element.text();
    var highlightedText = '<em>' + textToHighlight + '</em>';
    var newText = text.replace(textToHighlight, highlightedText);

    element.html(newText);
}




$('#bakiye_yuzde').on('DOMSubtreeModified', function() {
    document.getElementById("bakiye_yuzde").value = document.getElementById("bakiye_range-slider").innerText
});



$(document).on('click', "[id=r-btn]", function() {
    $.ajax({
        url: '/',
        type: 'POST',
        data: {
            form_type: $('#r-btn').val(),
            pwd: $('#pdw_input').val(),
            username: $('#username').val(),
            pass: $('#pass').val()
        },
        success: function(donen_veri) {
            if (donen_veri["status"] == "error")
                $('#label-login').html(donen_veri["resp"])

            else if (donen_veri["status"] == "logged")
                $('#main').html(donen_veri["resp"])


        },
        error: function(donen_veri) {
            $('#label-login').html("Sunucu hata verdi")
        }
    });
});


$(document).on('click', "[id=logout]", function() {
    $.ajax({
        url: '/logout',
        type: 'POST',
        success: function(donen_veri) {
            $('#main').html(donen_veri)
        },
        error: function(donen_veri) {
            $('#main').html("Sunucu hata verdi")
        }
    });

});

$(document).on('click', "[id=account]", function() {
    $.ajax({
        url: '/',
        type: 'GET',
        success: function(donen_veri) {
            $('#main').html(donen_veri)
        },
        error: function(donen_veri) {
            $('#main').html("Sunucu hata verdi")
        }
    });

});