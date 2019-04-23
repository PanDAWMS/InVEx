

class MeshVisualization extends DataVisualization{

    constructor(mainDiv, defaultRadius, meshDistance, xCoordinates, yCoordinates){
        super(mainDiv, defaultRadius);

        this.groupOfLabels = new THREE.Group();
        
        this.innerMeshDistance = meshDistance;
        this.proectionSubSpace = [0, 2, 1]
        this.meshCoordinates = [[], [], {}, {}];
        this.objectsOnMesh = [];
        this.visibilityState = [true, true, true, true];
        this.plotly_div = undefined;
        for (var i = 0; i<xCoordinates.length; ++i)
        {
            this.meshCoordinates[0][i] = [xCoordinates[i], i*meshDistance];
            this.objectsOnMesh.push([]);
            this.meshCoordinates[2][xCoordinates[i]] = i;
        }
        for (var i = 0; i<yCoordinates.length; ++i)
        {
            this.meshCoordinates[1][i] = [yCoordinates[i], i*meshDistance];
            this.meshCoordinates[3][yCoordinates[i]] = i;
        }
    }

    saveParameters(){
        var params = super.saveParameters();
        params['indist'] = this.innerMeshDistance;
        return params;
    }
    
    loadParameters(parametersDict){
		super.loadParameters(parametersDict)
		if ('indist' in parametersDict)
			this.changeDistance(parametersDict['indist']);
    }

    // #region GUI related

    // Creates dimension control elements with selectors.
	dimensionControlElements() {
		var dimensionControlID = 'dimensionControl';
		while(document.getElementById(dimensionControlID)!==null)
			dimensionControlID+=(Math.random()*10).toString().slice(-1);

		var form = createControlBasics('form' + dimensionControlID);

		var selectbox = document.createElement('select');
		selectbox.classList.add('form-control', 'form-control-sm');
		selectbox.id = 'y_' + dimensionControlID;
		selectbox.name = 'y_' + dimensionControlID;
		selectbox.style.color = 'green';
        form.groupDiv.appendChild(selectbox);
        
        for ( var j = 2; j < this.dimNames.length; j++ ) { // Create options for all the dimensions
            var option = document.createElement("option");
            if ( this.proectionSubSpace[ 1 ] == j )
                option.selected = true;
            option.value = j.toString();
            option.text = this.dimNames[ j ];
            selectbox.add(option);
        }
		
        var changeDimBtn = document.createElement('input'); //Create button to change the dimension
		changeDimBtn.id = 'button' + dimensionControlID;
		changeDimBtn.setAttribute('type', 'button');
		changeDimBtn.value = 'Change Dimensions';
		changeDimBtn.title = 'This may take some time';
		changeDimBtn.classList.add('button', 'small');
        changeDimBtn.sceneObject = this;
		changeDimBtn.dimsSelect = selectbox;
		changeDimBtn.onclick=function(){
			this.sceneObject.setNewSubSpace(parseInt(this.dimsSelect.value));
		};
		form.appendChild(changeDimBtn);

		return form;
    }

    //Creates the change distance controls.
    changeDistanceControls() {
        var distChangeID = 'distanceChange';
        while(document.getElementById(distChangeID)!==null)
            distChangeID += (Math.random()*10).toString().slice(-1);
        
        var form = createControlBasics('form' + distChangeID);

        var changeDistanceBtn = document.createElement('input');
        changeDistanceBtn.id = 'button' + distChangeID;
        changeDistanceBtn.classList.add('button', 'small');
        changeDistanceBtn.value = 'Change Distance';
        changeDistanceBtn.setAttribute('type', 'button');

        var distanceRange = document.createElement('input');
        changeDistanceBtn.id = 'range' + distChangeID;
        distanceRange.classList.add('custom-range');
        distanceRange.setAttribute('type', 'range');
        distanceRange.min = 0.2;
        distanceRange.max = 9;
        distanceRange.step = 0.1;

        var label = document.createElement('label');
        label.id = 'for' + distanceRange.id;
        label.setAttribute('for', distanceRange.id);
        label.innerText = 'Distance between spheres: ';

        changeDistanceBtn.sceneObject = this;
        changeDistanceBtn.distanceRange = distanceRange;
        distanceRange.value = this.innerMeshDistance.toString();
        changeDistanceBtn.onclick = function() {
            this.sceneObject.changeDistance(parseFloat(this.distanceRange.value));
            return false;
        };

        form.groupDiv.appendChild(label);
        form.groupDiv.appendChild(distanceRange);
        form.groupDiv.appendChild(changeDistanceBtn);

        return form;
    }
    
