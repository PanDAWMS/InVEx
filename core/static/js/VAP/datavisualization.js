// Sends Ajax 
function sendAjaxPredictRequest(selectedObject, otherData, sceneObj){
	data = { formt: 'rebuild', data: JSON.stringify(selectedObject.dataObject[1])};
	allData = Object.assign.apply({}, [data, otherData]);
	$.ajax({
				type:"POST",
				url: "",
				data : allData,
				success : function(results_dict) {
					scene.changeCluster(selectedObject, results_dict['results'][0]);
					console.log(results_dict['clustertype']);
				},
				failure: function(data) {
					alert('There was an error. Sorry');
				}
			})
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
		
		//Creates raycaster and mouse vector to calculate the click destination
        this.raycaster = new THREE.Raycaster();
        this.mouseVector = new THREE.Vector3();
        this.dragControls = null;
        this.dragEnabled = false;

        this.defaultSpRad = defaultRadius;

		//Sets the listener for mouse click
        mainDiv.addEventListener( "click", function(event){this.sceneObject.onMouseClick(event);}, false );
        this.changeTheme(this.theme);
        this.changeQuality(this.quality);
    }

    saveParameters(){
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
		//Radio button for single choice
		var singleChoiceRadio = createControlRadioWithLabel('single' + interactionModeID, interactionModeID, 'Activate Single Sphere Selection');
		singleChoiceRadio.sceneObject = this;
		singleChoiceRadio.multiChoiceControl = multiChoiceControl;
		if (this.interactiveMode == 'single')
			singleChoiceRadio.checked = true;
		singleChoiceRadio.onchange = function(event){
			this.sceneObject.setInteractiveMode('single', {});
			this.multiChoiceControl.style["visibility"] = 'hidden';
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
			this.multiChoiceControl.style["visibility"] = 'visible';
		};
		//Radio button for drag control
		var dragChoiceRadio = createControlRadioWithLabel('drag' + interactionModeID, interactionModeID, 'Activate Drag Sphere Control');
		dragChoiceRadio.sceneObject = this;
		dragChoiceRadio.multiChoiceControl = multiChoiceControl;
		if (this.interactiveMode == 'drag')
			dragChoiceRadio.checked = true;
		dragChoiceRadio.onchange = function(event){
			this.sceneObject.setInteractiveMode('drag', {});
			this.multiChoiceControl.style["visibility"] = 'hidden';
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

		var changeRadiusBtn = document.createElement('button');
		changeRadiusBtn.id = 'button' + radChangeID;
		changeRadiusBtn.classList.add('button', 'small');
		changeRadiusBtn.innerText = 'Change Radius';
		changeRadiusBtn.setAttribute('type', 'button');

		var radiusRange = document.createElement('input');
		changeRadiusBtn.id = 'range' + radChangeID;
		radiusRange.classList.add('custom-range');
		radiusRange.setAttribute('type', 'range');
		radiusRange.min = 0.1;
		radiusRange.max = 3;
		radiusRange.step = 0.1;

		var label = document.createElement('label');
		label.id = 'for' + radiusRange.id;
		label.setAttribute('for', radiusRange.id);
		label.innerText = 'Spheres Radius: ';

		changeRadiusBtn.sceneObject = this;
		changeRadiusBtn.radiusRange = radiusRange;
        radiusRange.value = this.defaultSpRad.toString();
		changeRadiusBtn.onclick = function() {
			this.sceneObject.changeRad(parseFloat(this.radiusRange.value));
			return false;
		};

		form.groupDiv.appendChild(label);
		form.groupDiv.appendChild(radiusRange);
		form.groupDiv.appendChild(changeRadiusBtn);

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
    createControlElements(sceneControlElement, multiChoiceControl, multiChoiceTab, fullload=true) {
        if(fullload){
			this.dimensionControlElements();
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
			row = addElementToDataTable(table, [this.groupOfSpheres.children[i].dataObject[2], this.groupOfSpheres.children[i].realData[0]].concat(this.groupOfSpheres.children[i].realData[1]), this.groupOfSpheres.children[i].realData[0], 2, false);
			row.cells[0].bgColor = (this.groupOfSpheres.children[i].material.color).getHexString();
		}
		for(var i = 0; i<this.selectedObject.length; ++i){
			row = addElementToDataTable(table, [this.selectedObject.children[i].dataObject[2], this.selectedObject.children[i].realData[0]].concat(this.selectedObject.children[i].realData[1]), this.selectedObject.children[i].realData[0], 2, false);
			row.cells[0].bgColor = invertColor(this.selectedObject.children[i].material.color).getHexString();
		}
		table.dataTableObj = $('#'+table.id).DataTable();
		return table;
	}

	createMultipleChoiceTable(parentElement) {
		var table = createDataTableDynamic(parentElement, parentElement.id+"-table", [this.index.toString()].concat(this.dimNames));
		return table;
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
		var material = new THREE.MeshPhongMaterial( {color: this.clusters_color_scheme[cluster]} );
		if (lodData != undefined) {
			var newSphereRadius = this.defaultSpRad + ((this.defaultSpRad * lodData[3]));
			this.sphereGeometry = new THREE.SphereGeometry( newSphereRadius, this.numberOfSegements, this.numberOfSegements );
		}
		var sphere = new THREE.Mesh(this.sphereGeometry, material);
		sphere.position.x = normData[1][this.proectionSubSpace[0]];
		sphere.position.y = normData[1][this.proectionSubSpace[1]];
		sphere.position.z = normData[1][this.proectionSubSpace[2]];
		normData[2] = cluster;
		normData[3] = sphere;
		realData[3] = sphere;
		auxData[3] = sphere;
		sphere.dataObject = normData;
		sphere.realData = realData;
		sphere.auxData = auxData;
		this.groupOfSpheres.add(sphere);
		return sphere;
	}

	changeCluster(sphere, newCluster){
		scene.unSelectObject(sphere);
		sphere.dataObject[2] = newCluster;
		sphere.material.color = this.clusters_color_scheme[newCluster];
		scene.selectObject(sphere);
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
		this.clusters_color_scheme = getColorScheme(this.clusters, this.theme);
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			this.groupOfSpheres.children[i].material.color = this.clusters_color_scheme[this.groupOfSpheres.children[i].dataObject[2]].clone();
		}
	}

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
	}

	//Redraw the scene. Recreates the sphere and selected sphere groups and recreates all the spheres in it.
	redrawScene(){
		var oldGroup = this.groupOfSpheres;
		this.scene.remove(this.groupOfSpheres);
		this.groupOfSpheres = new THREE.Group();
		var i = 0;
		for (i=0; i < oldGroup.children.length; ++i) {
			var newSphere = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].realData, oldGroup.children[i].dataObject[2], oldGroup.children[i].auxData);
			this.groupOfSpheres.add(newSphere);
		}
		this.scene.add(this.groupOfSpheres);

		oldGroup = this.selectedObject;
		this.scene.remove(this.selectedObject);
		this.selectedObject = new THREE.Group();
		for (i=0; i < oldGroup.children.length; ++i) {
			this.groupOfSelectOutlines.remove(oldGroup.children[i].selectedCircut);
			var newSphere = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].realData, oldGroup.children[i].dataObject[2], oldGroup.children[i].auxData);
			this.selectObject(newSphere);
		}
		this.scene.add(this.selectedObject);
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

		event.target.scene.printDataDialog(obj);

	}
	
	//prints the sphere data in a nice dialogue box on top of the scene.
	printDataDialog(sphereToPrint){

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
						sendAjaxPredictRequest(sphereToPrint, {csrfmiddlewaretoken: this.scene.csrf, fdid: this.scene.fdid}, this.scene);
                    }
                };

                this.dims_folder.add(obj,'Recalculate');


                for (var i = 0; i < this.dims_folder.__controllers.length - 1; i++) {
                    var current_controller = this.dims_folder.__controllers[ i ];
                    current_controller.selectedObject = sphereToPrint;
                    current_controller.dimNames = this.dimNames;
                    current_controller.subSpace = this.proectionSubSpace;
                    current_controller.realStats = this.realStats;

                    current_controller.onChange(function(value) {
                    });

                    current_controller.onFinishChange(function(value) {
                        var currDimName = this.property;
                        var currDimNum = this.dimNames.indexOf(currDimName);
                        var min = this.realStats[1][1][currDimNum];
                        var max = this.realStats[1][2][currDimNum];
                        var newNormValue = (( value - min ) / ( max - min )) * 100;
                        this.selectedObject.dataObject[1][currDimNum] = newNormValue;
                        var sphere = this.selectedObject;
                        sphere.position.set(sphere.dataObject[1][this.subSpace[0]],
                                            sphere.dataObject[1][this.subSpace[1]],
                                            sphere.dataObject[1][this.subSpace[2]]);
                    });
                }
	}

	//Reaction to mouse click event. Depends on the interactive mode calls different functions
	onMouseClick(event) {
		event.preventDefault();

		this.intersects = this.getIntersects( event.offsetX, event.offsetY );
		if ( this.intersects.length > 0 ) {
			var res = this.intersects.filter( function ( res ) {

				return res && res.object;

			} )[ 0 ];

			if ( res && res.object ) {
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
		}
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
		}
		
		this.selectObject(obj);	
		this.printDataDialog(obj);

		if (this.lodData.length > 0 ) {
			var csrftoken = Cookies.get('csrftoken');
			var data = { formt: 'group_data',
						 group_id: obj.dataObject[0],
						 fdid: scene.fdid,
						 csrfmiddlewaretoken: csrftoken
						};
			$.ajax({
				type:"POST",
				url: "",
				data : data,
				success : function(data, status, xhr) {
					var headers = [data['index_name']].concat(data['headers']);
					printDataset(document.getElementById('selected_group'), headers, fix_array(data['group_data']), 10);
				},
				failure: function(data, status, xhr) {
					console.log('There was an error. Sorry');
				}
			});
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
		this.printDataDialog(obj);
	}

	//selects the given object
	selectObject(obj){
		var geometry = new THREE.BoxBufferGeometry( 2*obj.geometry.parameters.radius, 2*obj.geometry.parameters.radius, 2*obj.geometry.parameters.radius );
		var edgesCube = new THREE.EdgesGeometry( geometry );
		var lineCube = new THREE.LineSegments( edgesCube, new THREE.LineBasicMaterial( { color: this.select_linecube_color } ) );
		obj.selectedCircut = lineCube;
		lineCube.position.x = obj.position.x;
		lineCube.position.y = obj.position.y;
		lineCube.position.z = obj.position.z;
		obj.material.color.set( invertColor(obj.material.color) );
		this.groupOfSelectOutlines.add(lineCube);
		this.selectedObject.add(obj);
	}

	//Unselects all objects
	unSelectAllObjects(obj){
		while (this.selectedObject.children.length!=0){
			this.unSelectObject(this.selectedObject.children.pop());
		}
	}

	//Unselects given object
	unSelectObject(obj){
		this.groupOfSelectOutlines.remove(obj.selectedCircut);
		obj.selectedCircut = null;
		obj.material.color.set( invertColor(obj.material.color) );
		this.groupOfSpheres.add(obj);
	}

	//Gets the object that is being on the given two dimensional point
	getIntersects(x, y, select=true, spheres=true) {
		x = ( x / this.mainDiv.clientWidth ) * 2 - 1;
		y = - ( y / this.mainDiv.clientHeight ) * 2 + 1;
		this.mouseVector.set( x, y );
		this.raycaster.setFromCamera( this.mouseVector, this.camera );
		spheres = spheres && (this.groupOfSpheres.children.length!=0);
		select = select && (this.selectedObject.children.length!=0); 
		if(spheres)
			if(select)
				return this.raycaster.intersectObjects( [this.groupOfSpheres, this.selectedObject], true );
			else
				return this.raycaster.intersectObject( this.groupOfSpheres, true );
		else
			if(select)
				return this.raycaster.intersectObject( this.selectedObject, true );
			else
				return [];

	}

	changeRad(newRad){
		this.sphereGeometry = new THREE.SphereGeometry( newRad, this.numberOfSegements, this.numberOfSegements );
		this.defaultSpRad = newRad;
		this.redrawScene();
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
    }
    
    setNewSubSpace(x1, x2, x3){
        super.setNewSubSpace(x1, x2, x3);
		this.moveSpheres();
    }
}