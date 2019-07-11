/**
 * Created by Maria on 05.03.2019.
 */

$.fn.dataTable.Api.register('row().show()', function () {
    var page_info = this.table().page.info();
    // Get row index
    var new_row_index = this.index();
    // Row position
    var row_position = this.table().rows()[0].indexOf(new_row_index);
    // Already on right page ?
    if (row_position >= page_info.start && row_position < page_info.end) {
        // Return row object
        return this;
    }
    // Find page number
    var page_to_display = Math.floor(row_position / this.table().page.len());
    // Go to that page
    this.table().page(page_to_display);
    // Return row object
    return this;
});

function getClusterMeans(data, clusters_list, cluster_number) {
    // generate list of indexes for current cluster number
    var cluster_indexes = [];
    for (var i = 0; i < clusters_list.length; i++ ) {
        if (clusters_list[i] == cluster_number)
            cluster_indexes.push(i);
    }
    // generate a list of all data objects for current cluster
    var data_cluster = [];
    for (var j = 0; j < data.length; j++) {
        if (cluster_indexes.includes(j) === true)
            data_cluster.push(data[j][1]);
    }
    // transpose array
    var result = Array.from({ length: data_cluster[0].length }, function(x, row) {
      return Array.from({ length: data_cluster.length }, function(x, col) {
        return data_cluster[col][row];
      });
    });
    var mean_values = [];
    for (var i = 0; i < result.length; i++)
        mean_values.push(ss.mean(result[i]));
    return mean_values;
}

function dataGroupRadarChart(groups_data, selections_history, dimNames) {
    var data = [];
    for (var i=0; i<selections_history.length; i++) {
        var group = selections_history[i]['group'];
        var group_dict = {};
        group_dict['type'] = 'scatterpolargl';
        group_dict['r'] = groups_data[group][0];
        group_dict['text'] = groups_data[group][1];
        group_dict['theta'] = dimNames;
        group_dict['fill'] = 'toself';
        group_dict['fillcolor'] = rgbToHex(selections_history[i]['color']);
        group_dict['opacity'] = 0.5;
        group_dict['name'] = 'Group ' + group;
        data.push(group_dict);
    }
    return data;
}

function dataClustersRadarChart(norm_data, real_data, clusters_list, clusters_color_scheme, dimNames) {
    var data = [];
    for (var cluster in clusters_color_scheme) {
        var cluster_dict = {};
        cluster_dict['type'] = 'scatterpolargl';
        cluster_dict['r'] = getClusterMeans(norm_data, clusters_list, cluster);
        cluster_dict['text'] = getClusterMeans(real_data, clusters_list, cluster);
        cluster_dict['theta'] = dimNames;
        cluster_dict['fill'] = 'toself';
        cluster_dict['fillcolor'] = rgbToHex(clusters_color_scheme[cluster]);
        cluster_dict['opacity'] = 0.5;
        cluster_dict['name'] = 'Cluster ' + cluster;
        data.push(cluster_dict);
    }
    return data;
}

function drawMultipleGroupRadarChart(element_id, groups_data, selections_history, dimNames, scale) {

    var data = dataGroupRadarChart(groups_data, selections_history, dimNames);

    layout = {
      polar: {
        radialaxis: {
          visible: true,
          range: [0, scale]
        }
      }
    };

    Plotly.newPlot(element_id, data, layout);
}

function drawMultipleClusterRadarChart(element_id, norm_data, real_data, clusters_list, clusters_color_scheme, dimNames) {

    var data2 = dataClustersRadarChart(norm_data, real_data, clusters_list, clusters_color_scheme, dimNames);

    layout = {
        polar: {
            radialaxis: {
                visible: true,
                range: [0, 100]
            }
        }
    };

    Plotly.plot(element_id, data, layout);
}

