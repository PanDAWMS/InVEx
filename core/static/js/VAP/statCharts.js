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

// This function draws the Parallel Coordinates graph
// --------------
// Inputs:
//  element_id - id of DOM element where to put ParCoords
//  scene - object with the scene to take data from
//  options - ParCoords display options
//
function drawParallelCoordinates(element_id, scene, options = {})
{
    this._coord = new ParallelCoordinates(element_id, scene, options);
}
