/**
 * Created by Natasha on 01-02-2016.
 */

google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(function() {drawChart([])});

var chartData = [];

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
        title: "Duration of "+ dataArray[0][0] +" in Days",
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


//Doesn't need to be a seperate function, but now I know how callbacks work!
function getDataFromServer(project, sequence, shot, callback){
    $.ajax({
        type:"POST",
        url: "/load_chart",
        data: {
            project: project,
            sequence: sequence,
            shot: shot
        },
        dataType: 'json',
        success:function(data){
            callback(data);
        },
        error: function(){
            callback([]);
        }
    });
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
    project = $("#projects").val();
    sequence = $("#sequences").val();
    shot = $("#shots").val();
    getDataFromServer(project, sequence, shot, function(chartData){
        if (chartData === undefined || chartData.length == 0) {
            alert("error");
        }
        else {
            $("#loader").hide();
            $("#bid-panel").show();
            drawChart(chartData);
        }
    });
});

$("#export").bind('click', function () {
    $("#loader").show();
    $.ajax({
        type: "POST",
        url: "/export_data",
        data: {
            project: $("#projects").val()
        },
        success: function (data) {
            if (data == 'success'){
                $("#loader").hide();
                alert('export complete')
            }
            else {
                alert('export failed')
            }
        }
    });
});


