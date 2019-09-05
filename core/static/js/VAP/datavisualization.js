// Sends Ajax 
function sendAjaxPredictRequest(selectedObject, otherData, sceneObj){
	var data = { formt: 'rebuild', data: JSON.stringify(selectedObject.dataObject[1])};
	var allData = Object.assign.apply({}, [data, otherData]);
	$.ajax({
				type:"POST",
				url: "",
				data : allData,
				success : function(results_dict) {
					scene.changeCluster(selectedObject, results_dict['results'][0]);
				},
				failure: function(data) {
					alert('There was an error. Sorry');
				}
			})
}

//calculates a color scheme for clusters. Clusters have to be an array, the result is a dictionary
function getColorScheme(clusters, theme = 'black') {

    /* colors: (230, 25, 75), (60, 180, 75), (0, 130, 200),
        (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230),
        (210, 245, 60), (250, 190, 190), (0, 128, 128), (230, 190, 255),
        (170, 110, 40), (255, 250, 200), (128, 0, 0), (170, 255, 195),
        (128, 128, 0), (255, 215, 180), (0, 0, 128), (255, 225, 25)*/

    var _red = [230, 60, 0, 245, 145, 70, 240, 210, 250, 0, 230, 170, 255, 128, 170, 128, 255, 0, 255, 0],
        _green = [25, 180, 130, 130, 30, 240, 50, 245, 190, 128, 190, 110, 250, 0, 255, 128, 215, 0, 225, 128],
        _blue = [75, 75, 200, 48, 180, 240, 230, 60, 190, 128, 255, 40, 200, 0, 195, 0, 180, 128, 25, 64];

    var clusters_unique = [...new Set(clusters)].sort((a, b) => a - b),
        len = clusters_unique.length,
        results = {};

    //console.log(clusters, clusters_unique, len);

    if (len === 1) 
        results[clusters_unique[0]] = theme === 'white' ?
            new THREE.Color(0, 0, 0) :
            new THREE.Color(1, 1, 1);
	else
        if (len === 2) {
            results[clusters_unique[0]] = new THREE.Color(1, 0, 0);
            results[clusters_unique[1]] = new THREE.Color(0, 0, 1);
        } else
            if (len < 21) 
                for (var i = 0; i < len; i++)
                    results[clusters_unique[i]] =
                            new THREE.Color("rgb(" + _red[i] + ', ' + _green[i] + ', ' + _blue[i] + ")");
            else {
                // code the clusters as a 3-digits number in base-base number system. 
                var parts = Math.round(Math.log(len)/Math.log(3)+0.5);
                var count_of_encoded_colors = Math.pow(parts, 3);
                if (parts+len > count_of_encoded_colors)
                    parts = parts + 1;
                var base = parts - 1;
                if (base == 0)
                    base = 1;
                var red, green, blue, skipped=0;
                //console.log({'parts':parts, 'base':base, 'count_of_encoded_colors':count_of_encoded_colors});
                for( var i = 0; i < len; i++ ) {
                    if (theme=='white'){
                        red = (~~((i+skipped)/(parts*parts)))%parts/base*0.8;
                        green = (~~((i+skipped)/parts))%parts/base*0.8;
                        blue = (i+skipped)%parts/base*0.8;
                    }
                    else {
                        red = 1-(~~((i+skipped)/(parts*parts)))%parts/base;
                        green = 1-(~~((i+skipped)/parts))%parts/base;
                        blue = 1-(i+skipped)%parts/base;
                    }
                    if (red==green && green==blue){
                        i--;
                        skipped++;
                    }
                    else
                       results[clusters_unique[i]] = new THREE.Color(red, green, blue);
                }
        }
    //console.log(results);
	return results;
}

function prepareUniqueData(data){
	// select unique values for categorical feature
	var setarr=[];
	for(var i=0; i<data[0][1].length; ++i){
		setarr.push(new Set());
	}

	for(var j=0; j<data.length; ++j){
		for(var i=0; i<data[j][1].length; ++i){
			setarr[i].add(data[j][1][i]);
		}
	}

	var result=[];
	for(var i=0; i<data[0][1].length; ++i){
		result.push(Array.from(setarr[i]));
	}
	return result;
}

class DataVisualization extends Scene{
 
    // #region Initialization
    constructor(mainDiv, defaultRadius){
        super(mainDiv);

        //initialize the parameters for data analysis
        this.index = '';
        this.normData = [];
        this.realData = [];
        this.auxData = [];
        this.auxNames = [];
        this.lodData = [];
        this.realStats = [];
        this.selectionsHistory = [];
        this.interactiveMode = 'single';
        
        //Set up the quality ranges and parameters for each quality.
        this.__qualityRange = [{'value':'exlow', 'text':'Extra low', 'segs':5}, 
        {'value':'low', 'text':'Low', 'segs':10},
        {'value':'med', 'text':'Medium', 'segs':15},
        {'value':'high', 'text':'High', 'segs':25},
        {'value':'exhigh', 'text':'Extra high', 'segs':40}];
		
		//Creates the ThreeJS groups 
        this.groupOfSpheres = new THREE.Group();
        this.scene.add(this.groupOfSpheres);
        this.selectedObject = new THREE.Group();
        this.scene.add(this.selectedObject);
        this.groupOfSelectOutlines = new THREE.Group();
        this.scene.add(this.groupOfSelectOutlines);

		this.clusters = undefined;
		
		this.customColors={};
		
		//Creates raycaster and mouse vector to calculate the click destination
        this.raycaster = new THREE.Raycaster();
        this.mouseVector = new THREE.Vector3();
        this.dragControls = null;
        this.dragEnabled = false;

        this.defaultSpRad = defaultRadius;

		//Sets the listener for mouse click
        mainDiv.addEventListener("click", function (event) { this.sceneObject.onMouseClick(event); }, false);
        mainDiv.addEventListener("touchend", function (event) { this.sceneObject.onTouchEnd(event); }, false);
        mainDiv.addEventListener("pointermove", function (event) { this.sceneObject.onPointerMove(event); }, false);
        this.changeTheme(this.theme);
        this.changeQuality(this.quality);
    }

    saveParameters() {
        var params = super.saveParameters();
        params['sphrad'] = this.defaultSpRad;
        return params;
    }
    
    loadParameters(parametersDict){
		super.loadParameters(parametersDict)
		if ('sphrad' in parametersDict)
			this.changeRad(parametersDict['sphrad']);
    }
    
