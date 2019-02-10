

class MeshVisualization extends DataVisualization{

    constructor(mainDiv, defaultRadius, meshDistance, xCoordinates, yCoordinates){
        super(mainDiv, defaultRadius);

        this.groupOfLabels = new THREE.Group();
        
        this.innerMeshDistance = meshDistance;
        this.proectionSubSpace = [0, 2, 1]
        this.meshCoordinates = [[], [], {}, {}];
        this.objectsOnMesh = [];
        this.visibilityState = [true, true, true, true];
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
		
        var changeDimBtn = document.createElement('button'); //Create button to change the dimension
		changeDimBtn.id = 'button' + dimensionControlID;
		changeDimBtn.setAttribute('type', 'button');
		changeDimBtn.innerText = 'Change Dimensions';
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

        var changeDistanceBtn = document.createElement('button');
        changeDistanceBtn.id = 'button' + distChangeID;
        changeDistanceBtn.classList.add('button', 'small');
        changeDistanceBtn.innerText = 'Change Distance';
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

    getColor(realData){
        return [new THREE.Color(0x00FF00), new THREE.Color(0x0000FF), new THREE.Color(0xFFFF00), new THREE.Color(0xFF0000)][this.checkState(realData)];
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
		var material = new THREE.MeshPhongMaterial( {color: this.getColor(realData)} );
		var sphere = new THREE.Mesh(this.sphereGeometry, material);
		sphere.position.x = this.meshCoordinates[0][i][1];
		sphere.position.y = normData[1][this.proectionSubSpace[1]];
        sphere.position.z = this.meshCoordinates[1][j][1];
        if (this.objectsOnMesh[i][j] == undefined)
            this.objectsOnMesh[i][j] = [];
        this.objectsOnMesh[i][j].push(sphere);
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
                        if (this.objectsOnMesh[i][j][k].selectedCircut != undefined){
                            this.objectsOnMesh[i][j][k].selectedCircut.position.x = this.objectsOnMesh[i][j][k].position.x;
                            this.objectsOnMesh[i][j][k].selectedCircut.position.y = this.objectsOnMesh[i][j][k].position.y;
                            this.objectsOnMesh[i][j][k].selectedCircut.position.z = this.objectsOnMesh[i][j][k].position.z;
                            this.objectsOnMesh[i][j][k].material.color = invertColor(this.getColor(this.objectsOnMesh[i][j][k].realData)); 
                        }
                        else
                            this.objectsOnMesh[i][j][k].material.color = this.getColor(this.objectsOnMesh[i][j][k].realData); 
                    }
    }
    
    setNewSubSpace(x2){
        super.setNewSubSpace(0, x2, 1);
		this.moveSpheres();
    }
    //#endregion
}