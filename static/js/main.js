/**
 * Created by Natasha on 01-02-2016.
 */

google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(function() {drawChart([])});

function drawChart(dataArray) {
    var data = google.visualization.arrayToDataTable(dataArray);

    var view = new google.visualization.DataView(data);
    view.setColumns([0, 1,
                    { calc: "stringify",
                        sourceColumn: 1,
                        type: "string",
                        role: "annotation" }, 2,
                    { calc: "stringify",
                        sourceColumn: 2,
                        type: "string",
                        role: "annotation" },
                    3]);

    var options = {
        title: "Duration of "+ dataArray[0][0] +" in Hours",
        width: 1000,
        height: 500,
        animation:{
            duration:1000,
            startup: true
        }
    };
    var chart = new google.visualization.ColumnChart(document.getElementById("columnchart_values"));
    var runFirstTime = google.visualization.events.addListener(chart, 'ready', function(){
        google.visualization.events.removeListener(runFirstTime);
        chart.draw(data, options);
    });
    chart.draw(data, options);
}

$("#projects").change(function() {
    $.ajax({
        type: "POST",
        url: "/change_sequence",
        data: {
            project: $("#projects").val()
        },
        success: function (data) {
            $("#sequences").html(data);
            $("#shots").empty()
        }
    });
});
$("#sequences").change(function() {
    $.ajax({
        type: "POST",
        url: "/change_shot",
        data: {
            project: $("#projects").val(),
            sequence: $("#sequences").val()
        },
        success: function(data) {
            $("#shots").html(data);
        }
    });
});
$("#submit").bind('click', function() {
    $("#loader").show();
    $.ajax({
        type:"POST",
        url: "/load_chart",
        data: {
            project: $("#projects").val(),
            sequence: $("#sequences").val(),
            shot: $("#shots").val()
        },
        dataType: 'json',
        success:function(data){
            $("#loader").hide();
            drawChart(data); // Returns a json object of shot/seq information.
        },
        error: function(data){
            alert('error in ajax return');
            console.log(data);
        }
    });
});