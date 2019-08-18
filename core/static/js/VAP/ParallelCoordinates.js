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

class ParallelCoordinates {

    constructor(element_id, real_data, clusters_list, clusters_color_scheme,
        dimNames, skipOptions = {}) {
        // Update data and draw the graph
        this.updateData(element_id, real_data, clusters_list, clusters_color_scheme, dimNames, skipOptions);
    }

    updateData(element_id, real_data, clusters_list, clusters_color_scheme,
        dimNames, skipOptions = {}) {       
        this.element_id = element_id;

        this.real_data = real_data;
        this.clusters_list = clusters_list;
        this.clusters_color_scheme = clusters_color_scheme;
        this.dimNames = dimNames;

        // If skipOptions is empty, init an empty one
        if (skipOptions === {})
            skipOptions = {
                dims: { mode: "none" },
                clusters: { mode: "none" },
                elements: { mode: "none" }
            };

        this.skipOptions = skipOptions;


        // -------------------
        // debug redefine
        this.skipOptions = {
            dims: {
                mode: "show", // hide, show, none
                values: ["IObytesRead", "IObytesReadRate", "IObytesWriteRate", "IObytesWritten", "IOcharWritten", "avgrss"]
            },
            clusters: {
                mode: "hide", // hide, show, none
                values: ["2", "3"]
            },
            elements: {
                mode: "none" // hide, show, none
                //values: ["2", "3"]
            }
        };
        // ------------------

        this._drawGraphAndTable();
    }


