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

function createClusterElements(divElement, formElement, cluster_params) {

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

    var elements = [];
    for ( var k = 0; k < cluster_params.length; k++ ) {
		var el = cluster_params[ k ];
        var option_element = document.createElement('option');
        option_element.innerText = el[ 1 ];
        option_element.value = el[ 0 ];
        select_element.appendChild(option_element);
        var element_div = document.createElement('div');
        elements.push(element_div);
        element_div.inputElements = [];
        for( var i = 2; i < el.length; i++ ) {
            var input = document.createElement("input");
            input.classList.add("form-control-sm");
            input.setAttribute("type", "text");
            for (var j = 0; j < el[i].attributes.length; j++ ) {
                input.setAttribute(el[ i ].attributes[ j ][ 0 ], el[ i ].attributes[ j ][ 1 ]);
            }
            input.id = 'inp'+("00000" + Math.random()*100000).slice(-5);
            input.setAttribute("name", el[ i ][ 'name' ]);
			if ('defvalue' in el[ i ]){
				input.value = el[ i ][ 'defvalue' ];
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
			if ('label' in el[ i ]){
                var label = document.createElement('label');
                label.setAttribute("for", input.id);
                label.textContent = el[ i ][ 'label' ];
                element_div.appendChild(label);
                input.labelText = el[ i ][ 'label' ];
            }
            element_div.inputElements.push(input);
            element_div.validateFields = function(){
                for( var i = 0; i < this.inputElements.length; i++ ){
                    if (!validate_field(this.inputElements[i]))
                        return false;
                }
                return true;
            }
            element_div.appendChild(input);
        }
        divElement.appendChild(element_div);
        if ( k == 0){
            element_div.style.display = 'block';
            select_element.element_div = element_div;
            select_element.validateFields = function(){return this.element_div.validateFields()};
        }
        else
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