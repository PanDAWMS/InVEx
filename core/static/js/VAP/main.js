function invertColor(color) {
	return new THREE.Color(1.0-color.r, 1.0-color.g, 1.0-color.b);
}

function drawPlainGrid() {
	var grid = new THREE.GridHelper(200, 20, '#5BB', '#FFF');
    grid.position.y-=0.2;
	return grid;
}

function removeElement(id) {
    var elem = document.getElementById(id);
    return elem.parentNode.removeChild(elem);
}

class Scene {

	constructor(mainDiv, controlsDiv, outputDiv, defaultRadius, numberOfSegements) {
			this.mainDiv = mainDiv;
			mainDiv.sceneObject = this;

			this.selectedObject = null;
			this.raycaster = new THREE.Raycaster();
			this.mouseVector = new THREE.Vector3();

			// init renderer
			this.renderer = new THREE.WebGLRenderer( { antialias: true } );
			this.renderer.setPixelRatio( window.devicePixelRatio );
			this.renderer.setSize( mainDiv.clientWidth, mainDiv.clientHeight );
			mainDiv.appendChild( this.renderer.domElement );

			// init scene
			this.scene = new THREE.Scene();
			this.scene.background = new THREE.Color( 0x333333 );

			this.groupOfGrid = new THREE.Group();
			this.scene.add(this.groupOfGrid);

			this.groupOfSpheres = new THREE.Group();
			this.scene.add(this.groupOfSpheres);

			// init camera
			this.camera = new THREE.PerspectiveCamera( 50, mainDiv.clientWidth / mainDiv.clientHeight, 1, 1000 );
			this.camera.position.set(100, 100, 100);
			this.camera.lookAt( this.scene.position );

			this.controls = new THREE.OrbitControls( this.camera, this.renderer.domElement );
			this.controls.enableRotate = true;
			this.controls.saveState();

            this.groupOfGrid.add(drawPlainGrid());

			this.drawAxes();

            // init lights
            this.initLight();

            //mainDiv.addEventListener( 'resize', this.onResize, false );
			mainDiv.addEventListener( "click", function(event){this.sceneObject.onMouseClick(event);}, false );

			this.height = 10;
			this.defaultSpRad = defaultRadius;
			this.width = 10;
			this.proectionSubSpace = [0,1,2];
			this.dimNames=[];
            this.dataArray = [];
			this.controlsDiv = controlsDiv;
			this.outputDiv = outputDiv;
			this.numberOfSegements = numberOfSegements;
			this.outputTable = null;
			this.sphereGeometry = new THREE.SphereGeometry( this.defaultSpRad, this.numberOfSegements, this.numberOfSegements);
            this.createGui();
            this.getClusterAlgorithm();

	}

//    draw3DGrid() {
//
//     var gridXZ = new THREE.GridHelper(100, 10, 'gray', 'gray');
//     gridXZ.position.set( 50,-0.1,50 );
//     this.scene.add(gridXZ);
//
//     var gridXY = new THREE.GridHelper(100, 10, 'gray', 'gray');
//     gridXY.position.set( 50,50,-0.1 );
//     gridXY.rotation.x = Math.PI/2;
//     this.scene.add(gridXY);
//
//     var gridYZ = new THREE.GridHelper(100, 10, 'gray', 'gray');
//     gridYZ.position.set( -0.1,50,50 );
//     gridYZ.rotation.z = Math.PI/2;
//     this.scene.add(gridYZ);
//
// }

    initLight() {
        //Create a new ambient light
        var light = new THREE.AmbientLight( 0x888888 );
        this.scene.add( light );

        //Create a new directional light
        var light = new THREE.DirectionalLight( 0xfdfcf0, 1 );
        light.position.set(20,10,20);
        this.scene.add( light );
    }

    createGui() {
        this.dims_gui = new dat.GUI({ autoPlace: false });
		//
		//this.dims_gui = new dat.GUI();
        this.dims_gui.domElement.id = 'gui';
        document.getElementById("gui_container").appendChild(this.dims_gui.domElement);
    }

	drawAxes() {
		var axes = new THREE.AxesHelper( 100 );
        axes.material.linewidth = 3;
		this.scene.add( axes );
	}

	setDimNames(dims){
		this.dimNames = dims;
	}

    setDataArray(dataArray) {
        this.dataArray = dataArray;
    }

	createSphere(data, col){
		var material = new THREE.MeshPhongMaterial( {color: col} );
		var sphere = new THREE.Mesh(this.sphereGeometry, material);
		sphere.position.x = data[1][this.proectionSubSpace[0]];
		sphere.position.y = data[1][this.proectionSubSpace[1]];
		sphere.position.z = data[1][this.proectionSubSpace[2]];
		sphere.dataObject = data;
        //sphere.clone();
		//data[3] = sphere;
		this.groupOfSpheres.add(sphere);
		return sphere;
	}

	animate() {
		this.renderer.render( this.scene, this.camera );
	}