function drawParallelCoordinates(element_id, real_data, clusters_list, clusters_color_scheme, dimNames) {
    var plot = document.getElementById(element_id),

    _dimensions = dimNames.map((dim, index) => {
        var _values = real_data.map((row) => { return row[1][index]; });

        return {
            label: dim,
            range: [Math.min(..._values), Math.max(..._values)],
            values: _values
        };
    }),

    color_max = Math.max(...Object.keys(clusters_color_scheme)),
    color_min = Math.min(...Object.keys(clusters_color_scheme)),
    zero_color = rgbToHex(clusters_color_scheme[color_min]),

    _colorscale = ((Object.keys(clusters_color_scheme).length === 1) ?
        [["0.0", zero_color], ["1.0", zero_color]] :
        Object.keys(clusters_color_scheme).
            map((x) => {
                return [(x - color_min) / (color_max - color_min),
                rgbToHex(clusters_color_scheme[x])];
            })),

    _color = clusters_list.map((x) => { return x; }),

    _parcoords = {
        type: 'parcoords',
        line: {
            showscale: true,
            colorscale: _colorscale,
            color: _color
        },
        dimensions: _dimensions
    },

    data = [_parcoords],

    layout = {
        width: dimNames.length > 7 ? 80 * dimNames.length : 600,
        height: 500,
        annotations: {
            visible: false
        }
    },

    config = {
        toImageButtonOptions: {
            format: 'png', // one of png, svg, jpeg, webp
            filename: 'parallel_coordinates',
            scale: 1 // Multiply title/legend/axis/canvas sizes by this factor
        }
    };
    
    Plotly.newPlot(element_id, data, layout, config);
    
    d3.select("#" + element_id)
        .style("overflow", "auto");

    d3.selectAll("#" + element_id + " .axis-title")
        .style("transform", "translate(0, -28px) rotate(-9deg)");




    d3.select("#" + element_id)
        .append("label")
        .attr("id", "hoverInfo1");

    d3.select("#" + element_id)
        .append("table")
        .attr("id", "t" + element_id)
        .attr("class", "table table-sm table-hover display compact");
    var __theader_array = dimNames.slice();
    __theader_array.unshift('ID');
    var __theader = __theader_array.map(row => { return { title: row }; });

    var __tcells = real_data.map(row => [row[0]].concat(row[1].map(String)));

       

    $('#t' + element_id).DataTable({
        data: __tcells,
        columns: __theader
    });


    plot.on('plotly_hover', function (data) {
        var infotext = "id: " + data.curveNumber;

        //console.log(data);

        d3.select("#hoverInfo1")
            .style("position", "absolute")
            .style("left", (data.clientX - 26) + "px")
            .style("top", (data.clientY + 50) + "px")
            .style("background", "#ddd")
            .html(infotext);

        //console.log($($('#t' + element_id).DataTable().row(data.curveNumber).data()));

        $('#t' + element_id).DataTable().row(data.curveNumber).show().draw(false);

        $('#t' + element_id).DataTable().rows(data.curveNumber).nodes()
        .to$()
        .toggleClass('selected');
            
    })
    .on('plotly_unhover', function (data) {
        d3.select("#hoverInfo1").html('<br/>');

        $('#t' + element_id).DataTable().rows(data.curveNumber).nodes()
            .to$()
            .removeClass('selected');
    });


    //var table = document.createElement("table");
    //table.id = ID;
    //table.classList.add("table", "table-sm", "table-hover", "display", "compact");
    //__tcells = __tcells_transposed[0].map((col, i) => __tcells_transposed.map(row => row[i]));

}

function drawSingleClusterRadarCharts(element_id, norm_data, real_data, clusters_list, clusters_color_scheme, dimNames) {
    var parent_element = document.getElementById(element_id);
    var data = dataClustersRadarChart(norm_data, real_data, clusters_list, clusters_color_scheme, dimNames);

    layout = {
      polar: {
        radialaxis: {
          visible: true,
          range: [0, 100]
        }
      },
      showlegend: true
    };

    for (var i = 0; i<data.length; i++) {
        var div = document.createElement("div");
        div.classList.add("columns", "medium-3");
        div.setAttribute("id", "chart_"+i);
        parent_element.appendChild(div);
        Plotly.plot("chart_"+i, [data[i]], layout);
    }
}