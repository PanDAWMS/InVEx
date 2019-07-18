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

function drawParallelCoordinates(element_id, real_data, clusters_list, clusters_color_scheme, dimNames, skipClust = []) {
    //console.log(clusters_list);
    d3.select("#" + element_id)
        .style("overflow", "auto");

    var margin = { top: 30, right: 10, bottom: 10, left: 10 },
        width = (dimNames.length > 7 ? 80 * dimNames.length : 600) - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var x = d3.scale.ordinal().rangePoints([0, width], 1),
        y = {},
        dragging = {};

    var line = d3.svg.line().interpolate("monotone"),
        axis = d3.svg.axis().orient("left"),
        background,
        foreground;

    var svg = d3.select("#" + element_id).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    $("#" + element_id + ".svg")
        .tooltip({
        track: true
        });

    var _values = [];

    // Extract the list of dimensions and create a scale for each.
    x.domain(dimensions = dimNames.map((dim, index) => {
        _values.push(real_data//.filter((elem, i) => { return skipClust.indexOf(clusters_list[i]) === -1; })
            .map((row) => { return row[1][index]; }));

        y[dim] = d3.scale.linear()
            .domain([Math.min(..._values[index]), Math.max(..._values[index])])
            .range([height, 0]);

        return dim;
    }));

    var _line_data = [];
    for (var i = 0; i < _values[0].length; i++) {
        var _tmp = {};
        for (var j = 0; j < _values.length; j++) _tmp[dimNames[j]] = _values[j][i];
        _line_data.push(_tmp);
    }



    // Add grey background lines for context.
    background = svg.append("g")
        .attr("class", "background")
        .selectAll("path")
        .data(_line_data)
        .enter().append("path")
            .attr("d", path);

    //console.log(background);

    // Add blue foreground lines for focus.
    foreground = svg.append("g")
        .attr("class", "foreground")
        .selectAll("path")
        .data(_line_data)
        .enter().append("path")
            .attr("d", path)
            .attr("stroke", (d, i) => rgbToHex(clusters_color_scheme[clusters_list[i]]))
            .on("mouseover", function (d, i) {
                d3.select(this).attr('stroke-width', 3);

                $('#t' + element_id).DataTable().row(i).show().draw(false);

                $('#t' + element_id).DataTable().rows().nodes()
                    .to$()
                    .removeClass('selected');

                $('#t' + element_id).DataTable().rows(i).nodes()
                    .to$()
                    .toggleClass('selected');
            })
            .on("mouseout", function (d) {
                d3.select(this).attr('stroke-width', 1);
            });

    // Add a group element for each dimension.
    var g = svg.selectAll(".dimension")
        .data(dimensions)
        .enter().append("g")
        .attr("class", "dimension")
        .attr("transform", function (d) { return "translate(" + x(d) + ")"; })
        .call(d3.behavior.drag()
            .origin(function (d) { return { x: x(d) }; })
            .on("dragstart", function (d) {
                dragging[d] = x(d);
                background.attr("visibility", "hidden");
            })
            .on("drag", function (d) {
                dragging[d] = Math.min(width, Math.max(0, d3.event.x));
                foreground.attr("d", path);
                dimensions.sort(function (a, b) { return position(a) - position(b); });
                x.domain(dimensions);
                g.attr("transform", function (d) { return "translate(" + position(d) + ")"; });
            })
            .on("dragend", function (d) {
                delete dragging[d];
                transition(d3.select(this)).attr("transform", "translate(" + x(d) + ")");
                transition(foreground).attr("d", path);
                background
                    .attr("d", path)
                    .transition()
                    .delay(500)
                    .duration(0)
                    .attr("visibility", null);
            }));

    // Add an axis and title.
    g.append("g")
        .attr("class", "axis")
        .each(function (d) { d3.select(this).call(axis.scale(y[d])); })
        .append("text")
        .style("text-anchor", "middle")
        .attr("y", -9)
        .text(function (d) { return d; });

    // Add and store a brush for each axis.
    g.append("g")
        .attr("class", "brush")
        .each(function (d) {
            d3.select(this).call(y[d].brush = d3.svg.brush().y(y[d]).on("brushstart", brushstart).on("brush", brush));
        })
        .selectAll("rect")
        .attr("x", -8)
        .attr("width", 16);

    function position(d) {
        var v = dragging[d];
        return v == null ? x(d) : v;
    }

    function transition(g) {
        return g.transition().duration(500);
    }

    // Returns the path for a given data point.
    function path(d) {
        return line(dimensions.map(function (p) { return [position(p), y[p](d[p])]; }));
    }

    function brushstart() {
        d3.event.sourceEvent.stopPropagation();
    }

    // Handles a brush event, toggling the display of foreground lines.
    function brush() {
        var actives = dimensions.filter(function (p) { return !y[p].brush.empty(); }),
            extents = actives.map(function (p) { return y[p].brush.extent(); }),
            visible = [];

        foreground.style("display", function (d, j) {
            return actives.every(function (p, i) { 
                var isVisible = (extents[i][0] <= d[p] && d[p] <= extents[i][1]);
                if (isVisible) visible.push(real_data[j][0]);
                return isVisible;
            }) ? null : "none";
        });
        if (actives.length === 0) visible.push("all");

        $('#t' + element_id).data('visible', visible);
        $('#t' + element_id).DataTable().draw();
    }



    var _color = clusters_list.filter((x) => { return skipClust.indexOf(x) === -1; });

    /*
    var plot = document.getElementById(element_id),

    color_max = Math.max(...Object.keys(clusters_color_scheme)),
    color_min = Math.min(...Object.keys(clusters_color_scheme)),
    zero_color = rgbToHex(clusters_color_scheme[color_min]),

    _colorscale = ((Object.keys(clusters_color_scheme).length === 1) ?
        [["0.0", zero_color], ["1.0", zero_color]] :
        Object.keys(clusters_color_scheme)
            .filter(x => { console.log(x, skipClust, skipClust.indexOf(x) === -1); return skipClust.indexOf(x) === -1; })
            .map((x) => {
                return [(x - color_min) / (color_max - color_min),
                rgbToHex(clusters_color_scheme[x])];
            })),

    _color = clusters_list.filter((x) => { return skipClust.indexOf(x) === -1; }),//  map((x) => { return x; }),

    _dimensions = dimNames.map((dim, index) => {
        var _values = real_data.filter((elem, i) => { return skipClust.indexOf(clusters_list[i]) === -1; })
            .map((row) => { return row[1][index]; });

        return {
            label: dim,
            range: [Math.min(..._values), Math.max(..._values)],
            values: _values
        };
    }),

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
    
    var graph = Plotly.newPlot(element_id, data, layout, config);
    //console.log(graph);

    d3.select("#" + element_id)
        .style("overflow", "auto");

    d3.selectAll("#" + element_id + " .axis-title")
        .style("transform", "translate(0, -28px) rotate(-9deg)");

    d3.selectAll(".plot-container")
        .attr('title', '');

    $(".plot-container").tooltip({
            track: true
        });
    */



    d3.select("#" + element_id)
        .append("table")
        .attr("id", "t" + element_id)
        .attr("class", "table table-sm table-hover display compact");

    var __theader_array = dimNames.slice();
    __theader_array.unshift('ID');

    var __theader = __theader_array.map(row => { return { title: row }; }),
        __tcells = real_data.map((row, i) => [row[0]].concat(row[1].map(String)).concat([rgbToHex(clusters_color_scheme[_color[i]])]));   

    $('#t' + element_id).DataTable({
        data: __tcells,
        columns: __theader,
        "rowCallback": (row, data) => {
            $(row).children().css('background', data[data.length - 1] + "33");
        }      
    });

    $('#t' + element_id).data('visible', ["all"]);

    $('#t' + element_id + ' tbody').on("mouseover", 'tr', function (d, i) {
                //console.log($('#t' + element_id).DataTable().row(this)[0][0]);
                //console.log(foreground);
                //$(this).css('background', "red");
        d3.select(foreground[0][$('#t' + element_id).DataTable().row(this)[0][0]]).attr('stroke-width', 3);
        console.log(foreground[0][$('#t' + element_id).DataTable().row(this)[0][0]], d);
            })
        .on("mouseout", 'tr', function (d) {
            console.log(this);
            d3.select(foreground[0][$('#t' + element_id).DataTable().row(this)[0][0]]).attr('stroke-width', 1);
        });



     /*   on('click', 'tr', function () {
        var data = table.row(this).data();
        alert('You clicked on ' + data[0] + '\'s row');
    });

    

    console.log(foreground);*/

    $.fn.dataTable.ext.search.push(
        function (settings, data, dataIndex) {
            if ($('#t' + element_id).data('visible')[0] === "all") return true;
            else return $('#t' + element_id).data('visible').includes(data[0]);
        }
    );

    /*plot.on('plotly_hover', function (data) {
        var infotext = "id: " + scene.realData[data.curveNumber][0];

        $(".plot-container").tooltip("option", "content", infotext);

        $('#t' + element_id).DataTable().row(data.curveNumber).show().draw(false);

        $('#t' + element_id).DataTable().rows().nodes()
            .to$()
            .removeClass('selected');

        $('#t' + element_id).DataTable().rows(data.curveNumber).nodes()
            .to$()
            .toggleClass('selected');

    });
    /*.on('plotly_unhover', function (data) {
        d3.select("#radar_chart_all")
            //.style("left", (data.clientX - 26) + "px")
            //.style("top", (data.y + 130) + "px")
            .attr('title', '');
    });*/
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