function invertColor(color) {
	return new THREE.Color(1.0-color.r, 1.0-color.g, 1.0-color.b);
}

function drawPlainGrid( white_theme=false ) {
	if (white_theme)
		var grid = new THREE.GridHelper(200, 20, '#000', '#000');
	else
		var grid = new THREE.GridHelper(200, 20, '#5BB', '#FFF');
	grid.position.y-=0.2;
	return grid;
}

function drawAxes() {
	var axes = new THREE.AxesHelper( 100 );
	return axes;
}


function getColorScheme( clusters, white_theme=false ) {
	var clusters_unique = Array.from(new Set(clusters));
	var len = clusters_unique.length;
	var results = {};
	if (len==1){
		if (white_theme)
			results[clusters_unique[0]] = new THREE.Color(0.8,0.8,0.8);
		else
			results[clusters_unique[0]] = new THREE.Color(1,1,1);
	}
	else
		if ( len == 2 ) {
			results[clusters_unique[0]] = new THREE.Color(1,0,0);
			results[clusters_unique[1]] = new THREE.Color(0,0,1);
		} else {
			var parts = Math.round(Math.log(len)/Math.log(3)+0.5);
			var base = parts - 1;
			if (base == 0)
				base = 1;
			for( var i = 0; i < len; i++ ) {
				if (white_theme)
					results[clusters_unique[i]] = new THREE.Color( (~~(i/(parts*parts)))%parts/base*0.8 , (~~(i/parts))%parts/base*0.8 , i%parts/base*0.8 );
				else
					results[clusters_unique[i]] = new THREE.Color( 1-(~~(i/(parts*parts)))%parts/base , 1-(~~(i/parts))%parts/base , 1-i%parts/base );
			}
		}
	return results;
}

