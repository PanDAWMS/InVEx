function validate_integer(input){
    if (!Number.isInteger(+input.value))
        return "The value of "+input.labelText+" must be an integer";
    if (input.minInputValue !== undefined && input.value < input.minInputValue)
        return "The value of "+input.labelText+" must not be less than " + input.minInputValue.toString();
    if (input.maxInputValue !== undefined && input.value > input.maxInputValue)
        return "The value of "+input.labelText+" must not be more than " + input.maxInputValue.toString();
    input.value = (+input.value).toString();
    return true;
}

function validate_float(input){
    if (Number.isNaN(+input.value))
        return "The value of "+input.labelText+" must be an number";
    if (input.minInputValue !== undefined && input.value < input.minInputValue)
        return "The value of "+input.labelText+" must not be less than " + input.minInputValue.toString();
    if (input.maxInputValue !== undefined && input.value > input.maxInputValue)
        return "The value of "+input.labelText+" must not be more than " + input.maxInputValue.toString();
    input.value = (+input.value).toString();
    
    return true;
}

function validate_field(input){
    switch (input.typeOfField){
        case 'integer':
            result=validate_integer(input);
            if (result === true)
                return true;
            console.log(result);
            alert(result);
            return false;
        case 'float':
            result=validate_float(input);
            if (result === true)
                return true;
            console.log(result);
            alert(result);
            return false;
    }
    return true;
}

function removeElement(id) {
    var elem = document.getElementById(id);
    return elem.parentNode.removeChild(elem);
}

function createClusterElements(divElement, formElement, cluster_params, curr_algorithm, curr_values) {

	var select_element = document.createElement('select');
	select_element.classList.add('form-control');
	select_element.classList.add('form-control-sm');
	select_element.id = 'select' + ("00000" + Math.random()*100000).slice(-5);
	select_element.name = 'algorithm';
    var label_select = document.createElement('label');
    label_select.innerText='Choose clustering algorithm';
    label_select.setAttribute('for', select_element.id);
    divElement.appendChild(label_select);
    divElement.appendChild(select_element);
    divElement.appendChild(document.createElement('br'));
    var elements = [];
    for ( var k = 0; k < cluster_params.length; k++ ) {
		var el = cluster_params[ k ];
        var option_element = document.createElement('option');
        option_element.innerText = el[ 1 ];
        option_element.value = el[ 0 ];
        select_element.appendChild(option_element);
        var element_div = document.createElement('div');
        element_div.classList.add("form-group");
        elements.push(element_div);
        element_div.inputElements = [];
        for( var i = 2; i < el.length; i++ ) {
            var form_group = document.createElement("div");
            form_group.classList.add("form-group");
            var input = document.createElement("input");
            input.classList.add("form-control-sm");
            input.classList.add("mr-4");
            input.setAttribute("type", "text");
            for (var j = 0; j < el[i].attributes.length; j++ ) {
                input.setAttribute(el[ i ].attributes[ j ][ 0 ], el[ i ].attributes[ j ][ 1 ]);
            }
            input.id = 'inp'+("00000" + Math.random()*100000).slice(-5);
            input.setAttribute("name", el[ i ][ 'name' ]);
            if ( curr_values != undefined && el[ 0 ] == curr_algorithm ) {
                input.value = el[ i ][ 'defvalue' ] = curr_values[el[ i ][ 'name' ]];
            } else {
                if ('defvalue' in el[ i ]){
				    input.value = el[ i ][ 'defvalue' ];
                }
            }
            if ('type' in el[ i ]){
                input.typeOfField = el[ i ][ 'type' ];
            }
			if ('min' in el[ i ]){
				input.minInputValue = el[ i ][ 'min' ];
			}
			if ('max' in el[ i ]){
				input.maxInputValue = el[ i ][ 'max' ];
			}
			element_div.inputElements.push(input);
            element_div.validateFields = function(){
                for( var i = 0; i < this.inputElements.length; i++ ){
                    if (!validate_field(this.inputElements[i]))
                        return false;
                }
                return true;
            }
			if ('label' in el[ i ]){
                var label = document.createElement('label');
                label.setAttribute("for", input.id);
                label.textContent = el[ i ][ 'label' ];
                label.classList.add("control-label");
                form_group.appendChild(label);
                input.labelText = el[ i ][ 'label' ];
            }

            form_group.appendChild(input);

            element_div.appendChild(form_group);
        }
        divElement.appendChild(element_div);

        if ( curr_algorithm === undefined && k == 0 ) {
            element_div.style.display = 'block';
            select_element.element_div = element_div;
            select_element.validateFields = function(){return this.element_div.validateFields()};
        }
        else if (curr_algorithm != undefined && option_element.value === curr_algorithm) {
            option_element.selected = true;
            element_div.style.display = 'block';
            select_element.element_div = element_div;
            select_element.validateFields = function(){return this.element_div.validateFields()};
        } else
        	element_div.style.display = 'none';
    }
    select_element.elements = elements;

	select_element.onchange = function() {
        for( var i = 0; i < this.elements.length; i++ ){
            this.elements[i].style.display = 'none';
        }
        this.elements[this.selectedIndex].style.display = 'block';
        select_element.element_div = this.elements[this.selectedIndex];
    };
    if (formElement.validateElements === undefined)
        formElement.validateElements = [select_element];
    else
        formElement.validateElements.push(select_element);
    formElement.addEventListener('submit', function(ev){
        for( var i = 0; i < this.validateElements.length; i++ ){
            if (!this.validateElements[i].validateFields()){
                ev.preventDefault();
                return false;
            }
        }
        return true;
    });
}

