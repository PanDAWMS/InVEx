function invertColor(color) {
	return new THREE.Color(1.0-color.r, 1.0-color.g, 1.0-color.b);
}

function drawPlainGrid( theme='black' ) {
	if (theme=='white')
		var grid = new THREE.GridHelper(200, 20, '#000', '#000');
	else
		var grid = new THREE.GridHelper(200, 20, '#5BB', '#FFF');
	grid.position.y-=0.2; //Position the grid a bit under the axes
	return grid;
}

function drawAxes() {
	var axes = new THREE.AxesHelper( 100 );
	return axes;
}

class Scene {

	// #region Scene initialization
	constructor(mainDiv) {
			this.mainDiv = mainDiv;
			mainDiv.sceneObject = this;

			this.proectionSubSpace = [0,1,2];
			this.dimNames=[];
			this.outputTable = null;

			// init renderer
			this.renderer = new THREE.WebGLRenderer( { antialias: true } );
			this.renderer.setPixelRatio( window.devicePixelRatio );
			this.renderer.setSize( mainDiv.clientWidth, mainDiv.clientHeight );
			mainDiv.appendChild( this.renderer.domElement );

			// init scene
			this.scene = new THREE.Scene();

			this.groupOfGrid = new THREE.Group();
			this.scene.add(this.groupOfGrid);

			// init camera
			this.camera = new THREE.PerspectiveCamera( 50, 2, 1, 1000 );
			this.camera.position.set(120, 120, 120);
			this.camera.lookAt( 0, 0, 0 );

			this.controls = new THREE.OrbitControls( this.camera, this.renderer.domElement );
        this.controls.enableRotate = true;
        this.controls.target = new THREE.Vector3(0, 0, 0);
			this.controls.saveState();
			
			this.grid = undefined;
			this.groupOfGrid.add(drawAxes());      

			// Load theme settings
			this.theme = getCookie('colortheme');
			if (this.theme == "")
				this.theme = 'black';
			else{
				setCookie('colortheme', this.theme, 14);
			}
			
        //Set up the quality ranges and parameters for each quality.
			this.__qualityRange = [{'value':'exlow', 'text':'Extra low'}, 
								{'value':'low', 'text':'Low'},
								{'value':'med', 'text':'Medium'},
								{'value':'high', 'text':'High'},
								{'value':'exhigh', 'text':'Extra high'}];
			this.quality = getCookie('quality');
			if (this.quality == "")
				this.quality = 'med';
			else
				setCookie('quality', this.quality, 14);

            // init lights
            this.initLight();
			this.createGui();
			this.csrf = document.getElementsByName("csrfmiddlewaretoken")[0].getAttribute("value");

        this.resizeCanvasToDisplaySize();
    }

    resizeCanvasToDisplaySize() {
        const canvas = this.renderer.domElement;
        // look up the size the canvas is being displayed
        const width = this.mainDiv.clientWidth - 30;
        const height = this.mainDiv.clientHeight - 20;

        // adjust displayBuffer size to match
        if (canvas.width !== width || canvas.height !== height) {
            // you must pass false here or three.js sadly fights the browser
            this.renderer.setSize(width, height);
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
        }
    }

	saveVisualParameters(){
		return {'camerapos': this.camera.position,
			'camerarot': this.camera.rotation,
			'subspace': this.proectionSubSpace,
			'sphrad': this.defaultSpRad};
	}
	