	//General function to create all the scene controls
    createControlElements(dimensionControlElement, sceneControlElement, multiChoiceControl, multiChoiceTab, fullload=true) {
        if(fullload){
			dimensionControlElement.appendChild(this.dimensionControlElements());
			this.printControls();
		}
        sceneControlElement.appendChild(this.changeDistanceControls());
        sceneControlElement.appendChild(this.changeRadiusControls());
        sceneControlElement.appendChild(this.interactionModeControls(multiChoiceControl, multiChoiceTab));
        sceneControlElement.appendChild(this.changeThemeControls());
        sceneControlElement.appendChild(this.changeQualityControls());
        sceneControlElement.appendChild(this.resetControls());
    }

    createCoordinatesTables(xCoordinateTab, yCoordinateTab){
        var xtable = createDataTable(xCoordinateTab, "xCoordinate-table", ['X Coordinate']);
        for(var i=0; i<this.meshCoordinates[0].length; ++i){
            var row = addElementToDataTable(xtable, [this.meshCoordinates[0][i][0]], 'x'+i.toString());
            row.sceneObject = this;
            row.meshRowNumber = i;
            row.onclick = function(){
                this.sceneObject.selectXRow(this.meshRowNumber);
            }
        }
        xtable.dataTableObj = $('#'+xtable.id).DataTable();

        var ytable = createDataTable(yCoordinateTab, "yCoordinate-table", ['Y Coordinate']);
        for(var i=0; i<this.meshCoordinates[1].length; ++i){
            var row = addElementToDataTable(ytable, [this.meshCoordinates[1][i][0]],  'y'+i.toString());
            row.sceneObject = this;
            row.meshRowNumber = i;
            row.onclick = function(){
                this.sceneObject.selectYRow(this.meshRowNumber);
            }
        }
        ytable.dataTableObj = $('#'+ytable.id).DataTable();
        return [xtable, ytable];
    }

    createDataOnSceneElements(parentElement){
        var greenSwitch=createSwitch('green_switch', 'green', 'Green spheres', 'medium', true, 'On', 'Off');
        var blueSwitch=createSwitch('blue_switch', 'blue', 'Blue spheres', 'medium', true, 'On', 'Off');
        var yellowSwitch=createSwitch('yellow_switch', 'yellow', 'Yellow spheres', 'medium', true, 'On', 'Off');
        var redSwitch=createSwitch('red_switch', 'red', 'Red spheres', 'medium', true, 'On', 'Off');
        greenSwitch.inputElement.sceneObj=this;
        greenSwitch.inputElement.onchange=function(){
            if(this.checked)
                this.sceneObj.visibilityState[0]=true;
            else
                this.sceneObj.visibilityState[0]=false;
            this.sceneObj.changeVisibilityAll();
        };

        blueSwitch.inputElement.sceneObj=this;
        blueSwitch.inputElement.onchange=function(){
            if(this.checked)
                this.sceneObj.visibilityState[1]=true;
            else
                this.sceneObj.visibilityState[1]=false;
            this.sceneObj.changeVisibilityAll();
        };
        
        yellowSwitch.inputElement.sceneObj=this;
        yellowSwitch.inputElement.onchange=function(){
            if(this.checked)
                this.sceneObj.visibilityState[2]=true;
            else
                this.sceneObj.visibilityState[2]=false;
            this.sceneObj.changeVisibilityAll();
        };

        redSwitch.inputElement.sceneObj=this;
        redSwitch.inputElement.onchange=function(){
            if(this.checked)
                this.sceneObj.visibilityState[3]=true;
            else
                this.sceneObj.visibilityState[3]=false;
            this.sceneObj.changeVisibilityAll();
        };

        parentElement.appendChild(greenSwitch);
        parentElement.appendChild(blueSwitch);
        parentElement.appendChild(yellowSwitch);
        parentElement.appendChild(redSwitch);
    }

