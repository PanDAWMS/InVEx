/**
 * Created by maria on 06.02.2019.
 */
function Matrix(options) {
    var margin = {top: 50, right: 50, bottom: 100, left: 100},
        width = 40 * options.labels.length,
        height = 40 * options.labels.length,
        data = options.data,
        container = options.container,
        labelsData = options.labels,
        startColor = options.start_color,
        endColor = options.end_color;

    var widthLegend = 100;

    if(!data){
        throw new Error('Please pass data');
    }

    if(!Array.isArray(data) || !data.length || !Array.isArray(data[0])){
        throw new Error('It should be a 2-D array');
    }

    var maxValue = d3.max(data, function(layer) { return d3.max(layer, function(d) { return d; }); });
    var minValue = d3.min(data, function(layer) { return d3.min(layer, function(d) { return d; }); });

    var numrows = data.length;
    var numcols = data.length;

    var svg = d3.select(container).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var background = svg.append("rect")
        .style("stroke", "black")
        .style("stroke-width", "2px")
        .attr("width", width)
        .attr("height", height);

    var x = d3.scaleBand()
        .domain(d3.range(numcols))
        .rangeRound([0, width]);

    var y = d3.scaleBand()
        .domain(d3.range(numrows))
        .rangeRound([0, height]);

    var colorMap = d3.scaleLinear()
        .domain([minValue,maxValue])
        .range([startColor, endColor]);

    var row = svg.selectAll(".row")
        .data(data)
        .enter().append("g")
        .attr("class", "row")
        .attr("transform", function(d, i) { return "translate(0," + y(i) + ")"; });

    var cell = row.selectAll(".cell")
        .data(function(d) { return d; })
            .enter().append("g")
        .attr("class", "cell")
        .attr("transform", function(d, i) { return "translate(" + x(i) + ", 0)"; });

    cell.append('rect')
        .attr("width", x.bandwidth())
        .attr("height", y.bandwidth())
        .style("stroke-width", 0);

    cell.append("text")
        .attr("dy", ".32em")
        .attr("x", x.bandwidth() / 2)
        .attr("y", y.bandwidth() / 2)
        .attr("text-anchor", "middle")
        .style("fill", function(d, i) { return d >= maxValue/2 ? 'white' : 'black'; })
        .text(function(d, i) { return d.toLocaleString(undefined, { maximumSignificantDigits: 1 }); });

    row.selectAll(".cell")
        .data(function(d, i) { return data[i]; })
        .style("fill", colorMap);

    var labels = svg.append('g')
        .attr('class', "labels");

    var columnLabels = labels.selectAll(".column-label")
        .data(labelsData)
        .enter().append("g")
        .attr("class", "column-label")
        .attr("transform", function(d, i) { return "translate(" + x(i) + "," + height + ")"; });

    columnLabels.append("line")
        .style("stroke", "black")
        .style("stroke-width", "1px")
        .attr("x1", x.bandwidth() / 2)
        .attr("x2", x.bandwidth() / 2)
        .attr("y1", 0)
        .attr("y2", 5);

    columnLabels.append("text")
        .attr("x", 0)
        .attr("y", y.bandwidth() / 2)
        .attr("dy", ".82em")
        .attr("text-anchor", "end")
        .attr("transform", "rotate(-60)")
        .text(function(d, i) { return d; });

    var rowLabels = labels.selectAll(".row-label")
        .data(labelsData)
    .enter().append("g")
        .attr("class", "row-label")
        .attr("transform", function(d, i) { return "translate(" + 0 + "," + y(i) + ")"; });

    rowLabels.append("line")
        .style("stroke", "black")
        .style("stroke-width", "1px")
        .attr("x1", 0)
        .attr("x2", -5)
        .attr("y1", y.bandwidth() / 2)
        .attr("y2", y.bandwidth() / 2);

    rowLabels.append("text")
        .attr("x", -8)
        .attr("y", y.bandwidth() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .text(function(d, i) { return d; });
    
}