    setClusters(clusters){
		this.clusters = clusters;
	}

	setIndex(idx) {
		this.index = idx;
    }

    setDataArray(normData) {
        this.normData = normData;
    }

	setRealData(realData) {
		this.realData = realData;
	}

	setRealStats(stats) {
		this.realStats = stats;
	}

	setAuxiliaryColumns(auxNames) {
		this.auxNames = auxNames;
	}

	setAuxiliaryData(auxData) {
		this.auxData = auxData;
    }

    setLOD(lodData) {
    	this.lodData = lodData;
	}
    
// #endregion
// #region GUI related
	//Creates interaction mode controls. Currently 3 types of controls: Single choise, multiple choice and drag controls.
    interactionModeControls(multiChoiceControl, multiChoiceTab) {
		var interactionModeID = 'interMode';
		while(document.getElementById(interactionModeID)!==null)
			interactionModeID += (Math.random()*10).toString().slice(-1);
		//Form that contains all the controls
		var form = createControlBasics('form' + interactionModeID);
		form.classList.add('text-left');
		//Radio button for single choice
		var singleChoiceRadio = createControlRadioWithLabel('single' + interactionModeID, interactionModeID, 'Activate Single Sphere Selection');
		singleChoiceRadio.sceneObject = this;
		singleChoiceRadio.multiChoiceControl = multiChoiceControl;
		if (this.interactiveMode == 'single')
			singleChoiceRadio.checked = true;
		singleChoiceRadio.onchange = function(event){
			this.sceneObject.setInteractiveMode('single', {});
			this.multiChoiceControl.classList.add('hide');
		};
		//radio button for multiple choice control
		var multiChoiceRadio = createControlRadioWithLabel('multi' + interactionModeID, interactionModeID, 'Activate Multiple Sphere Selection');
		multiChoiceRadio.sceneObject = this;
		multiChoiceRadio.multiChoiceControl = multiChoiceControl;
		multiChoiceRadio.multiChoiceTab = multiChoiceTab;
		if (this.interactiveMode == 'multi')
			multiChoiceRadio.checked = true;
		multiChoiceRadio.onchange = function(event){
			this.sceneObject.setInteractiveMode('multi', {'tabletab': this.multiChoiceTab});
			this.multiChoiceControl.classList.remove('hide');
		};
		//Radio button for drag control
		var dragChoiceRadio = createControlRadioWithLabel('drag' + interactionModeID, interactionModeID, 'Activate Drag Sphere Control');
		dragChoiceRadio.sceneObject = this;
		dragChoiceRadio.multiChoiceControl = multiChoiceControl;
		if (this.interactiveMode == 'drag')
			dragChoiceRadio.checked = true;
		dragChoiceRadio.onchange = function(event){
			this.sceneObject.setInteractiveMode('drag', {});
			this.multiChoiceControl.classList.add('hide');
		};
		
		form.groupDiv.appendChild(singleChoiceRadio);
		form.groupDiv.appendChild(singleChoiceRadio.labelElement);
		form.createNewLine();
		form.groupDiv.appendChild(multiChoiceRadio);
		form.groupDiv.appendChild(multiChoiceRadio.labelElement);
		form.createNewLine();
		form.groupDiv.appendChild(dragChoiceRadio);
		form.groupDiv.appendChild(dragChoiceRadio.labelElement);
		return form;
    }
	
	//Creates the change radius controls.
    changeRadiusControls() {
		var radChangeID = 'radiusChange';
		while(document.getElementById(radChangeID)!==null)
			radChangeID += (Math.random()*10).toString().slice(-1);
		
		var form = createControlBasics('form' + radChangeID);

		var buttonDiv = document.createElement('div');
		buttonDiv.setAttribute("align", "center");

        var radiusRange = document.createElement('input');
        radiusRange.id = 'range' + radChangeID;
		radiusRange.classList.add('custom-range');
		radiusRange.setAttribute('type', 'range');
		radiusRange.min = 0.1;
		radiusRange.max = 3;
		radiusRange.step = 0.1;

		var label = document.createElement('label');
		label.id = 'for' + radiusRange.id;
		label.setAttribute('for', radiusRange.id);
		label.innerText = 'Spheres Radius: ';

        radiusRange.sceneObject = this;
        radiusRange.value = this.defaultSpRad.toString();
        radiusRange.oninput = function () {
			this.sceneObject.changeRad(parseFloat(this.value));
			return false;
		};

		form.groupDiv.appendChild(label);
		form.groupDiv.appendChild(radiusRange);

		return form;
	}