    createRangeGroup(form, selectelement, startvalueindex){
		for ( var k = 2; k < this.dimNames.length; k++ ) {
			//Create the option element and the div element assosiated with it.
			var option_element = document.createElement('option');
			option_element.innerText = this.dimNames[k];
			option_element.value = startvalueindex+k;
			selectelement.appendChild(option_element);
			var element_div = document.createElement('div');
			element_div.classList.add("form-group");
			option_element.div = element_div;
			selectelement.elements.push(element_div);
			
            var inputid = 'inp'+form.id+option_element.value;
			while(document.getElementById(inputid)!==null)
				inputid += (Math.random()*10).toString().slice(-1);
			
			var input = document.createElement("input");
			input.setAttribute("type", "number");
			input.classList.add("form-control", "form-control-sm");
			input.id = inputid+'min';
			input.min = this.realStats[1][1][k-2];
			input.max = this.realStats[1][2][k-2];
			input.step = (this.realStats[1][2][k-2] - this.realStats[1][1][k-2])/100;
			input.value = this.realStats[1][3][k-2];
			var label = document.createElement('label');
			label.setAttribute("for", input.id);
			label.textContent = 'Min';
			label.classList.add("control-label");
			element_div.appendChild(label);
			input.labelText = 'Min';
			element_div.appendChild(input);
			element_div.mininput = input;
		
			input = document.createElement("input");
			input.setAttribute("type", "number");
			input.classList.add("form-control", "form-control-sm");
			input.id = inputid+'max';
			input.min = this.realStats[1][1][k-2];
			input.max = this.realStats[1][2][k-2];
			input.step = (this.realStats[1][2][k-2] - this.realStats[1][1][k-2])/100.0;
			input.value = this.realStats[1][3][k-2];
			var label = document.createElement('label');
			label.setAttribute("for", input.id);
			label.textContent = 'Max';
			label.classList.add("control-label");
			element_div.appendChild(label);
			input.labelText = 'Max';
			element_div.appendChild(input);
			element_div.maxinput = input;

			element_div.dataNumber = k;
			element_div.sceneObject = this;
            element_div.feature_name = this.dimNames[k];
			element_div.submitfunction = function(color){
                var determFunction=function(sphere, parameters){
					return (sphere.realData[1][parameters[0]]>=parameters[1]) && (sphere.realData[1][parameters[0]]<=parameters[2]);
				}
				var group = this.sceneObject.getSphereGroup(determFunction, [this.dataNumber, this.mininput.value, this.maxinput.value]);
				this.group_id = this.sceneObject.changeColorGroup(group, new THREE.Color(color));
				this.sceneObject.addSelectionsHistory(this.dataNumber,
					   								  this.feature_name,
												      [this.mininput.value, this.maxinput.value],
													  color,
													  this.group_id,
													  'range');
				this.sceneObject.updateHistoryPanel();
			}
			form.appendChild(element_div);
            element_div.classList.add('hide');
		}
    }