	onResize() {

		this.camera.aspect = this.mainDiv.clientWidth / this.mainDiv.clientHeight;
		this.camera.updateProjectionMatrix();
		this.renderer.setSize( this.mainDiv.clientWidth, this.mainDiv.clientHeight );

	}

	onMouseClick(event) {
		event.preventDefault();
        if (this.dims_gui.__folders['Multidimensional Coordinates']) {
            this.dims_gui.removeFolder(this.dims_folder);
        }
        if (this.selectedObject!=null) {
            this.unSelectObject(this.selectedObject);
            this.selectedObject = null;
        }
		this.intersects = this.getIntersects( event.layerX, event.layerY );
		if ( this.intersects.length > 0 ) {
			var res = this.intersects.filter( function ( res ) {

				return res && res.object;

			} )[ 0 ];

			if ( res && res.object ) {
				this.selectedObject = res.object;
				this.selectObject(this.selectedObject);
                var gui_data = {};
                var id = this.dimNames[0];
                var id_value = this.selectedObject.dataObject[ 0 ];
                gui_data[id] = id_value;
                for(var i = 0; i < this.selectedObject.dataObject[1].length; i++) {
                    gui_data[this.dimNames[i+1]] = this.selectedObject.dataObject[ 1 ][ i ]
                }
                this.createGui();
                if (!this.dims_gui.__folders['Multidimensional Coordinates']) {
                    this.dims_folder = this.dims_gui.addFolder('Multidimensional Coordinates');
                }
                for (var key in gui_data) {
                    this.dims_folder.add(gui_data, key).listen();
                }
                this.dims_folder.open();

			}

		}

	}

	selectObject(obj){
		var geometry = new THREE.BoxBufferGeometry( 2*obj.geometry.parameters.radius, 2*obj.geometry.parameters.radius, 2*obj.geometry.parameters.radius );
		var edges = new THREE.EdgesGeometry( geometry );
		var line = new THREE.LineSegments( edges, new THREE.LineBasicMaterial( { color: 0xffffff } ) );
		obj.selectedCircut = line;
		line.position.x = obj.position.x;
		line.position.y = obj.position.y;
		line.position.z = obj.position.z;
		this.selectedObject.material.color.set( invertColor(this.selectedObject.material.color) );
		this.scene.add(line);
	}

	unSelectObject(obj){
		this.scene.remove(obj.selectedCircut);
		obj.selectedCircut = null;
		this.selectedObject.material.color.set( invertColor(this.selectedObject.material.color) );

	}

	getIntersects(x, y) {

		x = ( x / this.mainDiv.clientWidth ) * 2 - 1;
		y = - ( y / this.mainDiv.clientHeight ) * 2 + 1;

		this.mouseVector.set( x, y, 0.5 );
		this.raycaster.setFromCamera( this.mouseVector, this.camera );

		return this.raycaster.intersectObject( this.groupOfSpheres, true );

	}