	createResetClustersButton(){
		var resetClustersID = 'resetclusters';
		while(document.getElementById(resetClustersID)!==null)
			resetClustersID += (Math.random()*10).toString().slice(-1);
		
		var form = createControlBasics('form' + resetClustersID);

		var resetClustersBtn = document.createElement('input');
		resetClustersBtn.id = 'button' + resetClustersID;
		resetClustersBtn.classList.add('button', 'small');
		resetClustersBtn.value = 'Reset clusters';
		resetClustersBtn.setAttribute('type', 'button');
		resetClustersBtn.sceneObject = this;
		resetClustersBtn.onclick = function(event) {
			event.preventDefault();
			this.sceneObject.resetClusters();
			this.classList.add('hide');
			return false;
		};
		form.appendChild(document.createElement('br'));
		form.appendChild(resetClustersBtn);
		
		return form;
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

                    var _real_data = [],
                        _clusters_list = [],
                        _clusters_color_scheme = [],
                        selected_spheres, active;

                    for (var i = 0; i < self.selectionsHistory.length; i++) {

                        selected_spheres = self.chosenSpheres(self.groupOfSpheres.children,
                            self.selectionsHistory[i]['feature_id'],
                            ((self.selectionsHistory[i]['type'] == 'range') ?
                                [self.selectionsHistory[i]['min'], self.selectionsHistory[i]['max']] :
                                [self.selectionsHistory[i]['value']]),
                            self.selectionsHistory[i]['type']);

                        active = self.selectionsHistory[i]['active'];

                        if (active) _clusters_color_scheme[i] = self.clusters_color_scheme['group' + i];

                        for (var j = 0; j < selected_spheres.length; j++) {
                            if (active) {
                                _real_data.push(selected_spheres[j].realData);
                                _clusters_list.push(i);
                            }
                            selected_spheres[j].material.color =
                                self.clusters_color_scheme[((active) ? 'group' + i : '0')].clone();
                        }
                    }

                    drawParallelCoordinates('radar_chart_groups', _real_data, _clusters_list, _clusters_color_scheme, self.dimNames);
                    requestAnimationFrame(render)
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
                    requestAnimationFrame(render);
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
            norm_data.push(group[i].dataObject[1]);
            for (var j = 0; j<this.realData.length;j++) {
                if (this.realData[j][0] == id)
                    real_data.push(this.realData[j][1]);
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

	remove(array, element) {
	  const index = array.indexOf(element);

	  if (index !== -1) {
		array.splice(index, 1);
	  }
	}

	resetAllColorGroups() {
		var group_names = [];
		for (var i = 0; i < this.selectionsHistory.length; i++) {
			var group_name = this.selectionsHistory[i]['group'];
			group_names.push(group_name);
			delete this.clusters_color_scheme[group_name];
			for (var j = 0; j < this.groupOfSpheres.children.length; j++ ) {
                this.remove(this.groupOfSpheres.children[j].dataObject[2], group_name);
                var groups_number = this.groupOfSpheres.children[j].dataObject[2].length;
                var initial_group = this.groupOfSpheres.children[j].dataObject[2][groups_number-1];
                this.groupOfSpheres.children[j].material.color = this.clusters_color_scheme[initial_group].clone();
            }
		}
		for (var i = 0; i < this.selectedObject.children.length; i++ ) {
			for (var g=0; g<group_names.length; g++)
				this.remove(this.selectedObject.children[i].dataObject[2], group_names[g]);
			var groups_number = this.selectedObject.children[i].dataObject[2].length;
			var initial_group = this.selectedObject.children[i].dataObject[2][groups_number-1];
			this.selectedObject.children[i].material.color = invertColor(this.clusters_color_scheme[initial_group].clone());
        }

        requestAnimationFrame(render);
	}

	chosenSpheres(spheres, featureID, featureValues, featureType) {
		var chosenSpheres = [];
		if (featureType == 'categorical') {
			var value = featureValues[0];
			for ( var i = 0; i < spheres.length; i++ ) {
				if (spheres[ i ].auxData[ 1 ][ featureID ] == value) {
					chosenSpheres.push(spheres[ i ]);
				}
			}
		} else if (featureType == 'range') {
			var min = featureValues[0];
			var max = featureValues[1];
			for ( var i = 0; i < spheres.length; i++ ) {
				if (spheres[ i ].realData[ 1 ][ featureID ] >= min &&
					spheres[ i ].realData[ 1 ][ featureID ]< max) {
					chosenSpheres.push(spheres[ i ]);
				}
			}
		}
		return chosenSpheres;
	}

	cleanElement(id) {
		var div = document.getElementById(id);
		while (div.firstChild) {
			div.removeChild(div.firstChild);
		}
	}

	addSelectionsHistory(feature_id, feature_name, feature_value, color, group, type) {
		var history_dict = {};
		history_dict['selected_feature'] = feature_name;
		history_dict['feature_id'] = feature_id;
		history_dict['type'] = type;
		history_dict['color'] = color;
		history_dict['active'] = true;
		history_dict['group'] = group;
		if (type == 'categorical')
			history_dict['value'] = feature_value[0];
		else if (type == 'range') {
			history_dict['min'] = feature_value[0];
			history_dict['max'] = feature_value[1];
		}
		this.selectionsHistory.push(history_dict);
		return history_dict;
	}

	createCategoricalGroup(form, selectelement, startvalueindex){
		var uniquedata = prepareUniqueData(this.auxData);
		for ( var k = 0; k < this.auxNames.length; k++ ) {
			//Create the option element and the div element assosiated with it.
			var option_element = document.createElement('option');
			option_element.innerText = this.auxNames[k];
			option_element.value = startvalueindex + k;
			selectelement.appendChild(option_element);
			var element_div = document.createElement('div');
			element_div.classList.add("form-group");
			option_element.div = element_div;
			selectelement.elements.push(element_div);
			
            var inputid = 'inp'+form.id+option_element.value;
			while(document.getElementById(inputid)!==null)
				inputid += (Math.random()*10).toString().slice(-1);
			
			var input = document.createElement("select");
			input.classList.add("form-control", "form-control-sm");
			input.id = inputid;
			
			//Create options for the select
			for(var i=0; i<uniquedata[k].length; ++i){
				var option = document.createElement('option');
				option.innerText = uniquedata[k][i];
				option.value = uniquedata[k][i];
				input.appendChild(option);
				if (i==0){
					option.selected=true;
				}
			}
			element_div.appendChild(input);

			element_div.input = input;
			element_div.auxNumber = k;
			element_div.feature_name = this.auxNames[k];
			element_div.sceneObject = this;
			element_div.submitfunction = function(color){
				var determFunction=function(sphere, parameters){
					return sphere.auxData[1][parameters[0]]==parameters[1];
				}
				var group = this.sceneObject.getSphereGroup(determFunction, [this.auxNumber, this.input.value]);
				this.group_id = this.sceneObject.changeColorGroup(group, new THREE.Color(color));
				this.sceneObject.addSelectionsHistory(this.auxNumber,
									  this.feature_name,
									  [this.input.value],
									  color,
									  this.group_id,
									  'categorical');
				this.sceneObject.updateHistoryPanel();
			}
			form.appendChild(element_div);
			if (k!=0){
				element_div.classList.add('hide');
			}
			else
				element_div.classList.remove('hide');
		}
	}

	createRangeGroup(form, selectelement, startvalueindex){
		for ( var k = 0; k < this.dimNames.length; k++ ) {
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
			input.min = this.realStats[1][1][k];
			input.max = this.realStats[1][2][k];
			input.step = (this.realStats[1][2][k] - this.realStats[1][1][k])/100;
			input.value = this.realStats[1][3][k];
            input.labelText = 'Min';
			var label = document.createElement('label');
			label.setAttribute("for", input.id);
			label.textContent = 'Min';
			label.classList.add("control-label");
			element_div.appendChild(label);
			element_div.appendChild(input);
			element_div.mininput = input;
		
			input = document.createElement("input");
			input.setAttribute("type", "number");
			input.classList.add("form-control", "form-control-sm");
			input.id = inputid+'max';
			input.min = this.realStats[1][1][k];
			input.max = this.realStats[1][2][k];
			input.step = (this.realStats[1][2][k] - this.realStats[1][1][k])/100.0;
			input.value = this.realStats[1][3][k];
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
			if ((this.auxNames.length!=0)||(k!=0)){
				element_div.classList.add('hide');
			}
			else
				element_div.classList.remove('hide');
		}
	}
	
	createNewGroupElement(){
		var newGroupID = 'groupelements';
		while(document.getElementById(newGroupID)!==null)
			newGroupID += (Math.random()*10).toString().slice(-1);
		
		var form = createControlBasics('form' + newGroupID);
		
		var main_select_element = document.createElement('select');
		main_select_element.classList.add('form-control', 'form-control-sm');
		main_select_element.id = 'select' + newGroupID;
		main_select_element.name = 'algorithm';
		form.appendChild(main_select_element);

		//Adding Aux data
		var elements = [];
		main_select_element.elements = [];

		this.createCategoricalGroup(form, main_select_element, 0);
		this.createRangeGroup(form, main_select_element, this.auxNames.length);

		main_select_element.onchange = function() {
			for( var i = 0; i < this.elements.length; i++ ){
				this.elements[i].classList.add('hide');
			}
			this.selectedOptions[0].div.classList.remove('hide');
		};

		var color_picker = document.createElement("input");
		color_picker.setAttribute("type", "text");
		color_picker.id="colorpicker"+newGroupID;
		color_picker.value='#0000ff';

		var label = document.createElement('label');
		label.setAttribute("for", color_picker.id);
		label.textContent = 'Choose Color: ';
		label.classList.add("control-label");
		label.style.display='inline';
		form.appendChild(label);

		form.appendChild(color_picker);
		form.appendChild(document.createElement('br'));
		form.appendChild(document.createElement('br'));
		form.color_picker = color_picker;

		var changeColorBtn = document.createElement('input');
		changeColorBtn.id = 'colorButton' + newGroupID;
		changeColorBtn.classList.add('button', 'small');
		changeColorBtn.value = 'Change Color';
		changeColorBtn.setAttribute('type', 'button');
		changeColorBtn.colorinput = color_picker;
		changeColorBtn.selectObject = main_select_element;
        var self = this;
		changeColorBtn.onclick = function(event) {
			this.selectObject.selectedOptions[0].div.submitfunction(this.colorinput.value);
			//this.undoButton.classList.remove('hide');
			return false;
		};
		form.appendChild(changeColorBtn);

		form.ready=function(){
			$('#'+this.color_picker.id).spectrum({showPalette: true,
				palette: ["red", "green", "blue", "orange", "yellow", "violet" ],
				showInitial: true,
				preferredFormat: "hex",});
		}

		return form;
	}

	//Assigns print controls
    printControls() {
		var display_clusters = document.getElementById("printBtn");
		if (display_clusters !== null){
			display_clusters.sceneObject = this;
			display_clusters.onclick = function() {
				var element = document.getElementById("cluster-table_wrapper");
				if (element) {
					element.parentNode.removeChild(element);
				}
				this.sceneObject.printClusters(document.getElementById("clusters"));
			};
		}
		
		var display_all_dataset = document.getElementById("printAllBtn");
		if (display_all_dataset !== null){
			display_all_dataset.sceneObject = this;
			display_all_dataset.onclick = function() {
				var element = document.getElementById("print-table_wrapper");
				if (element) {
					element.parentNode.removeChild(element);
				}
				printDataset(document.getElementById("print"), this.sceneObject.index.concat(this.sceneObject.dimNames), this.sceneObject.realData);
			};
		}
    }
	
	//General function to create all the scene controls
    createControlElements(dimensionControlElement, sceneControlElement, multiChoiceControl, multiChoiceTab, fullload=true) {
        if(fullload){
			dimensionControlElement.appendChild(this.dimensionControlElements());
			this.printControls();
		}
        sceneControlElement.appendChild(this.changeRadiusControls());
        sceneControlElement.appendChild(this.interactionModeControls(multiChoiceControl, multiChoiceTab));
        sceneControlElement.appendChild(this.changeThemeControls());
        sceneControlElement.appendChild(this.changeQualityControls());
        sceneControlElement.appendChild(this.resetControls());
	}

	//Creates a table with all the cluster information
    printClusters(element) {
		var table = createDataTable(element, element.id+"-table", ['Cluster', this.index.toString()].concat(this.dimNames), 2, 1);
		var row=null;
		for(var i = 0; i<this.groupOfSpheres.children.length; ++i){
			row = addElementToDataTable(table, [this.groupOfSpheres.children[i].dataObject[2][0], this.groupOfSpheres.children[i].realData[0]].concat(this.groupOfSpheres.children[i].realData[1]), this.groupOfSpheres.children[i].realData[0], 2, false);
			row.cells[0].bgColor = (this.groupOfSpheres.children[i].material.color).getHexString();
		}
		for(var i = 0; i<this.selectedObject.length; ++i){
			row = addElementToDataTable(table, [this.selectedObject.children[i].dataObject[2][0], this.selectedObject.children[i].realData[0]].concat(this.selectedObject.children[i].realData[1]), this.selectedObject.children[i].realData[0], 2, false);
			row.cells[0].bgColor = invertColor(this.selectedObject.children[i].material.color).getHexString();
		}
		table.dataTableObj = $('#'+table.id).DataTable();
		return table;
	}

	createMultipleChoiceTable(parentElement) {
		return createDataTableDynamic(parentElement, parentElement.id+"-table", [this.index.toString()].concat(this.dimNames));
	}

	addElementToTable(table, element){
		addElementToDataTableDynamic(table, [element.realData[0]].concat(element.realData[1]));
	}

	removeElementFromTable(table, element){
		removeElementFromDataTableDynamic(table, element.realData[0]);
    }
    
    // #endregion
    
	// #region User interaction
	//Creates a sphere on the scene, adds the data to the sphere and the sphere to the data.
    createSphere(normData, realData, cluster, auxData, lodData) {
		var material = new THREE.MeshPhongMaterial( {color: this.clusters_color_scheme[cluster].clone()} );

        var radius = this.defaultSpRad;

        if (lodData != undefined) {
            radius = this.defaultSpRad + ((this.defaultSpRad * lodData['group_koeff']));
            this.sphereGeometry = new THREE.SphereGeometry(radius, this.numberOfSegements, this.numberOfSegements );
		}
		var sphere = new THREE.Mesh(this.sphereGeometry, material);
		sphere.position.x = normData[1][this.proectionSubSpace[0]];
		sphere.position.y = normData[1][this.proectionSubSpace[1]];
		sphere.position.z = normData[1][this.proectionSubSpace[2]];
		normData[2] = [cluster];
		normData[3] = sphere;
		realData[3] = sphere;
		auxData[3] = sphere;
		sphere.dataObject = normData;
		sphere.realData = realData;
        sphere.auxData = auxData;

        sphere.scale.set(radius, radius, radius);

		this.groupOfSpheres.add(sphere);
		this.changeVisibilitySphere(sphere);
		return sphere;
	}

	getSphereGroup(determFunction, parameters){
		var result=[];
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			if(determFunction(this.groupOfSpheres.children[i], parameters))
				result.push(this.groupOfSpheres.children[i]);
		}
		for ( var i = 0; i < this.selectedObject.children.length; i++ ) {
			if(determFunction(this.selectedObject.children[i], parameters))
				result.push(this.selectedObject.children[i]);
		}
		return result;
	}

	resetClusters(){
		this.clusters=[0];
		this.clusters_color_scheme = this.createColorScheme();
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			this.groupOfSpheres.children[i].dataObject[2][this.groupOfSpheres.children[i].dataObject[2].length-1]=0;
			this.groupOfSpheres.children[i].material.color = this.clusters_color_scheme[this.groupOfSpheres.children[i].dataObject[2][0]].clone();
		}
		for ( var i = 0; i < this.selectedObject.children.length; i++ ) {
			this.selectedObject.children[i].dataObject[2][this.selectedObject.children[i].dataObject[2].length-1]=0;
			this.selectedObject.children[i].material.color = invertColor(this.clusters_color_scheme[this.selectedObject.children[i].dataObject[2][0]].clone());
        }

        this._coord.mode = "print";

        requestAnimationFrame(render);
	}