    createChartjsCharts(){
        var chartjs_div = document.createElement('div');
        chartjs_div.sceneobj = this;
        this.chartjs_div = chartjs_div;

        var chartjs_config = {
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
        
        var chartjs_div_source_id = 'chartjs_chart_source';
        while(document.getElementById(chartjs_div_source_id)!==null)
            chartjs_div_source_id += (Math.random()*10).toString().slice(-1);
        var chartjs_div_source = document.createElement('div');
        chartjs_div_source.id = chartjs_div_source_id;
        chartjs_div_source.classList.add('hide');
        chartjs_div_source.datasets = [];
        var source_labels = Object.keys(this.meshCoordinates[3]).sort();

        var chartjs_canvas_source = document.createElement('canvas');
        chartjs_canvas_source.id = chartjs_div_source_id + 'canvas';
        chartjs_div_source.appendChild(chartjs_canvas_source);
        var source_chartjs = new Chart(chartjs_canvas_source, {
            type:'bar',
            data: {
                labels: source_labels,
                datasets: []
            },
            options: chartjs_config,
        });
        source_chartjs.parameters_order = source_labels;
        

        var chartjs_div_destination_id = 'chartjs_chart_destination';
        while(document.getElementById(chartjs_div_destination_id)!==null)
            chartjs_div_destination_id += (Math.random()*10).toString().slice(-1);
        var chartjs_div_destination = document.createElement('div');
        chartjs_div_destination.id = chartjs_div_destination_id;
        chartjs_div_destination.classList.add('hide');
        chartjs_div_destination.datasets = [];
        var destination_labels = Object.keys(this.meshCoordinates[2]).sort();

        var chartjs_canvas_destination = document.createElement('canvas');
        chartjs_canvas_destination.id = chartjs_div_destination_id + 'canvas';
        chartjs_div_destination.appendChild(chartjs_canvas_destination);
        var destination_chartjs = new Chart(chartjs_canvas_destination, {
            type:'bar',
            data: {
                labels: destination_labels,
                datasets: []
            },
            options: chartjs_config,
        });
        destination_chartjs.parameters_order = destination_labels;

        chartjs_div.appendChild(chartjs_div_source);
        chartjs_div.appendChild(chartjs_div_destination);
        chartjs_div.source_div = chartjs_div_source;
        chartjs_div.destination_div = chartjs_div_destination;
        chartjs_div.source_chart = source_chartjs;
        chartjs_div.destination_chart = destination_chartjs;

        chartjs_div.add_data_source=function(numb_row, group_color="#000000"){
            var x_dim = this.source_chart.parameters_order;
            var data = [];
            var colors = [];
            for(var i=0; i<x_dim.length; ++i){
                if (this.sceneobj.meshCoordinates[3][x_dim[i]] in this.sceneobj.objectsOnMesh[numb_row]){
                    data.push(this.sceneobj.objectsOnMesh[numb_row][this.sceneobj.meshCoordinates[3]
                        [x_dim[i]]][0].dataObject[1][2]);
                }
                else{
                    data.push(0);
                }
                colors.push(group_color);
            }
            var dataset = {
                label: this.sceneobj.meshCoordinates[0][numb_row][0],
                data: data,
                backgroundColor: colors,
            };
            this.source_chart.data.datasets.push(dataset);
            this.source_div.datasets.push(dataset);
            this.source_chart.update();
            this.source_div.classList.remove('hide');
        }

        chartjs_div.add_data_destination=function(numb_row, group_color="#000000"){
            var x_dim = this.source_chart.parameters_order;
            var data = [];
            var colors = [];
            for(var i=0; i<x_dim.length; ++i){
                if (this.sceneobj.meshCoordinates[2][x_dim[i]] in this.sceneobj.objectsOnMesh[numb_row]){
                    data.push(this.sceneobj.objectsOnMesh[numb_row][this.sceneobj.meshCoordinates[2]
                        [x_dim[i]]][0].dataObject[1][2]);
                }
                else{
                    data.push(0);
                }
                colors.push(group_color);
            }
            var dataset = {
                label: this.sceneobj.meshCoordinates[1][numb_row][0],
                data: data,
                backgroundColor: colors,
            };
            this.destination_chart.data.datasets.push(dataset);
            this.destination_div.datasets.push(dataset);
            this.destination_chart.update();
            this.destination_div.classList.remove('hide');
        }
        
        return chartjs_div;
    }
    
    createPlotlyCharts(){
        var plotly_div = document.createElement('div');
        plotly_div.sceneobj = this;
        this.plotly_div = plotly_div;

        var plotly_config = {displayModeBar: true, responsive: true};

        var plotly_div_source_id = 'plotly_chart_source';
        while(document.getElementById(plotly_div_source_id)!==null)
            plotly_div_source_id += (Math.random()*10).toString().slice(-1);
        var plotly_div_source = document.createElement('div');
        plotly_div_source.id = plotly_div_source_id;
        plotly_div_source.classList.add('hide');
        plotly_div_source.traces = [];
        Plotly.newPlot(plotly_div_source, [], {title:'Sources', showlegend:true, autosize: true,
        xaxis: {
          tickangle: -90
        },
        yaxis: {
          zeroline: false,
          gridwidth: 2
        }}, plotly_config);
        

        var plotly_div_destination_id = 'plotly_chart_destination';
        while(document.getElementById(plotly_div_destination_id)!==null)
            plotly_div_destination_id += (Math.random()*10).toString().slice(-1);
        var plotly_div_destination = document.createElement('div');
        plotly_div_destination.id = plotly_div_destination_id;
        plotly_div_destination.classList.add('hide');
        plotly_div_destination.traces = [];
        Plotly.newPlot(plotly_div_destination, [], {title:'Destinations', showlegend:true, autosize: true,
        xaxis: {
          tickangle: -90
        },
        yaxis: {
          zeroline: false,
          gridwidth: 2
        },
        }, plotly_config);

        plotly_div.appendChild(plotly_div_source);
        plotly_div.appendChild(plotly_div_destination);
        plotly_div.source_plot = plotly_div_source;
        plotly_div.destination_plot = plotly_div_destination;

        plotly_div.add_data_source=function(numb_row, group_color="#000000"){
            var x_dim = Object.keys(this.sceneobj.meshCoordinates[3]).sort();
            var y_dim = [];
            var text_dim = [];
            for(var i=0; i<x_dim.length; ++i){
                if (this.sceneobj.meshCoordinates[3][x_dim[i]] in this.sceneobj.objectsOnMesh[numb_row]){
                    y_dim.push(this.sceneobj.objectsOnMesh[numb_row][this.sceneobj.meshCoordinates[3]
                        [x_dim[i]]][0].dataObject[1][2]);
                    text_dim.push(this.sceneobj.objectsOnMesh[numb_row][this.sceneobj.meshCoordinates[3]
                            [x_dim[i]]][0].realData[1][2]);
                }
                else{
                    y_dim.push(0);
                    text_dim.push("N/A");
                }
            }
            var trace = {
                x: x_dim,
                y: y_dim,
                type: 'bar',
                text: text_dim,
                name: this.sceneobj.meshCoordinates[0][numb_row][0],
                marker: {
                  color: group_color
                }
            };
            Plotly.addTraces(this.source_plot, trace);
            this.source_plot.traces.push(trace);
            this.source_plot.classList.remove('hide');
        }

        plotly_div.add_data_destination=function(numb_row, group_color="#000000"){
            var x_dim = Object.keys(this.sceneobj.meshCoordinates[2]).sort();
            var y_dim = [];
            var text_dim = [];
            for(var i=0; i<x_dim.length; ++i){
                if (this.sceneobj.meshCoordinates[2][x_dim[i]] in this.sceneobj.objectsOnMesh[numb_row]){
                    y_dim.push(this.sceneobj.objectsOnMesh[numb_row][this.sceneobj.meshCoordinates[2]
                        [x_dim[i]]][0].dataObject[1][2]);
                    text_dim.push(this.sceneobj.objectsOnMesh[numb_row][this.sceneobj.meshCoordinates[2]
                            [x_dim[i]]][0].realData[1][2]);
                }
                else{
                    y_dim.push(0);
                    text_dim.push("N/A");
                }
            }
            var trace = {
                x: x_dim,
                y: y_dim,
                type: 'bar',
                text: text_dim,
                name: this.sceneobj.meshCoordinates[1][numb_row][0],
                marker: {
                  color: group_color
                }
            };
            Plotly.addTraces(this.destination_plot, trace);
            this.destination_plot.traces.push(trace);
            this.destination_plot.classList.remove('hide');
        }
        
        return plotly_div;
    }
    
    //#endregion
    //#region User interaction
    checkState(realData){
        if (realData[1][this.proectionSubSpace[1]]<=this.realStats[1][3][this.proectionSubSpace[1]-2])
            return 0;
        var per = (realData[1][this.proectionSubSpace[1]]-this.realStats[1][3][this.proectionSubSpace[1]-2])/(this.realStats[1][2][this.proectionSubSpace[1]-2]-this.realStats[1][3][this.proectionSubSpace[1]-2]);
        if(per>0.8)
            return 3;
        if(per>0.5)
            return 2;
        return 1;
    }

    createColorScheme(){
        return Object.assign({}, this.customColors, {0: new THREE.Color(0x00FF00), 1: new THREE.Color(0x0000FF), 2: new THREE.Color(0xFFFF00), 3: new THREE.Color(0xFF0000)});
    }

    changeState(sphere){
        sphere.dataObject[2][sphere.dataObject[2].length - 1] = this.checkState(sphere.realData);
    }

    changeVisibilitySphere(sphere){
        if(this.visibilityState[this.checkState(sphere.realData)]){
			sphere.visible = true;
			if (sphere.selectedCircut != undefined)
				sphere.selectedCircut.visible = true;
		}
		else{
			sphere.visible = false;
			if (sphere.selectedCircut != undefined)
                sphere.selectedCircut.visible = false;
		}
    }

    //Creates a sphere on the scene, adds the data to the sphere and the sphere to the data.
    createSphere(normData, realData, cluster, auxData) {
        if (!((normData[1][0] in this.meshCoordinates[2]) && (normData[1][1] in this.meshCoordinates[3])))
            return null;
        var i = this.meshCoordinates[2][normData[1][0]];
        var j = this.meshCoordinates[3][normData[1][1]];
        if (Array.isArray(cluster))
            normData[2] = cluster;
        else
            normData[2] = [this.checkState(realData)];
		var material = new THREE.MeshPhongMaterial( {color: this.clusters_color_scheme[normData[2][0]].clone()} );
		var sphere = new THREE.Mesh(this.sphereGeometry, material);
		sphere.position.x = this.meshCoordinates[0][i][1];
		sphere.position.y = normData[1][this.proectionSubSpace[1]];
        sphere.position.z = this.meshCoordinates[1][j][1];
        if (this.objectsOnMesh[i][j] == undefined)
            this.objectsOnMesh[i][j] = [];
        this.objectsOnMesh[i][j].push(sphere);
		normData[3] = sphere;
		realData[3] = sphere;
		auxData[3] = sphere;
		sphere.dataObject = normData;
		sphere.realData = realData;
		sphere.auxData = auxData;
		this.groupOfSpheres.add(sphere);
		return sphere;
    }

    selectXRow(number){
        this.unSelectAllObjects();
        for(var i=0; i<this.objectsOnMesh[number].length; ++i){
            if (this.objectsOnMesh[number][i]!=undefined){
                for(var k=0; k<this.objectsOnMesh[number][i].length; ++k){
                    this.selectObject(this.objectsOnMesh[number][i][k]);
                }
            }
        }
    }

    selectYRow(number){
        this.unSelectAllObjects();
        for(var i=0; i<this.objectsOnMesh.length; ++i){
            if (this.objectsOnMesh[i][number]!=undefined){
                for(var k=0; k<this.objectsOnMesh[i][number].length; ++k){
                    this.selectObject(this.objectsOnMesh[i][number][k]);
                }
            }
        }
    }

    
    changeDistance(meshDistance){
        this.innerMeshDistance = meshDistance;
        for (var i = 0; i<this.meshCoordinates[0].length; ++i)
            this.meshCoordinates[0][i][1] =  i*meshDistance;
        for (var i = 0; i<this.meshCoordinates[1].length; ++i)
            this.meshCoordinates[1][i][1] = i*meshDistance;
        this.moveSpheres()
    }

    redrawScene(){
        if (this.meshCoordinates != undefined){
            this.objectsOnMesh = [];
            for (var i = 0; i<this.meshCoordinates[0].length; ++i)
            {
                this.objectsOnMesh.push([]);
            }
        }
        super.redrawScene()
    }
    
    moveSpheres() {
        for(var i=0; i<this.objectsOnMesh.length; ++i)
            for(var j=0; j<this.objectsOnMesh[i].length; ++j)
                if(this.objectsOnMesh[i][j] != undefined)
                    for(var k=0; k<this.objectsOnMesh[i][j].length; ++k){
                        this.objectsOnMesh[i][j][k].position.x = this.meshCoordinates[0][i][1];
                        this.objectsOnMesh[i][j][k].position.y = this.objectsOnMesh[i][j][k].dataObject[1][this.proectionSubSpace[1]];
                        this.objectsOnMesh[i][j][k].position.z = this.meshCoordinates[1][j][1];
                        this.changeState(this.objectsOnMesh[i][j][k]);
                        if (this.objectsOnMesh[i][j][k].selectedCircut != undefined){
                            this.objectsOnMesh[i][j][k].selectedCircut.position.x = this.objectsOnMesh[i][j][k].position.x;
                            this.objectsOnMesh[i][j][k].selectedCircut.position.y = this.objectsOnMesh[i][j][k].position.y;
                            this.objectsOnMesh[i][j][k].selectedCircut.position.z = this.objectsOnMesh[i][j][k].position.z;
                            this.objectsOnMesh[i][j][k].material.color = invertColor(this.clusters_color_scheme[this.objectsOnMesh[i][j][k].dataObject[2][0]].clone()); 
                        }
                        else
                            this.objectsOnMesh[i][j][k].material.color = this.clusters_color_scheme[this.objectsOnMesh[i][j][k].dataObject[2][0]].clone(); 
                    }
    }
    
    setNewSubSpace(x2){
        super.setNewSubSpace(0, x2, 1);
		this.moveSpheres();
    }

    updateHistoryPanel() {
		var form = document.getElementById("history");
		this.cleanElement("history");
		if (this.selectionsHistory.length > 0) {
			for (var i = 0; i < this.selectionsHistory.length; i++) {
				var p = document.createElement('p');
				if (this.selectionsHistory[i]['value'])
					p.innerText = this.selectionsHistory[i]['selected_feature'] + " = " + this.selectionsHistory[i]['value'];
				else if (this.selectionsHistory[i]['min'])
					p.innerText = this.selectionsHistory[i]['selected_feature'] + " : " + this.selectionsHistory[i]['min'] + ' - ' + this.selectionsHistory[i]['max'];
				form.appendChild(p);
				var div = document.createElement('div');
				div.classList.add('switch', 'tiny');
				var input = document.createElement('input');
				input.classList.add('switch-input');
				input.setAttribute('id','on-off-'+i);
				input.historyID = i;
				input.type = 'checkbox';
				input.name = 'exampleSwitch';
				var label = document.createElement('label');
				label.classList.add('switch-paddle');
				label.setAttribute('for','on-off-'+i);
				label.style.backgroundColor = this.selectionsHistory[i]['color'];
				var span = document.createElement('span');
				span.classList.add('show-for-sr');
				span.innerText = p.innerText;
				var on = document.createElement('span');
				on.classList.add('switch-active');
				on.setAttribute('aria-hidden', 'true');
				on.innerText = 'on';
				var off = document.createElement('span');
				off.classList.add('switch-inactive');
				off.setAttribute('aria-hidden', 'true');
				off.innerText = 'off';
				label.appendChild(span);
				label.appendChild(on);
				label.appendChild(off);
				div.appendChild(input);
				div.appendChild(label);
				form.appendChild(p);
				form.appendChild(div);

				var self = this;
				var id = i;
				input.onchange=function(event){
                    self.selectionsHistory[this.historyID]['active'] = !this.checked;
				};
			}
			var updateBtn = document.createElement('input');
				updateBtn.id = 'updateBtn';
				updateBtn.classList.add('button', 'small');
				updateBtn.value = 'Update Colors';
				updateBtn.setAttribute('type', 'button');
				updateBtn.onclick = function(event) {
					event.preventDefault();
                    var group_data = [];
                    for (var i = 0; i<self.groupOfSpheres.children.length; i++) {
                        var groups_number = self.groupOfSpheres.children[i].dataObject[2].length;
                        var initial_group = self.groupOfSpheres.children[i].dataObject[2][groups_number - 1];
                        self.groupOfSpheres.children[i].material.color = self.clusters_color_scheme[initial_group].clone();
                    }
                    for (var i = 0; i < self.selectedObject.children.length; i++ ) {
                        var groups_number = self.selectedObject.children[i].dataObject[2].length;
                        var initial_group = self.selectedObject.children[i].dataObject[2][groups_number - 1];
                        self.selectedObject.children[i].material.color = invertColor(self.clusters_color_scheme[initial_group].clone());
                    }
					for (var i = 0; i < self.selectionsHistory.length; i++) {
						var selected_spheres = [];
						var feature_id = self.selectionsHistory[i]['feature_id'];
						var type = self.selectionsHistory[i]['type'];
						var group = self.selectionsHistory[i]['group'];

						// get IDs of selected features from history
						if (type == 'range') {
							selected_spheres = self.chosenSpheres(self.groupOfSpheres.children,
								feature_id,
								[self.selectionsHistory[i]['min'],
								self.selectionsHistory[i]['max']],
								self.selectionsHistory[i]['type']);
						}
						else if (type == 'categorical') {
							selected_spheres = self.chosenSpheres(self.groupOfSpheres.children,
								feature_id,
								[self.selectionsHistory[i]['value']],
								self.selectionsHistory[i]['type']);
						}
                        if (self.selectionsHistory[i]['active'] == true) {
							for (var x = 0; x < selected_spheres.length; x++)
                                selected_spheres[x].material.color = self.clusters_color_scheme[group].clone();
                            for (var x = 0; x < self.selectedObject.children.length; x++ )
                                self.selectedObject.children[x].material.color = invertColor(self.clusters_color_scheme[group].clone());
							group_data[group] = self.getGroupsMeans(selected_spheres);
						}
					}
					drawMultipleGroupRadarChart('radar_chart_groups', group_data, self.selectionsHistory, self.dimNames.slice(2), 100);
				}
			var clearHistoryBtn = document.createElement('input');
				clearHistoryBtn.id = 'clearHistBtn';
				clearHistoryBtn.classList.add('button', 'small');
				clearHistoryBtn.value = 'Clear Color History';
				clearHistoryBtn.setAttribute('type', 'button');
				clearHistoryBtn.onclick = function(event) {
					event.preventDefault();
					self.cleanElement('history');
					self.resetAllColorGroups();
					self.selectionsHistory = [];
				}

			form.appendChild(updateBtn);
			form.appendChild(clearHistoryBtn);
		}
	}

    getGroupsMeans(group) {
        var norm_data = [];
        var real_data = [];
        for (var i=0; i<group.length; i++) {
            var id = group[i].dataObject[0];
            norm_data.push(group[i].dataObject[1].slice(2));
            for (var j = 0; j<this.realData.length;j++) {
                if (this.realData[j][0] == id)
                    real_data.push(this.realData[j][1].slice(2));
            }
        }
        // transpose array
        var norm_result = Array.from({ length: norm_data[0].length }, function(x, row) {
          return Array.from({ length: norm_data.length }, function(x, col) {
            return norm_data[col][row];
          });
        });
        var real_result = Array.from({ length: real_data[0].length }, function(x, row) {
          return Array.from({ length: real_data.length }, function(x, col) {
            return real_data[col][row];
          });
        });
        var norm_mean_values = [];
        for (var i = 0; i < norm_result.length; i++)
            norm_mean_values.push(ss.mean(norm_result[i]));
        var real_mean_values = [];
        for (var i = 0; i < real_result.length; i++)
            real_mean_values.push(ss.mean(real_result[i]));

        return [norm_mean_values, real_mean_values];
    }

    //#endregion
}