	loadVisualParameters(parametersDict){
		if ('camerapos' in parametersDict){
			this.camera.position.x = parametersDict['camerapos'].x;
			this.camera.position.y = parametersDict['camerapos'].y;
			this.camera.position.z = parametersDict['camerapos'].z;
		}
		
		if ('camerarot' in parametersDict){
			this.camera.rotation.order = parametersDict['camerarot']._order;
			this.camera.rotation.x = parametersDict['camerarot']._x;
			this.camera.rotation.y = parametersDict['camerarot']._y;
			this.camera.rotation.z = parametersDict['camerarot']._z;
		}
		
		if ('subspace' in parametersDict){
			this.proectionSubSpace = parametersDict['subspace'];
		}
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

	setSource(dsID){
		this.dsID = dsID;
	}

	// #endregion
	// #region GUI related

    createGui() {
        this.dims_gui = new dat.GUI({ autoPlace: false, width: 300 });
        this.dims_gui.domElement.id = 'gui';
        document.getElementById("gui_container").appendChild(this.dims_gui.domElement);
	}

	// Creates dimension control elements with selectors.
	dimensionControlElements() {
		var dimensionControlID = 'dimensionControl';
		while(document.getElementById(dimensionControlID)!==null)
			dimensionControlID+=(Math.random()*10).toString().slice(-1);

		var form = createControlBasics('form' + dimensionControlID);
		var XYZSelector = [];

		var selectbox = document.createElement('select');
		selectbox.classList.add('form-control', 'form-control-sm');
		selectbox.id = 'x_' + dimensionControlID;
		selectbox.name = 'x_' + dimensionControlID;
		selectbox.style.color = 'red';
		XYZSelector.push(selectbox);
		form.groupDiv.appendChild(selectbox);

		selectbox = document.createElement('select');
		selectbox.classList.add('form-control', 'form-control-sm');
		selectbox.id = 'y_' + dimensionControlID;
		selectbox.name = 'y_' + dimensionControlID;
		selectbox.style.color = 'green';
		XYZSelector.push(selectbox);
		form.groupDiv.appendChild(selectbox);

		selectbox = document.createElement('select');
		selectbox.classList.add('form-control', 'form-control-sm');
		selectbox.id = 'z_' + dimensionControlID;
		selectbox.name = 'z_' + dimensionControlID;
		selectbox.style.color = 'blue';
		XYZSelector.push(selectbox);
		form.groupDiv.appendChild(selectbox);
		
        for ( var i = 0; i < XYZSelector.length; i++ ) {
            for ( var j = 0; j < this.dimNames.length; j++ ) { // Create options for all the dimensions
				var option = document.createElement("option");
                if ( this.proectionSubSpace[ i ] == j )
					option.selected = true;
                option.value = j.toString();
				option.text = this.dimNames[ j ];
				XYZSelector[i].add(option);
            }
		}
		
        var changeDimBtn = document.createElement('input'); //Create button to change the dimension
		changeDimBtn.id = 'button' + dimensionControlID;
		changeDimBtn.setAttribute('type', 'button');
		changeDimBtn.value = 'Change Dimensions';
		changeDimBtn.title = 'This may take some time';
		changeDimBtn.classList.add('button', 'small');
        changeDimBtn.sceneObject = this;
		changeDimBtn.dimsSelectArray = XYZSelector;
		changeDimBtn.onclick=function(){
			this.sceneObject.setNewSubSpace(parseInt(this.dimsSelectArray[0].value),
											parseInt(this.dimsSelectArray[1].value),
											parseInt(this.dimsSelectArray[2].value));
			this.sceneObject.renderer.render(this.sceneObject.scene,
											 this.sceneObject.camera);
		};
		form.appendChild(changeDimBtn);

		return form;
	}

	// Creates the reset camera button and form around it.
    resetControls() {
		var resetID = 'resetBtn';
		while(document.getElementById(resetID)!==null)
			resetID+=(Math.random()*10).toString().slice(-1);

		var form = createControlBasics('form' + resetID);
		
		var resetCameraBtn = document.createElement('input');
		resetCameraBtn.id = resetID;
		resetCameraBtn.classList.add('button', 'small');
		resetCameraBtn.setAttribute('type', 'button');
		resetCameraBtn.value = 'Reset Camera';
		resetCameraBtn.sceneObject = this;
		resetCameraBtn.onclick = function() {
			this.sceneObject.resetCamera();
		};
		form.groupDiv.appendChild(resetCameraBtn);

		return form;
    }
	
	// Creates quality controls. 
	changeQualityControls() {
		var changeQualityID = 'changeQuality';
		while(document.getElementById(changeQualityID)!==null)
			changeQualityID+=(Math.random()*10).toString().slice(-1);
		// Form contains all the elements of the quality controls.
		var form = createControlBasics('form' + changeQualityID);
		//Selectbox contains the quality options
		var selectbox = document.createElement('select');
		selectbox.classList.add('form-control', 'form-control-sm');
		selectbox.id = changeQualityID;
		selectbox.name = changeQualityID;

		var option = null;
		for(var i=0; i<this.__qualityRange.length; ++i){
			option = document.createElement('option');
			option.value = this.__qualityRange[i]['value'];
			option.innerText = this.__qualityRange[i]['text'];
			selectbox.appendChild(option);
		}
		selectbox.value = this.quality;
		//Label for the quality control.
		var label = document.createElement('label');
		label.id = 'for' + selectbox.id;
		label.setAttribute('for', selectbox.id);
		label.innerText = 'Select quality: ';
		form.groupDiv.appendChild(label);
		form.groupDiv.appendChild(selectbox);
		form.createNewLine();
		//Button to change the quality.
		var button = document.createElement('input');
		button.id = 'button' + changeQualityID;
		button.setAttribute('type', 'button');
		button.value = 'Change Quality';
		button.title = 'This may take some time';
		button.qualitybox = selectbox;
		button.classList.add('button', 'small');
		button.sceneObject = this;
		button.onclick = function(){
			this.sceneObject.changeQuality(button.qualitybox.value);
		}
		form.groupDiv.appendChild(button);
		return form;
	}
	
	// Creates Theme controls
	changeThemeControls() {
		var changeThemeID = 'changeTheme';
		while(document.getElementById(changeThemeID)!==null)
			changeThemeID+=(Math.random()*10).toString().slice(-1);
			// Form contains all the elements of the theme controls.
		var form = createControlBasics('form' + changeThemeID);
		//Selectbox contains the themes options. Changes theme on change.		
		var selectbox = document.createElement('select');
		selectbox.classList.add('form-control', 'form-control-sm');
		selectbox.id = changeThemeID;
		selectbox.name = changeThemeID;

		var option = document.createElement('option');
		option.value = 'black';
		option.innerText = 'Black';
		selectbox.appendChild(option);

		var option = document.createElement('option');
		option.value = 'white';
		option.innerText = 'White';
		selectbox.appendChild(option);

		selectbox.value = this.theme;
		selectbox.sceneObject = this;
		selectbox.onchange = function(){
			this.sceneObject.changeTheme(this.value);
		}

		var label = document.createElement('label');
		label.id = 'for' + selectbox.id;
		label.setAttribute('for', selectbox.id);
		label.innerText = 'Select Theme: ';
		form.groupDiv.appendChild(label);
		form.groupDiv.appendChild(selectbox);

		return form;
	}

	//Main function to create control elements. Fullload indicates if all the control should be created
	createControlElements(dimensionControlElement, sceneControlElement, fullload=true) {
		if(fullload){
			dimensionControlElement.appendChild(this.dimensionControlElements());
		}
        sceneControlElement.appendChild(this.changeThemeControls());
        sceneControlElement.appendChild(this.changeQualityControls());
        sceneControlElement.appendChild(this.resetControls());
	}
	// #endregion

	// #region User interaction
	// Changes the theme. Currently there are two themes "white" and "black"
	changeTheme(newTheme){
		if (newTheme=='white'){
			this.theme = 'white';
		}
		else{
			this.theme = 'black';
		}
		if (this.grid !== undefined)
		{
			this.groupOfGrid.remove(this.grid);
		}
		this.grid = drawPlainGrid(this.theme);
		this.groupOfGrid.add(this.grid);
		setCookie('colortheme', this.theme, 14);
	}

	// Changes the quality of the picture. 
	changeQuality(quality){
		for(var i = 0; i<this.__qualityRange.length; ++i){
			if(quality == this.__qualityRange[i]['value']){
				var realquality = true;
			}
		}
		if (!realquality)
			quality = this.___qualityRange[3]['value'];
		this.redrawScene(); //Redraws the scene with the new quality.
		this.quality = quality;
		setCookie('quality', this.quality, 14);
	}

	// Function that is called to render the scene.
    render() {
        this.resizeCanvasToDisplaySize();
        this.renderer.render( this.scene, this.camera );
	}

	// Recalculates everything needed after window resize.
	onResize() {
        this.render();
	}

	redrawScene(){

	}

	setNewSubSpace(x1, x2, x3){
		this.proectionSubSpace[0] = x1;
		this.proectionSubSpace[1] = x2;
		this.proectionSubSpace[2] = x3;
	}

	resetCamera(){
		this.controls.reset();
	}

	// #endregion

	getDimNumber(dimName) {
		return this.dimNames.indexOf(dimName);
	}
}