	changeCluster(sphere, newCluster){
		scene.unSelectObject(sphere);
		sphere.dataObject[2].unshift(newCluster);
		sphere.material.color = this.clusters_color_scheme[newCluster].clone();
        scene.selectObject(sphere);

        requestAnimationFrame(render);
	}

	createColorScheme(){
		return Object.assign({}, this.customColors, getColorScheme(this.clusters, this.theme));
	}
	
	// Changes the theme. Currently there are two themes "white" and "black"
    changeTheme(newTheme){
        super.changeTheme(newTheme);
		if (this.theme=='white'){
			this.select_linecube_color = new THREE.Color(0,0,0);
			this.scene.background = new THREE.Color( 0xffffff );
		}
		else{
			this.select_linecube_color = new THREE.Color(1,1,1);
			this.scene.background = new THREE.Color( 0x333333 );
		}
		this.clusters_color_scheme = this.createColorScheme();
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			this.groupOfSpheres.children[i].material.color = this.clusters_color_scheme[this.groupOfSpheres.children[i].dataObject[2][0]].clone();
        }

        requestAnimationFrame(render);
	}

	// Color group of spheres
	changeColorGroup(group, color){
		var groupnumber=0;
		while(('group'+groupnumber) in this.customColors){
			++groupnumber;
		}
		var newgroup = 'group'+groupnumber;
		this.customColors[newgroup]=color;
		this.clusters_color_scheme[newgroup]=color;
		for(var i = 0; i< group.length; ++i){
			group[i].dataObject[2].unshift(newgroup);
			if (this.selectedObject.children.includes(group[i])){
				group[i].material.color = invertColor(this.customColors[newgroup].clone());
			}
			else
				group[i].material.color = this.customColors[newgroup].clone();
        }

        requestAnimationFrame(render);
		return newgroup;
	}

	// undoColorGroup() {
	// 	var groupnumber=0;
	// 	while(('group'+groupnumber) in this.customColors){
	// 		++groupnumber;
	// 	}
	// 	var oldgroup = 'group'+--groupnumber;
	// 	delete this.customColors[oldgroup];
	// 	delete this.clusters_color_scheme[oldgroup];
	// 	for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
	// 		this.groupOfSpheres.children[i].dataObject[2].shift();
	// 		this.groupOfSpheres.children[i].material.color = this.clusters_color_scheme[this.groupOfSpheres.children[i].dataObject[2][0]].clone();
	// 	}
	// 	for ( var i = 0; i < this.selectedObject.children.length; i++ ) {
	// 		this.selectedObject.children[i].dataObject[2].shift();
	// 		this.selectedObject.children[i].material.color = invertColor(this.clusters_color_scheme[this.selectedObject.children[i].dataObject[2][0]].clone());
	// 	}
	// 	return groupnumber==0;
	// }

	// Changes the quality of the picture. 
	changeQuality(quality){
		for(var i = 0; i<this.__qualityRange.length; ++i){
			if(quality == this.__qualityRange[i]['value']){
				this.numberOfSegements = this.__qualityRange[i]['segs']; //Assigns the segment parameter
				var realquality = true;
			}
		}
		if (!realquality){
			this.numberOfSegements = this.__qualityRange[3]['segs'];
            quality = this.___qualityRange[3]['value'];
        }
		this.sphereGeometry = new THREE.SphereGeometry( this.defaultSpRad, this.numberOfSegements, this.numberOfSegements); //Create a new sphere geometry for all spheres
		this.redrawScene(); //Redraw the sphere with new quality
		this.quality = quality;
        setCookie('quality', this.quality, 14);

        requestAnimationFrame(render);
	}

	//Redraw the scene. Recreates the sphere and selected sphere groups and recreates all the spheres in it.
	redrawScene(){
		var oldGroup = this.groupOfSpheres;
		this.scene.remove(this.groupOfSpheres);
		this.groupOfSpheres = new THREE.Group();
		var i = 0;
		for (i=0; i < oldGroup.children.length; ++i) {
			var newSphere = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].realData, oldGroup.children[i].dataObject[2][0], oldGroup.children[i].auxData);
			this.groupOfSpheres.add(newSphere);
		}
		this.scene.add(this.groupOfSpheres);

		oldGroup = this.selectedObject;
		this.scene.remove(this.selectedObject);
		this.selectedObject = new THREE.Group();
		for (i=0; i < oldGroup.children.length; ++i) {
			this.groupOfSelectOutlines.remove(oldGroup.children[i].selectedCircut);
			var newSphere = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].realData, oldGroup.children[i].dataObject[2][0], oldGroup.children[i].auxData);
			this.selectObject(newSphere);
		}
        this.scene.add(this.selectedObject);

        requestAnimationFrame(render);
	}
    
	// Deactivates all interactions before changing it.
    deactivateAllInteractions(){
		if(this.dragControls !== null){
			this.dragControls.deactivate();
			this.dragEnabled = false;
		}
		if (this.multiChoiceTable !== undefined){
			deleteDataTable(this.multiChoiceTable);
			this.multiChoiceTable=undefined;
		}
		if (this.dims_gui.__folders['Multidimensional Coordinates']) {
			this.dims_gui.removeFolder(this.dims_folder);
		}
		if (this.dims_gui.__folders['Auxiliary Data']) {
			this.dims_gui.removeFolder(this.dims_aux_folder);
		}
	}

	//Sets the new interaction mode.
	setInteractiveMode(mode, parameters){
		if (mode==this.interactiveMode)
			return;
		this.deactivateAllInteractions();
		this.unSelectAllObjects();
		if (mode=='drag'){
			this.interactiveMode='drag';
			var allobj=[];
			if(this.selectedObject.children.length!=0)
				allobj=allobj.concat(this.selectedObject.children);
			if(this.groupOfSpheres.children.length!=0)
				allobj=allobj.concat(this.groupOfSpheres.children);
			this.dragControls = new THREE.DragControls(allobj, this.camera, this.renderer.domElement );
			this.dragControls.scene = this;
			this.dragControls.addEventListener( 'dragstart', function ( event ) { 
				event.target.scene.controls.enabled = false;
			} );
			this.dragControls.addEventListener( 'dragend', function ( event ) { 
				event.target.scene.controls.enabled = true;
                requestAnimationFrame(render);
			} );
			this.dragControls.addEventListener( 'drag', this.onSphereMove);
			this.dragControls.activate();
			this.dragEnabled = true;
		}else{
			if(mode=='multi'){
				this.interactiveMode = 'multi';
				this.multiChoiceTableTab = parameters['tabletab'];
				this.multiChoiceTable = this.createMultipleChoiceTable(this.multiChoiceTableTab);			
			}else{
				this.interactiveMode='single';
			}
		}

        requestAnimationFrame(render);
	}

	//Reaction to a movement of a sphere. Checks the boundary, changes the dataobjects of the spheres.
	onSphereMove(event) {

		var obj = event.object;
		if (obj.position.x<0)
			obj.position.x = 0;
		else
			if (obj.position.x>100)
				obj.position.x=100;
		if (obj.position.y<0)
			obj.position.y = 0;
		else
			if (obj.position.y>100)
				obj.position.y=100;
		if (obj.position.z<0)
			obj.position.z = 0;
		else
			if (obj.position.z>100)
				obj.position.z=100;
		if (event.target.scene.selectedObject.children.includes(obj)) {
			obj.selectedCircut.position.x = obj.position.x;
			obj.selectedCircut.position.y = obj.position.y;
			obj.selectedCircut.position.z = obj.position.z;
		}
		var x = event.target.scene.proectionSubSpace[0];
		var y = event.target.scene.proectionSubSpace[1];
		var z = event.target.scene.proectionSubSpace[2];
		var min = event.target.scene.realStats[1][1];
		var max = event.target.scene.realStats[1][2];
		obj.dataObject[1][x] = obj.position.x;
		obj.dataObject[1][y] = obj.position.y;
		obj.dataObject[1][z] = obj.position.z;
		obj.realData[1][x] = obj.position.x * (max[x] - min[x]) / 100 + min[x];
		obj.realData[1][y] = obj.position.y * (max[y] - min[y]) / 100 + min[y];
		obj.realData[1][z] = obj.position.z * (max[z] - min[z]) / 100 + min[z];

		var scene = event.currentTarget.sceneObject.scene;

        event.target.scene.printDataDialog(obj, scene);
        requestAnimationFrame(render);
	}
	
	//prints the sphere data in a nice dialogue box on top of the scene.
	printDataDialog(sphereToPrint, scene){

		if (this.dims_gui.__folders['Multidimensional Coordinates']) {
			this.dims_gui.removeFolder(this.dims_folder);
		}
		if (this.dims_gui.__folders['Auxiliary Data']) {
			this.dims_gui.removeFolder(this.dims_aux_folder);
		}
		// Set DAT.GUI Controllers
		var gui_data = {};
		this.gui_data = gui_data;
		var aux_gui_data = {};

		gui_data[this.index] = sphereToPrint.dataObject[ 0 ];

		// Set GUI fields for all coordinates (real data values)
		for( var i = 0; i < sphereToPrint.realData[ 1 ].length; i++ ) {
			gui_data[this.dimNames[ i ]] = sphereToPrint.realData[ 1 ][ i ];
		}

		for ( var j = 0; j < sphereToPrint.auxData[ 1 ].length; j++ ) {
			aux_gui_data[this.auxNames[ j ]] = sphereToPrint.auxData[ 1 ][ j ];
		}

		// Create DAT.GUI object
		this.createGui();

		// Create new Folder
		if (!this.dims_gui.__folders['Multidimensional Coordinates']) {
			this.dims_folder = this.dims_gui.addFolder('Multidimensional Coordinates');
		}

		// Add dataset index field to dat.gui.Controller
		this.dims_folder.add( gui_data, this.index );

		// Add sliders with real data values
		var counter = 0;
		for ( var key in gui_data ) {
			if ( key != this.index ) {
				var min = 0;
				var max = 0;
				for ( var k = 0; k < this.realStats[ 0 ].length; k++ ) {
					if ( this.realStats[0][k] == 'Min' )
						min = this.realStats[1][k][counter];
					if ( this.realStats[0][k] == 'Max' )
						max = this.realStats[1][k][counter];
				}
				this.dims_folder.add( gui_data, key, min, max ).listen();
				counter++;
			}
		}

		this.dims_folder.open();

		// Create Auxiliary Data Folder
		if (!this.dims_gui.__folders['Auxiliary Data']) {
			this.dims_aux_folder = this.dims_gui.addFolder('Auxiliary Data');
		}

		for ( var key in aux_gui_data ) {
			this.dims_aux_folder.add( aux_gui_data, key );
		}

		this.dims_folder.open();
		this.dims_aux_folder.open();


		this.csrf = document.getElementsByName("csrfmiddlewaretoken")[0].getAttribute("value");

		var obj = {
			coordinates: sphereToPrint.dataObject[1],
			selectedObject: sphereToPrint,
			scene: this,
			Recalculate:function() {
				sendAjaxPredictRequest(sphereToPrint, {csrfmiddlewaretoken: this.scene.csrf, dsID: this.scene.dsID}, this.scene);
			}
		};

		this.dims_folder.add(obj,'Recalculate');


		for (var i = 0; i < this.dims_folder.__controllers.length - 1; i++) {
			var current_controller = this.dims_folder.__controllers[ i ];
			current_controller.selectedObject = sphereToPrint;
			current_controller.dimNames = this.dimNames;
			current_controller.subSpace = this.proectionSubSpace;
			current_controller.realStats = this.realStats;
			current_controller.sceneObject = scene;
			current_controller.onChange(function(value) {
			});
			current_controller.onFinishChange(function(value) {
				var currDimName = this.property;
				var currDimNum = this.dimNames.indexOf(currDimName);
				var min = this.realStats[1][1][currDimNum];
				var max = this.realStats[1][2][currDimNum];
				this.selectedObject.dataObject[1][currDimNum] = (( value - min ) / ( max - min )) * 100;
				var sphere = this.selectedObject;
				sphere.position.set(sphere.dataObject[1][this.subSpace[0]],
									sphere.dataObject[1][this.subSpace[1]],
									sphere.dataObject[1][this.subSpace[2]]);
                requestAnimationFrame(render);
			});
		}
	}

	//Reaction to mouse click event. Depends on the interactive mode calls different functions
	onMouseClick(event) {
        event.preventDefault();

        var rect = event.target.getBoundingClientRect();

        this.processClick(event.target,
            event.clientX - rect.left,
            event.clientY - rect.top);
    }

    //Reaction to touch end event
    onTouchEnd(event) {
        event.preventDefault();

        for (var i = 0; i < event.changedTouches.length; i++) {
            var rect = event.changedTouches[i].target.getBoundingClientRect();

            this.processClick(event.changedTouches[i].target,
                event.changedTouches[i].clientX - rect.left,
                event.changedTouches[i].clientY - rect.top);
        }

        for (var i = 0; i < event.touches.length; i++) {
            var rect = event.touches[i].target.getBoundingClientRect();

            this.processClick(event.touches[i].target,
                event.touches[i].clientX - rect.left,
                event.touches[i].clientY - rect.top);
        }

        for (var i = 0; i < event.targetTouches.length; i++) {
            var rect = event.targetTouches[i].target.getBoundingClientRect();

            this.processClick(event.targetTouches[i].target,
                event.targetTouches[i].clientX - rect.left,
                event.targetTouches[i].clientY - rect.top);
        }
    }

    //Reaction to touch end event
    onPointerMove(event) {
        event.preventDefault();

        if (event.pressure > 0.1) requestAnimationFrame(render);
    }

    processClick(target, offsetX, offsetY) {
        this.intersects = this.getIntersects(target, offsetX, offsetY);

        if (this.intersects.length > 0) {
            var res = this.intersects.filter(function (res) {

                return res && res.object;

            })[0];

            if (res && res.object) {
                if (this.interactiveMode == 'multi')
                    this.multiSelectionClick(res.object);
                if (this.interactiveMode == 'single')
                    this.singleSelectionClick(res.object);
                if (this.interactiveMode == 'drag')
                    this.dragSelectionClick(res.object);

            } else {
                if (this.dims_gui.__folders['Multidimensional Coordinates']) {
                    this.dims_gui.removeFolder(this.dims_folder);
                }
                if (this.dims_gui.__folders['Auxiliary Data']) {
                    this.dims_gui.removeFolder(this.dims_aux_folder);
                }
            }

            // Render frame when something has changed
            requestAnimationFrame(render);
        }
    }

    //Gets the object that is being on the given two dimensional point
    getIntersects(target, offsetX, offsetY) {
        var x = (offsetX / target.clientWidth) * 2 - 1,
            y = - (offsetY / target.clientHeight) * 2 + 1;

        var select = true, spheres = true;

        this.mouseVector.set(x, y);
        this.raycaster.setFromCamera(this.mouseVector, this.camera);
        spheres = spheres && (this.groupOfSpheres.children.length != 0);
        select = select && (this.selectedObject.children.length != 0);
        if (spheres)
            if (select)
                return this.raycaster.intersectObjects([this.groupOfSpheres, this.selectedObject], true);
            else
                return this.raycaster.intersectObject(this.groupOfSpheres, true);
        else
            if (select)
                return this.raycaster.intersectObject(this.selectedObject, true);
            else
                return [];
    }

	//reaction to an object click in single selection mode.
	singleSelectionClick(obj){
		// If True, unselect selected object
		if (this.selectedObject.children.includes(obj)) {
			this.unSelectObject(obj);
			this.selectedObject.remove(obj);
			if (this.dims_gui.__folders['Multidimensional Coordinates']) {
				this.dims_gui.removeFolder(this.dims_folder);
			}
			if (this.dims_gui.__folders['Auxiliary Data']) {
				this.dims_gui.removeFolder(this.dims_aux_folder);
			}
			var selected_group_link = document.getElementById("selected_group_link");
            selected_group_link.style.display = "none";

            requestAnimationFrame(render);
			return true;
		}

		// If true, unselect old object, select the new one
		if (this.selectedObject.children.length != 0) {
			this.unSelectAllObjects();
			if (this.dims_gui.__folders['Multidimensional Coordinates']) {
				this.dims_gui.removeFolder(this.dims_folder);
			}
			if (this.dims_gui.__folders['Auxiliary Data']) {
				this.dims_gui.removeFolder(this.dims_aux_folder);
			}

            requestAnimationFrame(render);
		}
		
		this.selectObject(obj);
		this.printDataDialog(obj, this.scene);

		/*
		--------------------------------------------------------------------
		LoD Data Objects Click 
		--------------------------------------------------------------------
		 */
		if (this.lodData.length > 0 ) {

			var curr_group = this.lodData.filter(function(a){ return a.group_name == obj.dataObject[0] })[0]['group_number'];

			var vis_group_obj = {
				VisualizeGroup:function() {
					var link=document.createElement('a');
					link.href=next_group_url.replace('NEWGROUPID', curr_group);
					link.target='_blank';
					link.click();
				}};
			this.dims_folder.add(vis_group_obj,'VisualizeGroup');
		}
	}

	//reaction to an object click in multiple selection mode.
	multiSelectionClick(obj, unselect=true, select=true){
		// If True, unselect selected object
		if (this.selectedObject.children.includes(obj)) {
			if (!unselect)
				return true;
			this.unSelectObject(obj);
			this.selectedObject.remove(obj);
			this.removeElementFromTable(this.multiChoiceTable, obj);
			return true;
		}
		if (!select)
			return true;
		this.selectObject(obj);
        this.addElementToTable(this.multiChoiceTable, obj);

        requestAnimationFrame(render);
	}

	//reaction to an object click in drag mode.
	dragSelectionClick(obj){
		// If true, unselect old object, select the new one
		if (this.selectedObject.children.length != 0) {
			this.unSelectAllObjects();
			if (this.dims_gui.__folders['Multidimensional Coordinates']) {
				this.dims_gui.removeFolder(this.dims_folder);
			}
			if (this.dims_gui.__folders['Auxiliary Data']) {
				this.dims_gui.removeFolder(this.dims_aux_folder);
			}
		}
		
		this.selectObject(obj);
		this.printDataDialog(obj, this);

        requestAnimationFrame(render);
	}

	//selects the given object
	selectObject(obj){
        if (obj == undefined)
            return false;

        var geometry = new THREE.BoxBufferGeometry(1.6, 1.6, 1.6);
        var edgesCube = new THREE.EdgesGeometry(geometry);
        var lineCube = new THREE.LineSegments(edgesCube, new THREE.LineBasicMaterial({ color: this.select_linecube_color }));

        obj.selectedCircut = lineCube;
        lineCube.position.x = obj.position.x;
        lineCube.position.y = obj.position.y;
        lineCube.position.z = obj.position.z;
        obj.material.color.set(invertColor(obj.material.color));

        lineCube.scale.set(obj.scale['x'], obj.scale['y'], obj.scale['z']);

        this.groupOfSelectOutlines.add(lineCube);
        this.selectedObject.add(obj);
        lineCube.visible = obj.visible;

        // Render frame when something has changed
        requestAnimationFrame(render);
	}

	//Unselects all objects
	unSelectAllObjects(){
		while (this.selectedObject.children.length!=0){
			this.unSelectObject(this.selectedObject.children.pop());
		}

        requestAnimationFrame(render);
	}

	changeVisibilityAll(){
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			this.changeVisibilitySphere(this.groupOfSpheres.children[i]);
		}
		for ( var i = 0; i < this.selectedObject.children.length; i++ ) {
			this.changeVisibilitySphere(this.selectedObject.children[i])
		}
	}

	//Change visiblility state of the sphere
	changeVisibilitySphere(sphere){
		if(true){
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
	
	//Unselects given object
	unSelectObject(obj){
		this.groupOfSelectOutlines.remove(obj.selectedCircut);
		obj.selectedCircut = undefined;
		obj.material.color.set( invertColor(obj.material.color) );
		this.groupOfSpheres.add(obj);

        requestAnimationFrame(render);
	}

	changeRad(newRad){
        //this.sphereGeometry = new THREE.SphereGeometry( newRad, this.numberOfSegements, this.numberOfSegements );
        this.defaultSpRad = newRad;
        var actualRad = newRad;

        for (var i = 0; i < this.groupOfSpheres.children.length; ++i) {
            if (this.lodData.length > 0 && this.lodData[this.groupOfSpheres.children[i].dataObject[0]][0] != this.groupOfSpheres.children[i].dataObject[0]) {
                alert('An error has occured in LOD generator! Check your data! \n lodData[' + this.groupOfSpheres.children[i].dataObject[0] +
                    '] (' + this.lodData[this.groupOfSpheres.children[i].dataObject[0]][0] + ') is not equal to groupOfSpheres.children[' +
                    i + '].realData[0] (' + this.groupOfSpheres.children[i].dataObject[0] + ')');
                return;
            }

            actualRad =
                ((this.lodData.length > 0) ?
                    newRad + (newRad * this.lodData[this.groupOfSpheres.children[i].dataObject[0]][3]) :
                    newRad);
            this.groupOfSpheres.children[i].scale.set(actualRad, actualRad, actualRad);
        }

        for (var i = 0; i < this.selectedObject.children.length; ++i) {
            actualRad =
                ((this.lodData.length > 0) ?
                    newRad + (newRad * this.lodData[this.selectedObject.children[i].dataObject[0]][3]) :
                    newRad);

            this.selectedObject.children[i].scale.set(actualRad, actualRad, actualRad);
            this.groupOfSelectOutlines.children[i].scale.set(actualRad, actualRad, actualRad);
        }

        // Render frame when something has changed
        requestAnimationFrame(render);
	}

	//Moves all spheres to their new location based on data object and given subspace
	moveSpheres() {
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			var sphere = this.groupOfSpheres.children[i];
			sphere.position.x = sphere.dataObject[1][this.proectionSubSpace[0]];
			sphere.position.y = sphere.dataObject[1][this.proectionSubSpace[1]];
			sphere.position.z = sphere.dataObject[1][this.proectionSubSpace[2]];
		}
		for ( var i = 0; i < this.selectedObject.children.length; i++ ) {
			var sphere = this.selectedObject.children[i];
			sphere.position.x = sphere.dataObject[1][this.proectionSubSpace[0]];
			sphere.position.y = sphere.dataObject[1][this.proectionSubSpace[1]];
			sphere.position.z = sphere.dataObject[1][this.proectionSubSpace[2]];
			sphere.selectedCircut.position.x = sphere.position.x;
			sphere.selectedCircut.position.y = sphere.position.y;
			sphere.selectedCircut.position.z = sphere.position.z;
		}
        this.changeVisibilityAll();

        requestAnimationFrame(render);
    }
    
    setNewSubSpace(x1, x2, x3){
        super.setNewSubSpace(x1, x2, x3);
		this.moveSpheres();
    }
}