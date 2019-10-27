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
        case 'list':
            // TODO: it's s stub.
            return true;
    }
    return true;
}

function removeElement(id) {
    var elem = document.getElementById(id);
    return elem.parentNode.removeChild(elem);
}

// Creates clusterization GUI elements. 
//GUI structure:
//--------------
//    {label_select} Choose clustering algorithm
//    {select_element} [select]
//
//    {label} / Name of each input field /
//    {input}[input]
//
//    Group:
//        {elements_label_select} Choose clustering features
//        {selectbox} [select] {inputElement}[button "+"]
//
//        {labelHint}(if nothing added) If the list is empty, clusterization is conducted through all features
//
//        {selectedLabel}/ Feature name / {deleteBtn}[button "-"]
//
//    [button "Clusterize"]
//

function get_categorical_features() {
    return features_stat.features.filter(function(obj) {
        return (['nominal','ordinal'].indexOf(obj.measure_type) >= 0);
    });
}

function get_categorical_features_names() {
    var names = [];
    var features = get_categorical_features();
    for ( var i = 0; i < features.length; i++ )
        names.push(features[i]["feature_name"]);
    return names;
}

function get_feature_number(feature_name) {
    return scene.dimNames.concat(scene.auxNames).indexOf(feature_name);
}

function createClusterElements(divElement, formElement, cluster_params, curr_algorithm, curr_values) {
    // The clustering algorithm selector
    var select_element = document.createElement('select');
    select_element.classList.add('form-control');
    select_element.classList.add('form-control-sm');
    select_element.id = 'select' + ("00000" + Math.random() * 100000).slice(-5);
    select_element.name = 'algorithm';

    var label_select = document.createElement('label');
    label_select.innerText='Choose clustering algorithm';
    label_select.setAttribute('for', select_element.id);

    // The variable for keeping the the clustering features list
    var clustering_list_json = document.createElement('input');
    clustering_list_json.type = 'text';
    clustering_list_json.name = 'clustering_list_json';
    clustering_list_json.style.display = 'none';

    // Adding those elements to the div
    divElement.appendChild(clustering_list_json);
    divElement.appendChild(label_select);
    divElement.appendChild(select_element);
    divElement.appendChild(document.createElement('br'));

    // Options and input fields for all the clusterization options
    var elements = [];
    for ( var k = 0; k < cluster_params.length; k++ ) {
        // The option element and the div element assosiated with it
		var el = cluster_params[k],
            option_element = document.createElement('option');
        option_element.innerText = el[1];
        option_element.value = el[0];
        select_element.appendChild(option_element);

        var element_div = document.createElement('div');
        element_div.classList.add("form-group");
        elements.push(element_div);
        element_div.inputElements = [];

        // Form parts for each clusterization option
        for (var i = 2; i < el.length; i++) {
            // Creating the div
            var form_group = document.createElement("div");
            form_group.classList.add("form-group");

            if (el[i]['type'] === 'list') {
                var selector = document.createElement('select');
                selector.classList.add('form-control', 'form-control-sm');
                selector.id = 'inp' + ("00000" + Math.random() * 100000).slice(-5);
                selector.setAttribute("name", el[i]['name']);
                var values = el[i]['values'];
                for (var val = 0; val < values.length; val++) {
                    let option = document.createElement('option');
                    option.innerText = values[val];
                    option.value = values[val];
                    selector.appendChild(option);
                }
                element_div.inputElements.push(selector);
                form_group.appendChild(selector);
            } else {
                // The number of clusters input
                var input = document.createElement("input");
                input.classList.add("form-control-sm");
                input.classList.add("mr-4");
                input.setAttribute("type", "text");

                for (var j = 0; j < el[i].attributes.length; j++)
                    input.setAttribute(el[i].attributes[j][0], el[i].attributes[j][1]);

                input.id = 'inp' + ("00000" + Math.random() * 100000).slice(-5);
                input.setAttribute("name", el[i]['name']);

                // Default parameters
                if (curr_values !== undefined && el[0] === curr_algorithm)
                    input.value = el[i]['defvalue'] = curr_values[el[i]['name']];
                else
                    if ('defvalue' in el[i])
                        input.value = el[i]['defvalue'];

                if ('type' in el[i])
                    input.typeOfField = el[i]['type'];

                if ('min' in el[i])
                    input.minInputValue = el[i]['min'];

                if ('max' in el[i])
                    input.maxInputValue = el[i]['max'];

                element_div.inputElements.push(input);

                // Labels for each input field
                if ('label' in el[i]) {
                    var label = document.createElement('label');
                    label.setAttribute("for", input.id);
                    label.textContent = el[i]['label'];
                    label.classList.add("control-label");
                    form_group.appendChild(label);
                    input.labelText = el[i]['label'];
                }

                form_group.appendChild(input);
            }
            element_div.validateFields = function () {
                for (var i = 0; i < this.inputElements.length; i++)
                    if (!validate_field(this.inputElements[i]))
                        return false;
                return true;
            };

            element_div.appendChild(form_group);
        }

        if (cluster_params[k][0] !== "GroupData")
        {
            // The group for the clustering features list
            // The div element with boundary
            var cluster_div = document.createElement("div");
            cluster_div.id = "features_list_" + cluster_params[k][0];
            cluster_div.classList.add("form-group");
            cluster_div.style.border = '1px solid lightgray';
            cluster_div.style.paddingBottom = '15px';
            cluster_div.style.paddingRight = '6px';
            cluster_div.style.marginBottom = '10px';

            // The 'Choose clustering features' label
            var elements_label_select = document.createElement('label');
            elements_label_select.innerText = 'Choose clustering features';
            cluster_div.appendChild(elements_label_select);
            cluster_div.appendChild(document.createElement('br'));

            // The SelectBox with the features list
            var selectbox = document.createElement('select');
            selectbox.classList.add('form-control', 'form-control-sm');
            selectbox.id = 'clusteringSelectBox_' + cluster_params[k][0];
            selectbox.style.width = '80%';

            // Options of that box
            for (let j = 0; j < scene.dimNames.length; j++) {
                let option = document.createElement("option");
                if (j === 0) option.selected = true;
                option.value = j.toString();
                option.text = scene.dimNames[j];
                option.id = 'option_' + scene.dimNames[j] + "_" + cluster_params[k][0];
                selectbox.add(option);
            }

            cluster_div.appendChild(selectbox);

            // The function for filling the clustering_list_json text
            var recalculate_json = function (params) {
                var clustering_list_json = document.getElementsByName('clustering_list_json')[0];

                var clustering_list = [],
                    nodes = $('#clustering_elements_' + params)[0].childNodes;

                for (var i = 0; i < nodes.length; i++)
                    clustering_list.push(nodes[i].dataset.arrayId);

                clustering_list_json.value = JSON.stringify(clustering_list);

                var labelHint = document.getElementById('labelHint_' + params);
                labelHint.style.display = (clustering_list.length === 0) ? 'block' : 'none';
            };

            // The label with a hint
            var labelHint = document.createElement('label');
            labelHint.id = 'labelHint_' + cluster_params[k][0];
            labelHint.style.fontStyle = 'italic';
            labelHint.innerText = 'If the list is empty, clusterization is conducted through all features.';

            // The div for holding the chosen features list
            var clustering_elements = document.createElement('div');
            clustering_elements.id = 'clustering_elements_' + cluster_params[k][0];

            // The '+' button
            var inputElement = document.createElement('input');
            inputElement.id = 'button_plus_' + cluster_params[k][0];
            inputElement.type = 'button';
            inputElement.value = '+';
            inputElement.classList.add('button');
            inputElement.classList.add('small');
            inputElement.style.margin = '0px';
            inputElement.style.cssFloat = 'right';
            inputElement.dataset.params = cluster_params[k][0];

            //this.cluster_params = cluster_params;

            // '+' onclick
            inputElement.onclick = function () {
                var selectbox = document.getElementById('clusteringSelectBox_' + this.dataset.params);

                // If nothing selected then return
                if (selectbox.selectedIndex === -1) return;

                var c_elements = document.getElementById('clustering_elements_' + this.dataset.params),
                    c_elementN = document.createElement('div');

                // Fill the variable to remember the id
                c_elementN.id = 'clusteringElement' + selectbox.selectedIndex;
                c_elementN.dataset.arrayId = selectbox.options[selectbox.selectedIndex].text;

                // The name of the feature
                var selectedLabel = document.createElement('label');
                selectedLabel.innerText = selectbox.options[selectbox.selectedIndex].text;
                selectedLabel.classList.add('selectedLabel');

                // The '-' button
                var deleteBtn = document.createElement('input');
                deleteBtn.dataset.selectedId = selectbox.selectedIndex;
                deleteBtn.type = 'button';
                deleteBtn.value = '-';
                deleteBtn.classList.add('button');
                deleteBtn.classList.add('small');
                deleteBtn.style.cssFloat = 'right';
                deleteBtn.style.margin = '0px';
                deleteBtn.dataset.params = this.dataset.params;

                // '-' onclick
                // Takes the id of the feature, deletes its 'c_elementN' and enables in the SelectBox
                deleteBtn.onclick = function (k) {
                    var selectedId = this.dataset.selectedId,
                        clusteringSelectBox = document.getElementById('clusteringSelectBox_' + this.dataset.params);

                    removeElement('clusteringElement' + selectedId);

                    clusteringSelectBox.options[selectedId].disabled = false;

                    recalculate_json(this.dataset.params);
                };

                // Adding this stuff to divs
                c_elementN.appendChild(document.createElement('br'));

                c_elementN.appendChild(deleteBtn);
                c_elementN.appendChild(selectedLabel);
                c_elements.appendChild(c_elementN);

                // Initialize and recalculate
                selectbox.options[selectbox.selectedIndex].disabled = true;
                selectbox.options[selectbox.selectedIndex].selected = false;

                recalculate_json(this.dataset.params);
            };

            // Adding the stuff to divs
            cluster_div.appendChild(inputElement);
            cluster_div.appendChild(clustering_elements);
            cluster_div.appendChild(labelHint);

            element_div.appendChild(cluster_div);
        }

         // Div with 'use normalized dataset' input
        var use_normalized_div = document.createElement('div');

        // The checkbox
        var use_normalized_input = document.createElement('input');
        use_normalized_input.id = "normalized_checkbox";
        use_normalized_input.name = "use_normalized_dataset";
        use_normalized_input.type = 'checkbox';
        use_normalized_input.checked = false;
        use_normalized_div.appendChild(use_normalized_input);

        // The label with a hint
        var use_normalized_label = document.createElement('label');
        use_normalized_label.innerText = 'Use normalized dataset';
        use_normalized_label.for = 'normalized_checkbox';
        use_normalized_div.appendChild(use_normalized_label);

        element_div.appendChild(use_normalized_div);
        divElement.appendChild(element_div);

        //Make the right element visible
        if (curr_algorithm === undefined && k === 0) {
            element_div.style.display = 'block';
            select_element.element_div = element_div;
            select_element.validateFields = function () { return this.element_div.validateFields(); };
        }
            else if (curr_algorithm !== undefined && option_element.value === curr_algorithm) {
                option_element.selected = true;
                element_div.style.display = 'block';
                select_element.element_div = element_div;
                select_element.validateFields = function () { return this.element_div.validateFields(); };

                let current_id = "features_"+curr_algorithm,
                    plus = document.getElementById("button_plus_"+curr_algorithm);

                for(let y=0; y<curr_values[current_id].length; y++){
                    document.getElementById("option_"+curr_values[current_id][y] + "_" + curr_algorithm).selected = true;
                    plus.click();
                }
            } else
                element_div.style.display = 'none';
    }

    select_element.elements = elements;

    // Switch the contents depending on what algorithm is selected
	select_element.onchange = function() {
        for( var i = 0; i < this.elements.length; i++ ){
            this.elements[i].style.display = 'none';
        }
        this.elements[this.selectedIndex].style.display = 'block';

        recalculate_json(this.selectedOptions[0].label);
        select_element.element_div = this.elements[this.selectedIndex];
    };

    // Fields validation before sending to the server
    if (formElement.validateElements === undefined)
        formElement.validateElements = [select_element];
    else
        formElement.validateElements.push(select_element);

    formElement.addEventListener('submit', function (ev) {
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
    table.classList.add("table", "table-sm", "table-hover", "display","compact");

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
    table.classList.add("table", "table-sm", "table-hover", "display","compact");

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
        "deferRender": true,
        "scrollY":        "300px",
        "scrollX":        true,
        "scrollCollapse": true,
        "fixedColumns":   {
            leftColumns: 1
        }});
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
    table.dataTableObj = $('#'+table.id).DataTable({
        scrollY:        "300px",
        scrollX:        true,
        scrollCollapse: true,
        paging:         true,
        fixedColumns:   {
            leftColumns: 1
        }
    });
    return table;
}