	changeRad(newRad){
		var oldGroup = this.groupOfSpheres;
		this.scene.remove(this.groupOfSpheres);
		this.groupOfSpheres = new THREE.Group();
		this.sphereGeometry = new THREE.SphereGeometry( newRad, this.numberOfSegements, this.numberOfSegements );
		this.defaultSpRad = newRad;
		var i = 0;
		for (i=0; i < oldGroup.children.length; ++i) {
			if (this.selectedObject === oldGroup.children[i])
				this.selectedObject = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].material.color);
			else {
                var newSphere = this.createSphere(oldGroup.children[i].dataObject, oldGroup.children[i].material.color);
            }
		}
        this.scene.add(this.groupOfSpheres);
	}

	moveSpheres(){
		var i = 0;
		if (this.selectedObject!=null)
			this.unSelectObject(this.selectedObject);
		for (i=0; i<this.groupOfSpheres.children.length; ++i){
			var sphere = this.groupOfSpheres.children[i];
			sphere.position.x = sphere.dataObject[1][this.proectionSubSpace[0]];
			sphere.position.y = sphere.dataObject[1][this.proectionSubSpace[1]];
			sphere.position.z = sphere.dataObject[1][this.proectionSubSpace[2]];
		}
		if (this.selectedObject!=null)
			this.selectObject(this.selectedObject);
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

	dimensionControlElements() {
        var chooseDimArray = [];
		var dimensionsForm = document.getElementById("dimensions_form");
		var XYZSelector = dimensionsForm.getElementsByTagName("select");
        for (var i = 0; i < XYZSelector.length; i++ ) {
            var currSelector = XYZSelector[ i ];
            for (var j = 1; j < this.dimNames.length; j++ ) {
                var option = document.createElement("option");
                if (this.proectionSubSpace[ i ] == j - 1)
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
				parseInt(this.dimsSelectArray[1].value), parseInt(this.dimsSelectArray[2].value));
        };
	}

    // {'parameter1': self.parameter1, 'parameter2': self.parameter2, 'parameter3': self.parameter3}
    getClusterAlgorithm() {
        this.parameters_str = '{"Number of clusters": 10}'; // example json string
        this.parameters_dict = JSON.parse(this.parameters_str);
        var e = document.getElementById("cluster-selector");
        this.algorithm = e.options[e.selectedIndex].value;
        var self = this;
        e.addEventListener('change', function (e) {
            if (document.getElementById("cluster-params")) {
                removeElement("cluster-params");
            }
            var alg = e.target.value;
            var params_div = document.createElement("div");
            params_div.setAttribute("id", "cluster-params");
            params_div.classList.add("form-group");
            document.getElementById("cluster_form").appendChild(params_div);
            switch(alg) {
              case 'K-Means':
                var form = document.createElement("div");
                form.classList.add("form-group");
                params_div.appendChild(form);
                for ( var key in self.parameters_dict ) {
                    if (self.parameters_dict.hasOwnProperty(key)) {
                        var val = self.parameters_dict[key];
                        var label = document.createElement("label");
                        label.setAttribute("for", key);
                        label.textContent = key;
                        var input = document.createElement("input");
                        input.classList.add("form-control-sm");
                        input.setAttribute("type", "text");
                        input.setAttribute("placeholder", val);
                        input.setAttribute("id", key);
                        form.appendChild(label);
                        form.appendChild(input);
                    }
                }
                break;

              case 'DBSCAN':
                  if (document.getElementById("cluster-params")) {
                    removeElement("cluster-params");
                  }
                  break;
            }
        });
    }


    // read algorithm parameters from json file
    setAlgorithmParams() {
        
    }

    radiusControlElement() {
        var changeRadiusBtn = document.getElementById("changeRadiusBtn");
        var radiusRange = document.getElementById("radiusRange");
        changeRadiusBtn.sceneObject = this;
        radiusRange.value = this.defaultSpRad.toString();
		changeRadiusBtn.onclick = function() {
            var radiusRange = document.getElementById("radiusRange");
            console.log(radiusRange.value);
			this.sceneObject.changeRad(parseInt(radiusRange.value));
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
        var printAllBtn = document.getElementById("printBtn");
        printAllBtn.sceneObject = this;
        printAllBtn.onclick=function() {
            if ( document.getElementById('table-results') ) {
			    this.outputDiv.removeChild(this.outputTable);
		    }
			this.sceneObject.printAllElements();
        };
    }

	createControlElements() {
        this.dimensionControlElements();
        this.radiusControlElement();
        this.resetControls();
        this.printControls();
	}

    // print fragment of the initial dataset
    // nrows = the number of rows
    printInitialDataset(nrows) {
        var initial_dataset = document.getElementById("initial-dataset");
        var table = document.createElement("table");
        table.setAttribute("id", "dataset");
		table.classList.add("table", "table-sm", "table-hover");
        var thead = document.createElement("thead");
        table.appendChild(thead);
		var row = document.createElement("tr");
		thead.appendChild(row);
        var th = null;
        for(var i = 0; i < this.dimNames.length; ++i ) {
			th = document.createElement("th");
			th.innerText = this.dimNames[i].toString();
			row.appendChild(th);
		}
        var tbody = document.createElement("tbody");
        table.appendChild(tbody);
        for ( var j=0; j < nrows; ++j ) {
			var obj	= this.dataArray[j];
			row = document.createElement("tr");

			th = document.createElement("th");
			th.innerText = obj[0];
			row.appendChild(th);

			for(var i = 0; i < obj[1].length; i++ ) {
				var td = document.createElement("td");
				td.innerText = obj[1][i];
				row.appendChild(td);
			}
			tbody.appendChild(row);
		}
        this.outputTable = table;
		this.outputDiv.appendChild(this.outputTable);
        initial_dataset.appendChild(table);
    }

	printAllElements(){
		var table = document.createElement("table");
        table.setAttribute("id", "table-results");
		table.classList.add("table", "table-sm", "table-hover");
        var thead = document.createElement("thead");
        table.appendChild(thead);
		var row = document.createElement("tr");
		thead.appendChild(row);

		var cell = null;

		for(var i = 0; i < this.dimNames.length; ++i ) {
			cell = document.createElement("th");
			cell.innerText = this.dimNames[i].toString();
			row.appendChild(cell);
		}
		cell = document.createElement("th");
		cell.innerText = "Cluster";
		row.appendChild(cell);

        var tbody = document.createElement("tbody");
        table.appendChild(tbody);

		for ( var j=0; j < this.groupOfSpheres.children.length; ++j ){
			var obj	= this.groupOfSpheres.children[j];
			row = document.createElement("tr");
			tbody.appendChild(row);

			cell = document.createElement("th");
			cell.innerText = obj.dataObject[0].toString();
			row.appendChild(cell);

			for(var i = 0; i < obj.dataObject[1].length; i++ ){
				cell = document.createElement("td");
				cell.innerText = obj.dataObject[1][i].toString();
				row.appendChild(cell);
			}
			cell = document.createElement("td");
			if (this.selectObject==obj)
				cell.bgColor = invertColor(obj.material.color).getHexString();
			else
				cell.bgColor = obj.material.color.getHexString();
			row.appendChild(cell);
		}
        this.outputTable = table;
		this.outputDiv.appendChild(this.outputTable);
	}
}