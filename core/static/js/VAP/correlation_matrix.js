/**
 * Created by maria on 06.02.2019.
 */

function MatrixPlotly(options) {

    var data = [{
        x: options.labels,
        y: options.labels,
        z: options.data,
        type: 'heatmap'
    }];
    var layout = {
        title: 'Features Correlation Matrix',
        height: 410,
        width: 250 + 20 * options.labels.length,
        autosize: false,
        margin: {
            l: 150,
            t: 30,
            b: 120
        },
        xaxis: {
            showticklabels: true,
            tickangle: 45
        }
    };
    Plotly.plot(options.container, {
        data: data,
        layout: layout
    });

}