//Creates a basic GUI for a form
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
    table.classList.add("hover","display","compact");
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
    if (typeof color === 'undefined') return "#000000";
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

function cluster_selector(clusters_color_scheme, controls_parent, table_parent) {
    var selector = document.getElementById(controls_parent);
    
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
            var cluster_stat = document.getElementById(table_parent);
            while (cluster_stat.firstChild) {
                cluster_stat.removeChild(cluster_stat.firstChild);
            }
            var parent = document.getElementById(table_parent);
            var h3 = document.createElement("h3");
            h3.innerText = "Cluster №" + parseInt(event.target.innerText) + " statistics";
            h3.style.background = event.target.style.background;
            parent.appendChild(h3);
            printClusterStats(scene.realData, scene.clusters, parseInt(event.target.innerText), scene.dimNames, table_parent);
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

function collect_client_data(form) {
    /*
    Collecting data from client window:
    - visual parameters
    - dataset info
     */
    var visual_params = document.createElement('input');
    visual_params.name = 'visualparameters';
    visual_params.type = 'hidden';
    visual_params.value = JSON.stringify(scene.saveVisualParameters());
    var dataset_info = document.createElement('input');
    dataset_info.name = 'dataset_info';
    dataset_info.type = 'hidden';
    dataset_info.value = JSON.stringify(this.features_stat);
    form.appendChild(visual_params);
    form.appendChild(dataset_info);
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