function sendAjaxPredicRequest(selectedObject, otherData, sceneObj){
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

class Scene {

	// #region Scene initialization
	constructor(mainDiv, defaultRadius, numberOfSegements, theme='black') {
			this.mainDiv = mainDiv;
			mainDiv.sceneObject = this;

			// init renderer
			this.renderer = new THREE.WebGLRenderer( { antialias: true } );
			this.renderer.setPixelRatio( window.devicePixelRatio );
			this.renderer.setSize( mainDiv.clientWidth, mainDiv.clientHeight );
			mainDiv.appendChild( this.renderer.domElement );

			// init scene
			this.scene = new THREE.Scene();

			this.groupOfGrid = new THREE.Group();
			this.scene.add(this.groupOfGrid);

			this.groupOfSpheres = new THREE.Group();
			this.scene.add(this.groupOfSpheres);

			this.selectedObject = new THREE.Group();
			this.scene.add(this.selectedObject);

			this.groupOfSelectOutlines = new THREE.Group();
			this.scene.add(this.groupOfSelectOutlines);

			// init camera
			this.camera = new THREE.PerspectiveCamera( 50, mainDiv.clientWidth / mainDiv.clientHeight, 1, 1000 );
			this.camera.position.set(100, 100, 100);
			this.camera.lookAt( this.scene.position );

			this.controls = new THREE.OrbitControls( this.camera, this.renderer.domElement );
			this.controls.enableRotate = true;
			this.controls.saveState();

			this.clusters = undefined;
			
			this.raycaster = new THREE.Raycaster();
			this.mouseVector = new THREE.Vector3();
			this.dragControls = null;
			this.dragEnabled = false;
			this.grid = undefined;
            this.groupOfGrid.add(drawAxes());

			//this.drawAxes();

            // init lights
            this.initLight();

            //mainDiv.addEventListener( 'resize', this.onResize, false );
			mainDiv.addEventListener( "click", function(event){this.sceneObject.onMouseClick(event);}, false );
			this.changeTheme(theme);

			this.height = 10;
			this.defaultSpRad = defaultRadius;
			this.width = 10;
			this.proectionSubSpace = [0,1,2];
			this.dimNames=[];
			this.index = '';
            this.normData = [];
            this.interactiveMode = 'regular';
			this.realData = [];
			this.auxData = [];
			this.clusters = [0];
			this.auxNames = [];
			this.numberOfSegements = numberOfSegements;
			this.outputTable = null;
			this.sphereGeometry = new THREE.SphereGeometry( this.defaultSpRad, this.numberOfSegements, this.numberOfSegements);
            this.createGui();

	}
	
	saveParameters(){
		return {'camerapos': this.camera.position, 'camerarot': this.camera.rotation, 'subspace': this.proectionSubSpace, 'sphrad': this.defaultSpRad};
	}
	
	loadParameters(parametersDict){
		if ('camerapos' in parametersDict)
			this.camera.position.x = parametersDict['camerapos'].x;
			this.camera.position.y = parametersDict['camerapos'].y;
			this.camera.position.z = parametersDict['camerapos'].z;
		
		if ('camerarot' in parametersDict)
			this.camera.rotation.order = parametersDict['camerarot']._order;
			this.camera.rotation.x = parametersDict['camerarot']._x;
			this.camera.rotation.y = parametersDict['camerarot']._y;
			this.camera.rotation.z = parametersDict['camerarot']._z;
		
		if ('subspace' in parametersDict)
			this.proectionSubSpace = parametersDict['subspace'];
		
		if ('sphrad' in parametersDict)
			this.changeRad(parametersDict['sphrad']);
		
	}

    initLight() {
        //Create a new ambient light
        var light = new THREE.AmbientLight( 0x888888 );
        this.scene.add( light );

        //Create a new directional light
        var light = new THREE.DirectionalLight( 0xfdfcf0, 1 );
        light.position.set(20,10,20);
        this.scene.add( light );
    }

	setDimNames(dims){
		this.dimNames = dims;
	}

	setClusters(clusters){
		this.clusters = clusters;
	}

	setIndex(idx) {
		this.index = idx;
	}

	setSource(fdid){
		this.fdid = fdid;
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

	// #endregion
	// #region GUI related

    createGui() {
        this.dims_gui = new dat.GUI({ autoPlace: false, width: 300 });
        this.dims_gui.domElement.id = 'gui';
        document.getElementById("gui_container").appendChild(this.dims_gui.domElement);
	}
	
	radiusControlElement() {
        var changeRadiusBtn = document.getElementById("changeRadiusBtn");
        var radiusRange = document.getElementById("radiusRange");
        changeRadiusBtn.sceneObject = this;
        radiusRange.value = this.defaultSpRad.toString();
		changeRadiusBtn.onclick = function() {
            var radiusRange = document.getElementById("radiusRange");
			this.sceneObject.changeRad(parseFloat(radiusRange.value));
        };
    }

    resetControls() {
        var resetCameraBtn = document.getElementById("resetBtn");
		resetCameraBtn.sceneObject = this;
		resetCameraBtn.onclick = function() {
			this.sceneObject.resetCamera();
			};
    }

    printControls() {
        var display_clusters = document.getElementById("printBtn");
        display_clusters.sceneObject = this;
        display_clusters.onclick = function() {
        	var element = document.getElementById("cluster-table_wrapper");
        	if (element) {
        		element.parentNode.removeChild(element);
			}
			this.sceneObject.printClusters(document.getElementById("clusters"));
        };

		var display_all_dataset = document.getElementById("printAllBtn");
		display_all_dataset.sceneObject = this;
        display_all_dataset.onclick = function() {
            var element = document.getElementById("print-table_wrapper");
        	if (element) {
        		element.parentNode.removeChild(element);
			}
			printDataset(document.getElementById("print"), this.sceneObject.index.concat(this.sceneObject.dimNames), this.sceneObject.realData);
        };
    }

	createControlElements() {
        this.dimensionControlElements();
        this.radiusControlElement();
        this.resetControls();
        this.printControls();
	}

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
	createSphere(normData, realData, cluster, auxData) {
		var material = new THREE.MeshPhongMaterial( {color: this.clusters_color_scheme[cluster]} );
		var sphere = new THREE.Mesh(this.sphereGeometry, material);
		sphere.position.x = normData[1][this.proectionSubSpace[0]];
		sphere.position.y = normData[1][this.proectionSubSpace[1]];
		sphere.position.z = normData[1][this.proectionSubSpace[2]];
		normData[2] = cluster;
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

	changeTheme(newTheme){
		if (newTheme=='white'){
			this.white_theme = true;
			this.select_linecube_color = new THREE.Color(0,0,0);
			this.scene.background = new THREE.Color( 0xffffff );
		}
		else{
			this.white_theme = false;
			this.select_linecube_color = new THREE.Color(1,1,1);
			this.scene.background = new THREE.Color( 0x333333 );
		}
		if (this.grid !== undefined)
		{
			this.groupOfGrid.remove(this.grid);
		}
		this.grid = drawPlainGrid(this.white_theme);
		this.groupOfGrid.add(this.grid);
		this.clusters_color_scheme = getColorScheme(this.clusters, this.white_theme);
		for ( var i = 0; i < this.groupOfSpheres.children.length; i++ ) {
			this.groupOfSpheres.children[i].material.color = this.clusters_color_scheme[this.groupOfSpheres.children[i].dataObject[2]].clone();
		}		
	}

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
				this.interactiveMode='regular';
			}
		}

	}

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
		if (event.target.scene.selectedObject.children.includes(obj)){
			obj.selectedCircut.position.x = obj.position.x;
			obj.selectedCircut.position.y = obj.position.y;
			obj.selectedCircut.position.z = obj.position.z;
		}
		var x = event.target.scene.proectionSubSpace[0];
		var y = event.target.scene.proectionSubSpace[1];
		var z = event.target.scene.proectionSubSpace[2];
		var min = event.target.scene.realStats[1][0];
		var max = event.target.scene.realStats[1][1];
		obj.dataObject[1][x] = obj.position.x;
		obj.dataObject[1][y] = obj.position.y;
		obj.dataObject[1][z] = obj.position.z;
		obj.realData[1][x] = obj.position.x * (max[x] - min[x]) / 100 + min[x];
		obj.realData[1][y] = obj.position.y * (max[y] - min[y]) / 100 + min[y];
		obj.realData[1][z] = obj.position.z * (max[z] - min[z]) / 100 + min[z];
		event.target.scene.printDataDialog(obj);
	}
	
	animate() {
		this.renderer.render( this.scene, this.camera );
	}

	onResize() {
		this.camera.aspect = this.mainDiv.clientWidth / this.mainDiv.clientHeight;
		this.camera.updateProjectionMatrix();
		this.renderer.setSize( this.mainDiv.clientWidth, this.mainDiv.clientHeight );
	}
	
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
						sendAjaxPredicRequest(sphereToPrint, {csrfmiddlewaretoken: this.scene.csrf, fdid: this.scene.fdid}, this.scene);
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
                        var initialValue = this.initialValue;
                        var normValue = this.selectedObject.children[0].dataObject[1][currDimNum];
                        var min = this.realStats[1][1][currDimNum];
                        var max = this.realStats[1][2][currDimNum];
                        var newNormValue = (( value - min ) / ( max - min )) * 100;
                        this.selectedObject.children[0].dataObject[1][currDimNum] = newNormValue;
                        var sphere = this.selectedObject.children[0];
                        sphere.position.set(sphere.dataObject[1][this.subSpace[0]],
                                            sphere.dataObject[1][this.subSpace[1]],
                                            sphere.dataObject[1][this.subSpace[2]]);
                    });
                }
	}

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
				if (this.interactiveMode == 'regular')
					this.regularSelectionClick(res.object);
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

	regularSelectionClick(obj){
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
	}

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

	selectObject(obj){
		this.selectedObject.add(obj);
		var geometry = new THREE.BoxBufferGeometry( 2*obj.geometry.parameters.radius, 2*obj.geometry.parameters.radius, 2*obj.geometry.parameters.radius );
		var edgesCube = new THREE.EdgesGeometry( geometry );
		var edgesCube = new THREE.EdgesGeometry( geometry );
		var lineCube = new THREE.LineSegments( edgesCube, new THREE.LineBasicMaterial( { color: this.select_linecube_color } ) );
		obj.selectedCircut = lineCube;
		lineCube.position.x = obj.position.x;
		lineCube.position.y = obj.position.y;
		lineCube.position.z = obj.position.z;
		obj.material.color.set( invertColor(obj.material.color) );
		this.groupOfSelectOutlines.add(lineCube);
	}

	unSelectAllObjects(obj){
		while (this.selectedObject.children.length!=0){
			this.unSelectObject(this.selectedObject.children.pop());
		}
	}

	unSelectObject(obj){
		this.groupOfSelectOutlines.remove(obj.selectedCircut);
		obj.selectedCircut = null;
		obj.material.color.set( invertColor(obj.material.color) );
		this.groupOfSpheres.add(obj);
	}

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
		var oldGroup = this.groupOfSpheres;
		this.scene.remove(this.groupOfSpheres);
		this.groupOfSpheres = new THREE.Group();
		this.sphereGeometry = new THREE.SphereGeometry( newRad, this.numberOfSegements, this.numberOfSegements );
		this.defaultSpRad = newRad;
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
			var newSphere = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].realData, oldGroup.children[i].dataObject[2], oldGroup.children[i].auxData);
			this.selectObject(newSphere);
		}
		this.scene.add(this.selectedObject);
	}

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
			sphere.selectedCircut.x = sphere.position.x;
			sphere.selectedCircut.y = sphere.position.y;
			sphere.selectedCircut.z = sphere.position.z;
		}
	}

	setNewSubSpace(x1, x2, x3){
		this.proectionSubSpace[0] = x1;
		this.proectionSubSpace[1] = x2;
		this.proectionSubSpace[2] = x3;
		this.moveSpheres();
	}

	resetCamera(){
		this.controls.reset();
	}

	// #endregion

	getDimNumber(dimName) {
		return this.dimNames.indexOf(dimName);
	}

	dimensionControlElements() {
        var chooseDimArray = [];
		var dimensionsForm = document.getElementById("dimensions_form");
		var XYZSelector = dimensionsForm.getElementsByTagName("select");
        for ( var i = 0; i < XYZSelector.length; i++ ) {
            var currSelector = XYZSelector[ i ];
            for ( var j = 0; j < this.dimNames.length; j++ ) {
				var option = document.createElement("option");
                if ( this.proectionSubSpace[ i ] == j )
					option.selected = true;
                option.value = j.toString();
                option.text = this.dimNames[ j ];
                currSelector.add(option);
            }
            chooseDimArray.push(currSelector);
        }
        var changeDimBtn = document.getElementById("change_dim_btn");
        changeDimBtn.sceneObject = this;
		changeDimBtn.dimsSelectArray = chooseDimArray;
		changeDimBtn.onclick=function(){
			this.sceneObject.setNewSubSpace(parseInt(this.dimsSelectArray[0].value),
											parseInt(this.dimsSelectArray[1].value),
											parseInt(this.dimsSelectArray[2].value));
        };
	}
}