    _drawGraphAndTable() {
        // A link to this ParCoord object
        var _PCobject = this;

        // Add overflow from the start
        d3.select("#" + this.element_id)
            .style("overflow", "auto");

        // Construct the list with dimentions on graph
        this._dimensions = this.dimNames.filter((elem, i) => {
            if (!('dims' in this.skipOptions)) return true;
            if (this.skipOptions['dims'].mode === 'show' && this.skipOptions['dims'].values.includes(elem)) return true;
            if (this.skipOptions['dims'].mode === 'hide' && !this.skipOptions['dims'].values.includes(elem)) return true;
            if (this.skipOptions['dims'].mode === 'none') return true;
            return false;
        });

        // Sizes of the graph
        this._margin = { top: 30, right: 10, bottom: 10, left: 10 };
        this._width = (this._dimensions.length > 7 ? 80 * this._dimensions.length : 600) - this._margin.left - this._margin.right;
        this._height = 500 - this._margin.top - this._margin.bottom;

        // Arrays for x and y data, and brush dragging
        this._x = d3.scale.ordinal().rangePoints([0, this._width], 1);
        this._y = {};
        this._dragging = {};

        // Line and axis parameters, arrays with lines (gray and colored)
        this._line = d3.svg.line().interpolate("monotone");
        this._axis = d3.svg.axis().orient("left");

        // Append an SVG to draw lines on
        this._graph = d3.select("#" + this.element_id).append("svg")
            .attr("width", this._width + this._margin.left + this._margin.right)
            .attr("height", this._height + this._margin.top + this._margin.bottom);

        // Shift the draw space
        this._svg = this._graph.append("g")
            .attr("transform", "translate(" + this._margin.left + "," + this._margin.top + ")");

        // Arrays with line pos values and array (line id)<->(id in real_data)
        this._values = [];
        this._ids = this.real_data.map((row) => row[0]);

        // Extract the list of dimensions and create a scale for each
        this._x.domain(this._dimensions.map((dim, index) => {
            this._values.push(this.real_data //.filter((elem, i) => { return skipClust.indexOf(clusters_list[i]) === -1; })
                .map((row) => row[1][index]));

            this._y[dim] = d3.scale.linear()
                .domain([Math.min(...this._values[index]), Math.max(...this._values[index])])
                .range([this._height, 0]);

            return dim;
        }));

        // Array to make brushes
        this._line_data = [];
        for (var i = 0; i < this._values[0].length; i++) {
            let tmp = {};
            for (var j = 0; j < this._values.length; j++) tmp[this._dimensions[j]] = this._values[j][i];
            this._line_data.push(tmp);
        }

        // Grey background lines for context
        this._background = this._svg.append("g")
            .attr("class", "background")
            .selectAll("path")
            .data(this._line_data)
            .enter().append("path")
            .attr("d", this._path.bind(this));

        // Foreground lines
        this._foreground = this._svg.append("g")
            .attr("class", "foreground")
            .selectAll("path")
            .data(this._line_data)
            .enter().append("path")
            .attr("d", this._path.bind(this))

            // Cluster color scheme is applied to the stroke color 
            .attr("stroke", (d, i) => rgbToHex(this.clusters_color_scheme[this.clusters_list[i]]))
            .attr("stroke-opacity", "0.4")

            // When mouse is over the line, make it bold and colorful, move to the front
            // and select a correspoding line in the table below
            .on("mouseover", function (d, i) {
                $(this).addClass("bold");
                d3.select(this).moveToFront();
                
                //console.log(_PCobject);
                //bold[0][i].attr("display", "block");
                //stroke: #0082C866;

                _PCobject._datatable.rows().nodes()
                    .to$().removeClass('selected');

                let row = _PCobject._datatable.row((idx, data) => data[0] === _PCobject._parcoordsToTable(i));

                row.show().draw(false);
                _PCobject._datatable.rows(row).nodes().to$().addClass('selected');
            })

            // When mouse is away, clear the effect
            .on("mouseout", function (d) {
                $(this).removeClass("bold");
            });

        // Add a group element for each dimension
        this._g = this._svg.selectAll(".dimension")
            .data(this._dimensions)
            .enter().append("g")
            .attr("class", "dimension")
            .attr("transform", function (d) { return "translate(" + _PCobject._x(d) + ")"; })
            .call(d3.behavior.drag()
                .origin(function (d) { return { x: this._x(d) }; }.bind(this))
                .on("dragstart", function (d) {
                    this._dragging[d] = this._x(d);
                    this._background.attr("visibility", "hidden");
                }.bind(this))
                .on("drag", function (d) {
                    this._dragging[d] = Math.min(this._width, Math.max(0, d3.event.x));
                    this._foreground.attr("d", this._path.bind(this));
                    this._dimensions.sort(function (a, b) { return this._position(a) - this._position(b); }.bind(this));
                    this._x.domain(this._dimensions);
                    this._g.attr("transform", function (d) { return "translate(" + this._position(d) + ")"; }.bind(this));
                }.bind(this))
                .on("dragend", function (d) {
                    delete _PCobject._dragging[d];
                    _PCobject._transition(d3.select(this)).attr("transform", "translate(" + _PCobject._x(d) + ")");
                    _PCobject._transition(_PCobject._foreground).attr("d", _PCobject._path.bind(_PCobject));
                    _PCobject._background
                        .attr("d", _PCobject._path.bind(_PCobject))
                        .transition()
                        .delay(500)
                        .duration(0)
                        .attr("visibility", null);
                }));
        //console.log(_PCobject._y);



        // Add an axis and titles
        this._g.append("g")
            .attr("class", "axis")
            .each(function (d) { d3.select(this).call(_PCobject._axis.scale(_PCobject._y[d])); })
            .append("text")
            .style("text-anchor", "middle")
            .attr("y", -9)
            .text(function (d) { return d; });

        // Add and store a brush for each axis
        this._g.append("g")
            .attr("class", "brush")
            .each(function (d) {
                d3.select(this).call(
                    _PCobject._y[d].brush = d3.svg.brush()
                        .y(_PCobject._y[d])
                        .on("brushstart", _PCobject._brushstart)
                        .on("brush", _PCobject._brush.bind(this, _PCobject)));
            })
            .selectAll("rect")
            .attr("x", -8)
            .attr("width", 16);

        // Cluster list
        this._color = this.clusters_list;///.filter((x) => { return skipClust.indexOf(x) === -1; });

        // Add table below the ParCoords
        d3.select("#" + this.element_id)
            .append("table")
            .attr("id", "t" + this.element_id)
            .attr("class", "table hover");

        // Array with headers
        this._theader_array = this.dimNames.slice();
        this._theader_array.unshift('ID');

        // Map headers for the tables
        this._theader = this._theader_array.map(row => { return { title: row }; }),

            // Array with table cell data
            this._tcells = this.real_data.map((row, i) =>
                [row[0]]
                    .concat(row[1].map(String))
                    .concat([rgbToHex(this.clusters_color_scheme[this._color[i]])])
            ),

            // Vars for table and its datatable
            this._table = $('#t' + this.element_id),
            this._datatable = this._table.DataTable({
                data: this._tcells,
                columns: this._theader,

                // Make colors lighter for readability
                "rowCallback": (row, data) => {
                    $(row).children().css('background', data[data.length - 1] + "33");
                }
            });

        // 'visible' data array with lines on foreground (not filtered by a brush)
        //  possible values: ["all"] or ["id in real_data", ...]
        this.visible = ["all"];

        // Initialize a search result with all objects visible
        this._search_results = this.real_data.map((x) => x[0]);

        // Add glow to lines when a line is hovered over in the table
        $('#t' + this.element_id + ' tbody').on("mouseover", 'tr', function (d, i) {
            let line = _PCobject._foreground[0][_PCobject._tableToParcoords(_PCobject._datatable.row(this).data()[0])];
            $(line).addClass("bold");
            d3.select(line).moveToFront();
        })
            .on("mouseout", 'tr', function (d) {
                $(_PCobject._foreground[0][
                    _PCobject._tableToParcoords(_PCobject._datatable.row(this).data()[0])
                ]).removeClass("bold");
            });

        // Add footer elements
        this._table.append(
            $('<tfoot/>').append($('#t' + this.element_id + ' thead tr').clone())
        );

        // Add inputs to those elements
        $('#t' + this.element_id + ' tfoot th').each(function (i, x) {
            $(this).html('<input type="text" placeholder="Search" id="t' + _PCobject.element_id + 'Input' + i + '"/>');
        });

        // Apply the search
        this._datatable.columns().every(function (i, x) {
            $('#t' + _PCobject.element_id + 'Input' + i).on('keyup change', function () {
                //_PCobject._brush(_PCobject);

                _PCobject._datatable
                    .columns(i)
                    .search(this.value)
                    .draw();

                /*_PCobject._search_results = Object.values(
                    _PCobject._datatable
                        .rows({ search: 'applied' }).nodes()
                            .map((x) => x.firstChild.innerHTML));*/

                //console.log(_PCobject._search_results);

                /*let actives = _PCobject._dimensions.filter(function (p) { return !_PCobject._y[p].brush.empty(); }),
                    extents = actives.map(function (p) { return _PCobject._y[p].brush.extent(); }),
                    visible = [];

                _PCobject._foreground.style("display", function (d, j) {
                    let isVisible = actives.every(function (p, i) {
                        return extents[i][0] <= d[p] && d[p] <= extents[i][1];
                    });

                    return isVisible && _PCobject._search_results.includes(_PCobject._parcoordsToTable(j)) ? null : "none";
                });*/

                _PCobject._brush(_PCobject);
                //if (actives.length === 0) visible.push("all");

                //_PCobject._foreground.style("display", null);
                //console.log(_PCobject._datatable.rows({ search: 'applied' }).data());
                
            });
        });

        // When a brush filteres lines, this is the callback in the table
        $.fn.dataTable.ext.search.push(
            function (settings, data, dataIndex, rowData, counter) {
                if (settings.sTableId !== "t" + _PCobject.element_id) return true;

                if (counter === 0) _PCobject._search_results = [];

                if (_PCobject.visible[0] === "all") {
                    _PCobject._search_results.push(data[0]);
                    return true;
                }
                console.log(settings);
                if (_PCobject.visible.includes(data[0])) _PCobject._search_results.push(data[0]);

                return _PCobject.visible.includes(data[0]);
            }
        );

        // trash bin :)
        
        /* $("#" + element_id + ".svg")
                .tooltip({
                track: true
                });*/
        // console.log('ids', _ids);

        return this;
    }

