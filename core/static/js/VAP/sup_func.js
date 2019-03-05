// A function to validate integer input.
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

//function to validate float input.
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

//Function that validates input depending on type of field.
function validate_field(input){
    switch (input.typeOfField){
        case 'integer':
            var result=validate_integer(input);
            if (result === true)
                return true;
            console.log(result);
            alert(result);
            return false;
        case 'float':
            var result=validate_float(input);
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

// Creates clusterization GUI elements. 
function createClusterElements(divElement, formElement, cluster_params, curr_algorithm, curr_values) {
    //Create the selector in the div.
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
    
    //Create options and input fields for all the clusterization options. 
    var elements = [];
    for ( var k = 0; k < cluster_params.length; k++ ) {
        //Create the option element and the div element assosiated with it.
		var el = cluster_params[ k ];
        var option_element = document.createElement('option');
        option_element.innerText = el[ 1 ];
        option_element.value = el[ 0 ];
        select_element.appendChild(option_element);
        var element_div = document.createElement('div');
        element_div.classList.add("form-group");
        elements.push(element_div);
        element_div.inputElements = [];

        //Creates inputs for all the 
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

        //Make the right element visible
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


function createSwitch(ID, name, label, size, state, texton, textoff){
    while(document.getElementById(ID)!==null)
        ID+=(Math.random()*10).toString().slice(-1);
    
    var outerDiv=document.createElement('div');
    outerDiv.id = ID;
    var par = document.createElement('label');
    par.id=ID+'label';
    par.innerText=label;
    var switchElement=document.createElement('div');
    switchElement.classList.add('switch', size);
    switchElement.id=ID+'switchdiv';

    var inputElement = document.createElement('input');
    inputElement.id=ID+'input';
    inputElement.type='checkbox';
    inputElement.name=name;
    inputElement.checked=state;
    inputElement.classList.add('switch-input');
    switchElement.appendChild(inputElement);

    var labelElement = document.createElement('label');
    labelElement.id=ID+'labelelement';
    labelElement.classList.add('switch-paddle');
    labelElement.setAttribute('for', inputElement.id);

    var span=document.createElement('span');
    span.classList.add('show-for-sr');
    span.innerText=label;
    labelElement.appendChild(span);

    if(texton!=''){
        var span=document.createElement('span');
        span.classList.add('switch-active');
        span.setAttribute('aria-hidden','true');
        span.innerText=texton;
        labelElement.appendChild(span);  
    }

    if(textoff!=''){
        var span=document.createElement('span');
        span.classList.add('switch-inactive');
        span.setAttribute('aria-hidden','true');
        span.innerText=textoff;
        labelElement.appendChild(span);  
    }

    switchElement.appendChild(labelElement);
    outerDiv.appendChild(par);
    outerDiv.appendChild(switchElement);
    outerDiv.switchElement = switchElement;
    outerDiv.inputElement = inputElement;
    outerDiv.label = par;

    return outerDiv;
}

//Creates data table for information output. Use this for static tables.
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

//Adds the element to data table. Use this for static tables.
function addElementToDataTable(table, data, id, numberOfHead=1, checkUnique=true){
    if (checkUnique)
        for(var i=0; i<table.bodyElement.rows.length; ++i){
            if(table.bodyElement.rows[i].uniqueID==id){
                return table.bodyElement.rows[i];
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

//Creates data table for dynamic information output. Use this for dynamic tables.
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
    var columndef=[{ className: "datatableboldcolumn", "targets": [...Array(numofheadrows).keys()] },
        { "render": function ( data, type, row ) {
          if(typeof data == 'number')
              return data.toLocaleString(undefined, { maximumSignificantDigits: 3 });
          else
              return data.toString();
      },"targets": "_all"}];
    if (cust_col_def!==null){
        var columndef=columndef.concat(cust_col_def);
    }
    table.dataTableObj = $('#'+table.id).DataTable({
        "columnDefs": columndef,
        "rowId": id_num,
        "deferRender": true});
    return table;
}

//Adds a row to a dynamic table
function addElementToDataTableDynamic(table, data){
    return table.dataTableObj.row.add(data).draw();
}

//Removes a row from dynamic table
function removeElementFromDataTableDynamic(table, id){
    table.dataTableObj.row('#'+id.toString()).remove();
    table.dataTableObj.draw();
    return null;
}

function deleteDataTable(table){
    table.dataTableObj.destroy();
    table.parentElement.removeChild(table);
}

//Prints dataset to a static data table
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

//Creates a basic GUI form
function createControlBasics(formID){
    while(document.getElementById(formID)!==null)
        formID+=(Math.random()*10).toString().slice(-1);
    var form = document.createElement('form');
    form.id = formID;
    var div = document.createElement('div');
    div.classList.add('form-group', 'form-check', 'text-center');
    form.appendChild(div);
    form.groupDiv = div;
    form.createNewLine = function(){this.groupDiv.appendChild(document.createElement('br'));};
    return form;
}

//Creates a radio button with a label and given name.
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

function createTopElement(tabTitleParentElement, tabContentParentElement, tabId, tabTitle, selected){
    while(document.getElementById(tabId)!==null)
        tabId+=(Math.random()*10).toString().slice(-1);

    var tabTitle = document.createElement('li');
    tabTitle.id = tabId + 'title';
    tabTitle.classList.add('tabs-title');
    if (selected)
        tabTitle.classList.add('is-active');
    tabTitle.role='presentation';

    var tabTitleLink = document.createElement('a');
    tabTitleLink.href = '#'+tabId;
    tabTitleLink.role = 'tab';
    tabTitleLink.id = tabId+'link';
    tabTitleLink.tabindex = '-1';
    tabTitleLink.innerText = tabTitle;
    if (selected)
        tabTitleLink.setAttribute('aria-selected', 'true');
    else
        tabTitleLink.setAttribute('aria-selected', 'false');
    tabTitleLink.setAttribute('aria-controls', tabId);
    tabTitle.appendChild(tabTitleLink);

    var tabContentDiv = document.createElement('div');
    tabContentDiv.classList.add('tabs-panel');
    tabContentDiv.id = tabId;
    tabContentDiv.role='tabpanel';
    tabContentDiv.setAttribute('aria-labelledby', tabId+'-label');
    if (selected)
        tabContentDiv.classList.add('is-active');
    
    tabTitle.contentDiv = tabContentDiv;
    tabContentDiv.tabTitleElement = tabTitle;
    tabTitleParentElement.appendChild(tabTitle);
    tabContentParentElement.appendChild(tabContentDiv);

    return tabContentDiv;
}

function printStats(stats, dimensions, parent){
    var initial_dataset = document.getElementById(parent);
    var table = document.createElement("table");
    table.setAttribute("id", "stats-table");
    table.classList.add("hover");
    var thead = document.createElement("thead");
    var row, th, td;

    // first row with statistics column names
    row = document.createElement("tr");
    th = document.createElement("th");
    th.innerText = "  ";
    row.appendChild(th);
    for ( var j = 0; j < stats[ 0 ].length; j++ ) {
        th = document.createElement("th");
        th.innerText = stats[0][j];
        row.appendChild(th);
    }
    thead.appendChild(row);
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    for(var i = 0; i < dimensions.length; i++ ) {
        row = document.createElement("tr");
        th = document.createElement("th");
        th.innerText = dimensions[ i ].toString();
        row.appendChild(th);
        for ( var j = 0; j < stats[ 0 ].length; j++ ) {
            var stat_value = stats[ 1 ][ j ][ i ];
            td = document.createElement("td");
            td.innerText = stat_value.toLocaleString(undefined, { maximumSignificantDigits: 3 });
            row.appendChild(td);
        }
        tbody.appendChild(row);
    }
    table.appendChild(tbody);
    initial_dataset.appendChild(table);
    $(table).dataTable();
}

function rgbToHex(color) {
    var R = color["r"] * 255;
    var G = color["g"] * 255;
    var B = color["b"] * 255;
    return "#"+toHex(R)+toHex(G)+toHex(B);
}
function toHex(n) {
 n = parseInt(n,10);
 if (isNaN(n)) return "00";
 n = Math.max(0,Math.min(n,255));
 return "0123456789ABCDEF".charAt((n-n%16)/16)
      + "0123456789ABCDEF".charAt(n%16);
}

function cluster_selector(clusters_color_scheme, parent_element) {
    var selector = document.getElementById("clusters");
    var label = document.createElement("label");
    label.innerHTML = "Choose Cluster";
    var btnGroup = document.createElement("div");
    btnGroup.classList.add("small");
    btnGroup.classList.add("button-group");
    for (var cluster in clusters_color_scheme) {
        var color = clusters_color_scheme[cluster];
        var a = document.createElement("a");
        a.setAttribute("href","#")
        a.classList.add("button");
        a.innerHTML = cluster;
        a.style.background = rgbToHex(color);
        a.onclick=function(event) {
            event.preventDefault();
            var cluster_stat = document.getElementById(parent_element);
            while (cluster_stat.firstChild) {
                cluster_stat.removeChild(cluster_stat.firstChild);
            }
            var parent = document.getElementById(parent_element);
            var h3 = document.createElement("h3");
            h3.innerText = "Cluster №" + parseInt(event.target.innerText) + " statistics";
            h3.style.background = event.target.style.background;
            parent.appendChild(h3);
            printClusterStats(scene.realData, scene.clusters, parseInt(event.target.innerText), scene.dimNames, parent_element);
        };
        btnGroup.appendChild(a);
    }
    selector.appendChild(label);
    selector.appendChild(btnGroup);
}

function printClusterStats(realdata, clusters, cluster_number, dimNames, parent_element) {
    var cluster_list = [];
    for (var i = 0; i < clusters.length; i++ ) {
        if (clusters[i] == cluster_number)
            cluster_list.push(i);
    }
    var data_cluster = [];
    for (var j = 0; j < realdata.length; j++) {
        if (cluster_list.includes(j) === true)
            data_cluster.push(realdata[j][1]);
    }
    var result = Array.from({ length: data_cluster[0].length }, function(x, row) {
      return Array.from({ length: data_cluster.length }, function(x, col) {
        return data_cluster[col][row];
      });
    });
    var count = result[0].length;
    var stat = [];
    stat.push(["Min", "Max", "Mean", "Std"]);
    var means = [];
    var maxs = [];
    var mins = [];
    var stds = [];
    for (var i = 0; i < result.length; i++) {
        var mean = ss.mean(result[i]),
        std = ss.standardDeviation(result[i]),
        min = ss.min(result[i]),
        max = ss.max(result[i]);
        means.push(mean);
        maxs.push(max);
        mins.push(min);
        stds.push(std);
    }
    stat.push([mins, maxs, means, stds]);
    var count_info = document.createElement("h5");
    count_info.innerText = "Number of elements: " + count.toString();
    var parent = document.getElementById(parent_element);
    parent.appendChild(count_info);

    printStats(stat, dimNames, parent_element);
}

function add_parameters(submited_form) {
    var new_input = document.createElement('input');
    new_input.name = 'visualparameters';
    new_input.type = 'hidden';
    new_input.value = JSON.stringify(scene.saveParameters());
    submited_form.appendChild(new_input);
}

function fix_array(data) {
    var new_array = new Array(data.length);
    for (var i = 0; i < data.length; i++) {
        var values = [];
        for (var j = 0; j < data[i][1][0].length; j++) {
            values[j] = data[i][1][0][j];
        }
        new_array[i] = [data[i][0].toString(), values];
    }
    return new_array;
}