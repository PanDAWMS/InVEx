/**
 * Created by maria on 06.02.2019.
 */

function MatrixPlotly(options) {

    trace1 = {
      x: options.labels,
      y: options.labels,
      z: options.data,
      type: 'heatmap'
    };
    data = [trace1];
    layout = {title: 'Features Correlation Matrix',
              width: 30 * options.labels.length,
              height: 30 * options.labels.length
    };
    Plotly.plot(options.container, {
      data: data,
      layout: layout
    });

}