function createDataTable(parentElement, ID, headers){
    while(document.getElementById(ID)!==null)
        ID+=(Math.random()*10).toString().slice(-1);

    var table = document.createElement("table");
    table.id = ID;
    table.classList.add("table", "table-sm", "table-hover");

    var thead = document.createElement("thead");
    table.appendChild(thead);
    var row = document.createElement("tr");
    thead.appendChild(row);
    var cell = null;
    for(var i = 0; i < headers.length; i++ ) {
        cell = document.createElement("th");
        cell.innerText = headers[i].toString();
        row.appendChild(cell);
    }

    var tbody = document.createElement("tbody");
    table.appendChild(tbody);
    table.bodyElement = tbody;
    parentElement.appendChild(table);
    return table;
}

function addElementToDataTable(table, data, id, numberOfHead=1, checkUnique=true){
    if (checkUnique)
        for(var i=0; i<table.bodyElement.rows.length; ++i){
            if(table.bodyElement.rows[i].uniqueID==id){
                var row=table.bodyElement.rows[i];
                return row;
            }
        }
    var row = document.createElement("tr");
    row.uniqueID = id;
    row.id=id;
    var cell = null;
    for(var i=0; i<numberOfHead; ++i){
        cell = document.createElement("th");
        if(typeof data[i] == 'number')
            cell.innerText = data[i].toLocaleString(undefined, { maximumSignificantDigits: 3 });
        else
            cell.innerText = data[i].toString();
        row.appendChild(cell);
    }

    for(var i = numberOfHead; i < data.length; i++ ){
        cell = document.createElement("td");
        if(typeof data[i] == 'number')
            cell.innerText = data[i].toLocaleString(undefined, { maximumSignificantDigits: 3 });
        else
            cell.innerText = data[i].toString();
        row.appendChild(cell);
    }
    table.bodyElement.append(row);
    
    return row;
}

function createDataTableDynamic(parentElement, ID, headers, numofheadrows=1, id_num=0, cust_col_def=null){
    while(document.getElementById(ID)!==null)
        ID+=(Math.random()*10).toString().slice(-1);

    var table = document.createElement("table");
    table.id = ID;
    table.classList.add("table", "table-sm", "table-hover");

    var thead = document.createElement("thead");
    table.appendChild(thead);
    var row = document.createElement("tr");
    thead.appendChild(row);
    var cell = null;
    for(var i = 0; i < headers.length; i++ ) {
        cell = document.createElement("th");
        cell.innerText = headers[i].toString();
        row.appendChild(cell);
    }

    var tbody = document.createElement("tbody");
    table.appendChild(tbody);
    table.bodyElement = tbody;
    parentElement.appendChild(table);
    columndef=[{ className: "datatableboldcolumn", "targets": [...Array(numofheadrows).keys()] },
        { "render": function ( data, type, row ) {
          if(typeof data == 'number')
              return data.toLocaleString(undefined, { maximumSignificantDigits: 3 });
          else
              return data.toString();
      },"targets": "_all"}];
    if (cust_col_def!==null){
        columndef=columndef.concat(cust_col_def);
    }
    table.dataTableObj = $('#'+table.id).DataTable({
        "columnDefs": columndef,
        "rowId": id_num,
        "deferRender": true});
    return table;
}

function addElementToDataTableDynamic(table, data){
    var row = table.dataTableObj.row.add(data).draw();
    return row;
}

function removeElementFromDataTableDynamic(table, id){
    table.dataTableObj.row('#'+id.toString()).remove();
    table.dataTableObj.draw();
    return null;
}

function deleteDataTable(table){
    table.dataTableObj.destroy();
    table.parentElement.removeChild(table);
}


function printDataset(element, headers, dataset, num_rows, id_num=0){
    var table = createDataTable(element, element.id+"-table", headers);
    if((num_rows === undefined) || (num_rows>dataset.length))
        num_rows = dataset.length;
    for(var i = 0; i<num_rows; ++i){
        addElementToDataTable(table, [dataset[i][0]].concat(dataset[i][1]), dataset[i][0], 1, false);
    }
    table.dataTableObj = $('#'+table.id).DataTable();
    return table;
}

function createControlBasics(formID){
    while(document.getElementById(formID)!==null)
        formID+=(Math.random()*10).toString().slice(-1);
    var form = document.createElement('form');
    form.id = formID;
    var div = document.createElement('div');
    div.classList.add('form-group', 'form-check');
    form.appendChild(div);
    form.groupDiv = div;
    form.createNewLine = function(){this.groupDiv.appendChild(document.createElement('br'));};
    return form;
}

function createControlRadioWithLabel(radioID, name, text){
    while(document.getElementById(radioID)!==null)
        radioID+=(Math.random()*10).toString().slice(-1);

    var radioButton = document.createElement('input');
    radioButton.id = radioID;
    radioButton.classList.add('form-check-input');
    radioButton.setAttribute('type', 'radio');
    radioButton.setAttribute('name', name);

    var label = document.createElement('label');
    label.id = 'for' + radioButton.id;
    label.classList.add('form-check-label');
    label.setAttribute('for', radioButton.id);
    label.innerText = text;
    radioButton.labelElement = label;
    
    return radioButton;
}