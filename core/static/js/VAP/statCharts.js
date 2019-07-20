/**
 * Created by Maria on 05.03.2019.
 */

// This function allows to jump to a certain row in a DataTable
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

// This is used to manipulate d3 objects
// e.g., to move a line on a graph to the front
// https://github.com/wbkd/d3-extended
d3.selection.prototype.moveToFront = function () {
    return this.each(function () {
        this.parentNode.appendChild(this);
    });
};
d3.selection.prototype.moveToBack = function () {
    return this.each(function () {
        var firstChild = this.parentNode.firstChild;
        if (firstChild) {
            this.parentNode.insertBefore(this, firstChild);
        }
    });
};

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

// This function draws the Parallel Coordinates graph
// --------------
// Inputs:
//  element_id - id of DOM element where to put ParCoords
//  real_data - data to visualize, array format: [0: [0: id, 1: [array of values]], ... ]
//  clusters_list - array of ints with cluster numbers, format: [0, 0, 2, 3, ...]
//  clusters_color_scheme - array of cluster colors, format: [0: {r: float, g: float, b: float}, ...]
//  dimNames - array of dimention names, format: [0: "name", ...]
//  ??
//
function drawParallelCoordinates(element_id, real_data, clusters_list, clusters_color_scheme, dimNames, skipClust = []) {
    // Add overflow from the start
    d3.select("#" + element_id)
        .style("overflow", "auto");

    // Sizes of the graph
    var margin = { top: 30, right: 10, bottom: 10, left: 10 },
        width = (dimNames.length > 7 ? 80 * dimNames.length : 600) - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom,

    // Arrays for x and y data, and brush dragging
        x = d3.scale.ordinal().rangePoints([0, width], 1),
        y = {},
        dragging = {},

    // Line and axis parameters, arrays with lines (gray and colored)
        line = d3.svg.line().interpolate("monotone"),
        axis = d3.svg.axis().orient("left"),
        background,
        foreground;

    // Append an SVG to draw lines on
    graph = d3.select("#" + element_id).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    // Fancy glowing filter
    var filter = `
            <filter id="blur">
                <!-- Tweak colors in original image -->
                <feComponentTransfer in="SourceGraphic" result="components">
                    <feFuncR type="linear" slope="2"/>
                    <feFuncG type="linear" slope="2"/>
                    <feFuncB type="linear" slope="2"/>
                </feComponentTransfer>

                <!-- Apply blur -->
                <feGaussianBlur stdDeviation="4" result="blurring"></feGaussianBlur>              

                <!-- Mix those two -->
                <feMerge>
                    <feMergeNode in="blurring"/>
                    <feMergeNode in="components"/>
                </feMerge>
            </filter>`;

    // Place the filter on place
    graph.append("defs")
        .html(filter);

    // Shift the draw space
    var svg = graph.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")"),

    // Arrays with line pos values and array (line id)<->(id in real_data)
        _values = [],
        _ids = real_data.map((row) => row[0]);

    // Functions to perform id transformation
    function _tableToParcoords(index) { return _ids.indexOf(index); }
    function _parcoordsToTable(index) { return _ids[index]; }

    // Extract the list of dimensions and create a scale for each
    x.domain(dimensions = dimNames.map((dim, index) => {
        _values.push(real_data //.filter((elem, i) => { return skipClust.indexOf(clusters_list[i]) === -1; })
            .map((row) => row[1][index]));

        y[dim] = d3.scale.linear()
            .domain([Math.min(..._values[index]), Math.max(..._values[index])])
            .range([height, 0]);

        return dim;
    }));

    // Array to make brushes
    var _line_data = [];
    for (var i = 0; i < _values[0].length; i++) {
        let _tmp = {};
        for (var j = 0; j < _values.length; j++) _tmp[dimNames[j]] = _values[j][i];
        _line_data.push(_tmp);
    }

    // Grey background lines for context
    background = svg.append("g")
        .attr("class", "background")
        .selectAll("path")
        .data(_line_data)
        .enter().append("path")
            .attr("d", path);

    // Foreground lines
    foreground = svg.append("g")
        .attr("class", "foreground")
        .selectAll("path")
        .data(_line_data)
        .enter().append("path")
            .attr("d", path)

            // Cluster color scheme is applied to the stroke color 
            .attr("stroke", (d, i) => rgbToHex(clusters_color_scheme[clusters_list[i]]))

            // When mouse is over the line, make it glow, move to the front
            // and select a correspoding line in the table below
            .on("mouseover", function (d, i) {
                $(this).addClass("glowing");
                d3.select(this).moveToFront();

                datatable.rows().nodes()
                    .to$().removeClass('selected');

                let row = datatable.row((idx, data) => data[0] === _parcoordsToTable(i));

                row.show().draw(false);
                datatable.rows(row).nodes().to$().addClass('selected');
            })

            // When mouse is away, clear the glowing effect
            .on("mouseout", function (d) {
                $(this).removeClass("glowing");
            });

    // Add a group element for each dimension
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

    // Add an axis and titles
    g.append("g")
        .attr("class", "axis")
        .each(function (d) { d3.select(this).call(axis.scale(y[d])); })
        .append("text")
        .style("text-anchor", "middle")
        .attr("y", -9)
        .text(function (d) { return d; });

    // Add and store a brush for each axis
    g.append("g")
        .attr("class", "brush")
        .each(function (d) {
            d3.select(this).call(y[d].brush = d3.svg.brush().y(y[d]).on("brushstart", brushstart).on("brush", brush));
        })
        .selectAll("rect")
        .attr("x", -8)
        .attr("width", 16);

    // Functions for lines and brushes
    function position(d) {
        var v = dragging[d];
        return v == null ? x(d) : v;
    }

    function transition(g) {
        return g.transition().duration(500);
    }

    function brushstart() {
        d3.event.sourceEvent.stopPropagation();
    }

    // Returns the path for a given data point
    function path(d) {
        return line(dimensions.map(function (p) { return [position(p), y[p](d[p])]; }));
    }

    // Handles a brush event, toggling the display of foreground lines
    function brush() {
        var actives = dimensions.filter(function (p) { return !y[p].brush.empty(); }),
            extents = actives.map(function (p) { return y[p].brush.extent(); }),
            visible = [];

        foreground.style("display", function (d, j) {
            return actives.every(function (p, i) { 
                var isVisible = extents[i][0] <= d[p] && d[p] <= extents[i][1];

                if (isVisible) visible.push(real_data[j][0]);
                return isVisible;
            }) ? null : "none";
        });
        if (actives.length === 0) visible.push("all");

        $('#t' + element_id).data('visible', visible);
        $('#t' + element_id).DataTable().draw();
    }

    // Cluster list
    var _color = clusters_list.filter((x) => { return skipClust.indexOf(x) === -1; });

    // Add table below the ParCoords
    d3.select("#" + element_id)
        .append("table")
        .attr("id", "t" + element_id)
        .attr("class", "table table-sm table-hover display compact");    

    // Array with headers
    var _theader_array = dimNames.slice();
    _theader_array.unshift('ID');

    // Map headers for the tables
    var _theader = _theader_array.map(row => { return { title: row }; }),

    // Array with table cell data
        _tcells = real_data.map((row, i) =>
            [row[0]]
                .concat(row[1].map(String))
                .concat([rgbToHex(clusters_color_scheme[_color[i]])])
        ),

    // Vars for table and its datatable
        table = $('#t' + element_id),
        datatable = table.DataTable({
            data: _tcells,
            columns: _theader,

            // Make colors lighter for readability
            "rowCallback": (row, data) => {
                $(row).children().css('background', data[data.length - 1] + "33");
            }      
        });

    // 'visible' data array with lines on foreground (not filtered by a brush)
    //  possible values: ["all"] or ["id in real_data", ...]
    table.data('visible', ["all"]);

    // Add glow to lines when a line is hovered over in the table
    $('#t' + element_id + ' tbody').on("mouseover", 'tr', function (d, i) {
            let line = foreground[0][_tableToParcoords(datatable.row(this).data()[0])];
            $(line).addClass("glowing");
            d3.select(line).moveToFront();
        })
        .on("mouseout", 'tr', function (d) {
            $(foreground[0][_tableToParcoords(datatable.row(this).data()[0])]).removeClass("glowing");
        });

    // Add footer elements
    table.append(
        $('<tfoot/>').append($('#t' + element_id + ' thead tr').clone())
    );

    // Add inputs to those elements
    $('#t' + element_id + ' tfoot th').each(function (i, x) {
        $(this).html('<input type="text" placeholder="Search" id="tableInput' + i + '"/>');
    });

    // Apply the search
    datatable.columns().every(function (i, x) {
        $('#tableInput'+i).on('keyup change', function () {
            datatable
                .columns(i)
                .search(this.value)
                .draw();
        });
    });

    // When a brush filteres lines, this is the callback in the table
    $.fn.dataTable.ext.search.push(
        function (settings, data, dataIndex) {
            if ($('#t' + element_id).data('visible')[0] === "all") return true;
            else return $('#t' + element_id).data('visible').includes(data[0]);
        }
    );



    // trash bin :)

/* $("#" + element_id + ".svg")
        .tooltip({
        track: true
        });*/
   // console.log('ids', _ids);
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