/**
 * Created by Maria on 05.03.2019.
 */

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

function drawParallelCoordinates(element_id, real_data, real_stats, clusters_list, clusters_color_scheme, dimNames) {
    var _dimensions = [];

    for (var i = 0; i < dimNames.length; i++) {
        var tmp = {};

        tmp['label'] = dimNames[i];
        tmp['range'] = [real_stats[1][1][i], real_stats[1][2][i]];
		tmp['values'] = real_data.map((row) => {return row[1][i]});  

        _dimensions[i] = tmp;
    }

	var color_count = Object.keys(clusters_color_scheme).length,
		_colorscale = Object.keys(clusters_color_scheme).
			map((x, index) => {return [x/(color_count-1), rgbToHex(clusters_color_scheme[index])];}),
		_color = clusters_list.map((x) => {return x/(color_count-1)});

	var data = [{
		type: 'parcoords',
		line: {
			showscale: true,
			colorscale: _colorscale,
			color: _color,
			colorbar: {
				ticktext: Object.keys(clusters_color_scheme)
			}
		},
	
		dimensions: _dimensions
	}];

	var layout = {
		width: 80 * dimNames.length
	};

	Plotly.plot(element_id, data, layout);

	drawParallelCoordinatesD3(element_id, real_data, real_stats, clusters_list, clusters_color_scheme, dimNames);
}

function drawParallelCoordinatesD3(element_id, real_data, real_stats, clusters_list, clusters_color_scheme, dimNames) {
    /*
    * Parallel Coordinates visualization, inspired by :
    * Byron Houwens : https://codepen.io/BHouwens/pen/RaeGVd?editors=0010
    * Mike Bostock : https://bl.ocks.org/mbostock/1341021
    *
    */

    /*
     * Data
     *****************************/
    var data = [];

    for (var i = 0; i < real_data.length; i++) {
        var tmp = [];

        for (var j = 0; j < dimNames.length; j++)
            tmp[dimNames[j]] = real_data[i][1][j];

        data[i] = tmp;
    }
        
    var features = [];

    for (var i = 0; i < dimNames.length; i++) {
        var tmp = [];

        tmp['name'] = dimNames[i];
        tmp['range'] = [real_stats[1][1][i], real_stats[1][2][i]];

        features[i] = tmp;
    }

    /*
     * Parameters
     *****************************/
    const width = 90 * dimNames.length, height = 500, padding_x = 80, padding_y = 30, brush_width = 20;
    const filters = {};

    /*
     * Helper functions
     *****************************/
    // Horizontal scale
    const xScale = d3.scalePoint()
        .domain(features.map(x => x.name))
        .range([padding_x, width - padding_x]);

    // Each vertical scale
    const yScales = {};
    features.map(x => {
        yScales[x.name] = d3.scaleLinear()
            .domain(x.range)
            .range([height - padding_y, padding_y]);
    });
    //yScales.team = d3.scaleOrdinal()
    //    .domain(features[0].range)
    //    .range([height - padding, padding]);

    // Each axis generator
    const yAxis = {};
    d3.entries(yScales).map(x => {
        yAxis[x.key] = d3.axisLeft(x.value);
    });

    // Each brush generator
    const brushEventHandler = function (feature) {
        if (d3.event.sourceEvent && d3.event.sourceEvent.type === "zoom")
            return; // ignore brush-by-zoom
        if (d3.event.selection != null) {
            filters[feature] = d3.event.selection.map(d => yScales[feature].invert(d));
        } else {
            if (feature in filters)
                delete (filters[feature]);
        }
        applyFilters();
    }

    const applyFilters = function () {
        d3.select('g.active').selectAll('path')
            .style('display', d => (selected(d) ? null : 'none'));
    }

    const selected = function (d) {
        const _filters = d3.entries(filters);
        return _filters.every(f => {
            return f.value[1] <= d[f.key] && d[f.key] <= f.value[0];
        });
    }

    const yBrushes = {};
    d3.entries(yScales).map(x => {
        let extent = [
            [-(brush_width / 2), padding_y],
            [brush_width / 2, height - padding_y]
        ];
        yBrushes[x.key] = d3.brushY()
            .extent(extent)
            .on('brush', () => brushEventHandler(x.key))
            .on('end', () => brushEventHandler(x.key));
    });

    // Paths for data
    const lineGenerator = d3.line();

    const linePath = function (d) {
        const _data = d3.entries(d).filter(x => x.key);
        let points = _data.map(x => ([xScale(x.key), yScales[x.key](x.value)]));
        return (lineGenerator(points));
    }

    /*
     * Parallel Coordinates
     *****************************/
    // Main svg container
    const pcSvg = d3.select('#radar_chart_all')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Inactive data
    pcSvg.append('g').attr('class', 'inactive').selectAll('path')
        .data(data)
        .enter()
        .append('path')
        .attr('d', d => linePath(d));

    // Inactive data
    pcSvg.append('g').attr('class', 'active').selectAll('path')
        .data(data)
        .enter()
        .append('path')
        .attr('d', d => linePath(d));

    // Vertical axis for the features
    const featureAxisG = pcSvg.selectAll('g.feature')
        .data(features)
        .enter()
        .append('g')
        .attr('class', 'feature')
        .attr('transform', d => ('translate(' + xScale(d.name) + ',0)'));

    featureAxisG
        .append('g')
        .each(function (d) {
            d3.select(this).call(yAxis[d.name]);
        });

    featureAxisG
        .each(function (d) {
            d3.select(this)
                .append('g')
                .attr('class', 'brush')
                .call(yBrushes[d.name]);
        });

    featureAxisG
        .append("text")
        .attr("text-anchor", "middle")
        .attr('y', padding_y / 2)
        .text(d => d.name);    

    d3.select('g.active').selectAll('path')
        .each(function (d, i) {
            d3.select(this)
                .style('stroke', rgbToHex(clusters_color_scheme[clusters_list[i]]));
        });
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