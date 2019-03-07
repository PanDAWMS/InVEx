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

    var data = dataClustersRadarChart(norm_data, real_data, clusters_list, clusters_color_scheme, dimNames);

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