    // Functions to perform id transformation
    _tableToParcoords(index) { return this._ids.indexOf(index); }
    _parcoordsToTable(index) { return this._ids[index]; }

    // Functions for lines and brushes
    _position(d) {
        let v = this._dragging[d];
        return v == null ? this._x(d) : v;
    }

    _transition(g) {
        return g.transition().duration(500);
    }

    _brushstart() {
        d3.event.sourceEvent.stopPropagation();
    }

    // Returns the path for a given data point
    _path(d) {
        return this._line(
            this._dimensions.map(
                function (p) { return [this._position(p), this._y[p](d[p])]; },
                this
            )
        );
    }

    // Handles a brush event, toggling the display of foreground lines
    _brush(object) {
        let actives = object._dimensions.filter(function (p) { return !object._y[p].brush.empty(); }),
            extents = actives.map(function (p) { return object._y[p].brush.extent(); }),
            visible = [];

        object._foreground.style("display", function (d, j) {
            let isVisible = actives.every(function (p, i) {
                return extents[i][0] <= d[p] && d[p] <= extents[i][1];
            });

            if (isVisible) visible.push(object.real_data[j][0]);
            return isVisible && object._search_results.includes(object._parcoordsToTable(j)) ? null : "none";
        });
        if (actives.length === 0) visible.push("all");

        object.visible = visible;
        object._datatable.draw();
    }
}