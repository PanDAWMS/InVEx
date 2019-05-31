/**
 * Created by maria on 24/03/2019.
 */

class DatasetStats {

    constructor(dsID, num_records, index_name, features, lod_activated, lod_value, lod_mode) {
        this.dsID = dsID;
        this.num_records = num_records;
        this.index_name = index_name;
        this.features = features;
        this.lod_activated = lod_activated;
        this.lod_mode = lod_mode;
        this.lod_value =  lod_value;
        this.MEASURES = [{'type':'ratio','columns':["feature_name","feature_type","measure_type","min","mean","max","std","percentage_missing"]},
                         {'type':'ordinal','columns':["feature_name","feature_type","measure_type","unique_number","percentage_missing","distribution"]},
                         {'type':'nominal','columns':["feature_name","feature_type","measure_type","unique_number","percentage_missing","distribution"]},
                         {'type':'interval','columns':["feature_name","feature_type","measure_type","unique_number","unique_values","percentage_missing"]},
                         {'type':'clustered','columns':["feature_name","feature_type","measure_type","unique_number","percentage_missing","unique_values"]}];
        this.lods = [{
            'mode': 'minibatch',
            'message': 'Set the number of clusters and select multiple features using "group" selector',
            'number_of_groups': 'user_defined'
          },
          {
            'mode': 'param',
            'message': 'Select single categorical feature for grouping using "group" selector',
            'number_of_groups': 'auto'
          }
        ];
    }

    set_lod_mode(mode) {
        this.lod_mode = mode;
    }

    get_lod_mode() {
        return this.lod_mode;
    }

    set_lod_value(value) {
        this.lod_value = value;
    }

    get_lod_value() {
        return this.lod_value;
    }

    activate_lod() {
        this.lod_activated = "true";
        // var lod_number = document.getElementById("id_lod_number");
        // lod_number.disabled = false;
        if (document.querySelector('[id^="lod_select_"]')) {
            var lod_selectors = document.querySelectorAll('[id^="lod_select_"]');
            for (var i = 0; i < lod_selectors.length; i++) {
                lod_selectors[i].disabled = false;
            }
        }
    }

    deactivate_lod() {
        this.lod_activated = "false";
        // var lod_number = document.getElementById("id_lod_number");
        // lod_number.disabled = true;
        if (document.querySelector('[id^="lod_select_"]')) {
            var lod_selectors = document.querySelectorAll('[id^="lod_select_"]');
            for (var i = 0; i < lod_selectors.length; i++) {
                if (lod_selectors[i].checked) {
                    lod_selectors[i].checked = false;
                    lod_selectors[i].features[lod_selectors[i].feature_id]["lod_enabled"] = "false";
                }
                lod_selectors[i].disabled = true;
            }
        }
    }

    //-----
    // Panel for choosing type of LoD. Currently it's minibatch and parameter.
    //-----
    LoDChecker(id) {
        var div = document.createElement("div");
        div.classList.add("form-group");
        div.id = id;
        div.style.display = "none";
        var label = document.createElement("label");
        label.htmlFor = "lod_checker";
        label.innerText = "Choose LoD Type:";
        var select = document.createElement("select");
        select.classList.add("form-control");
        select.id = "lod_checker";
        select.root = div;
        for (var i=0;i<this.lods.length;i++) {
            var option = document.createElement("option");
            option.id = this.lods[i]['mode'];
            option.innerText = this.lods[i]['mode'];
            select.appendChild(option);
        }
        select.lods = this.lods;
        select.value = this.lod_mode;

        var msg = this.LoDMessage();
        var groups_number = this.LoDGroupNumber();

        select.msg = msg;
        select.groups_number = groups_number;
        select.self = this;

        div.appendChild(label);
        div.appendChild(select);
        div.appendChild(msg);
        div.appendChild(groups_number);

        var selected = this.lods.filter(function(a){ return a.mode == select.value })[0];
        msg.innerHTML = selected['message'];
        if (selected['number_of_groups'] == 'user_defined') {
            groups_number.style.display = "block";
            groups_number.firstChild.value = this.lod_value;
        } else {
            groups_number.style.display = "none";
        }
        msg.style.display = "block";

        select.onchange = function(event) {
          var selected = event.target.lods.filter(function(a){ return a.mode == event.target.value })[0];
          event.target.self.set_lod_mode(selected['mode']);
          event.target.msg.innerHTML = selected['message'];
          if (selected['number_of_groups'] == 'user_defined') {
              event.target.groups_number.style.display = "block";
              event.target.groups_number.value = this.lod_value;
          } else {
              event.target.groups_number.style.display = "none";
          }
          event.target.msg.style.display = "block";
        };
        return div;
    }

    LoDMessage() {
        var msg = document.createElement("p");
        msg.style.display = "none";
        return msg;
    }

    LoDGroupNumber() {
        var div_number = document.createElement("div");
        div_number.classList.add("cell", "small-2");
        var number = document.createElement("input");
        number.type = "number";
        number.setAttribute("name", "lod_value");
        number.setAttribute("id", "id_lod_number");
        number.setAttribute("min", "2");
        number.setAttribute("max", "3000");
        number.dataset_info = this;
        div_number.appendChild(number);
        div_number.style.display = "none";
        number.addEventListener("change", function(event) {
            event.target.dataset_info.set_lod_value(event.target.value);
        });
        return div_number;
    }

    createLOD(id) {
        var top_element = document.getElementById(id);
        top_element.classList.add("grid-x", "grid-margin-x", "align-middle");

        var div_check = document.createElement("div");
        div_check.classList.add("cell", "small-4");
        var checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.setAttribute("name", "activated");
        checkbox.id = "id_lod_checkbox";
        checkbox.dataset_info = this;
        checkbox.lod_value = this.lod_value;
        checkbox.lod_mode = this.lod_mode;
        var label = document.createElement("label");
        label.innerText = "Activate Level-of-Detail Generator";
        label.title = "LoD is used for grouping of objects from large data samples";

        div_check.appendChild(checkbox);
        div_check.appendChild(label);
        var lod_checker = this.LoDChecker("lod_check_panel");
        checkbox.lod_checker = lod_checker;
        div_check.appendChild(lod_checker);

        top_element.appendChild(div_check);

        checkbox.addEventListener( "click", function(event) {
            if (event.target.checked) {
                event.target.dataset_info.activate_lod();
                event.target.dataset_info.set_lod_value(event.target.lod_value);
                event.target.dataset_info.set_lod_mode(event.target.lod_mode);
                event.target.lod_checker.style.display = "block";
            } else {
                event.target.dataset_info.deactivate_lod();
                event.target.lod_checker.style.display = "none";
            }
        });

        if (this.lod_activated === "true") {
            checkbox.checked = true;
            this.activate_lod();
            this.set_lod_value(this.lod_value);
            this.set_lod_mode(this.lod_mode);
            lod_checker.style.display = "block";
        } else {
            this.deactivate_lod();
            lod_checker.style.display = "none";
        }
        return top_element;
    }

    display_dataset_info() {
        var dataset_info = [{"row_name":"Dataset Name","value":this.dsID},
                            {"row_name":"Number of Records","value":this.num_records},
                            {"row_name":"Index","value":this.index_name}];

        var table = document.createElement("table");
        table.setAttribute("id","dataset_info");
        var thead = document.createElement("thead");
        var headers = document.createElement("tr");
        for (var i=0;i<dataset_info.length;i++) {
            var name = document.createElement("th");
            name.innerHTML = dataset_info[i]["row_name"];
            headers.appendChild(name);
        }
        thead.appendChild(headers);
        var tbody = document.createElement("tbody");
        var values = document.createElement("tr");
        for (var i=0;i<dataset_info.length;i++) {
            var value = document.createElement("td");
            value.innerHTML = dataset_info[i]["value"]
            values.appendChild(value);
        }
        tbody.appendChild(values);
        table.appendChild(thead);
        table.appendChild(tbody);
        return table;
    }

    generate_chart(distribution_data, title) {
        var domElement = document.createElement("div");
        domElement.id = "distr_" + title;
        var _labels = [];
        var _data = [];
        for (var k in distribution_data) {
            _labels.push(k.toString());
            _data.push(distribution_data[k]);
        }
        var data = [{x: _labels, y: _data, type: 'bar'}];
        var layout = {
           xaxis: { type: 'category' }
        };
        Plotly.newPlot(domElement, data, layout, {displayModeBar: false});
        return domElement;
    }

    values_frequency(item) {
        var table = document.createElement("table");
        table.setAttribute("id","frequency_"+item['feature_name']);

        if ('distribution' in item) {
            var distribution = item['distribution'];
            //return this.draw_bar_chart(item['feature_name'], distribution);
            for (var k in distribution) {
                var row = document.createElement("tr");
                var key = document.createElement("td");
                var value = document.createElement("td");

                key.innerHTML = k;
                value.innerHTML = distribution[k];

                row.appendChild(key);
                row.appendChild(value);
                table.append(row);
            }
            return table;
        } else {
            return this.draw_uniques_fieldset(item);
        }
    }

    _headers(type) {
        var thead = document.createElement("thead");

        var tr = document.createElement("tr");
        // empty column for +/-
        tr.appendChild(document.createElement("th"));

        var lod_selector = document.createElement("th");
        lod_selector.textContent = "group";
        lod_selector.title = "Select all (of the defined measure_type)";
        lod_selector.style.cursor = "pointer";
        lod_selector.addEventListener( "click", function() {
            if (document.getElementById("id_lod_checkbox").checked) {
                var lod_selectors = document.querySelectorAll('[id^="lod_select_' + type + '"]');
                for (var i = 0; i < lod_selectors.length; i++) {
                    if (!lod_selectors[i].checked) {
                        lod_selectors[i].checked = true;
                        lod_selectors[i].features[lod_selectors[i].feature_id]["lod_enabled"] = "true";
                    }
                }
            }
        });
        tr.appendChild(lod_selector);

        var selector = document.createElement("th");
        selector.textContent = "select";
        selector.title = "Select all (of the defined measure_type)";
        selector.style.cursor = "pointer";
        selector.addEventListener( "click", function() {
            var selectors = document.querySelectorAll('[id^="select_' + type + '"]');
            for (var i = 0; i < selectors.length; i++) {
                if (!selectors[i].checked) {
                    selectors[i].checked = true;
                    selectors[i].features[selectors[i].feature_id]["enabled"] = "true";
                }
            }
        });
        tr.appendChild(selector);

        var element = this.MEASURES.filter(function(e) {
          return (e['type'] === type);
        });
        element[0]['columns'].forEach(create_row);
        function create_row(value, index, array) {
            var th = document.createElement("th");
            th.textContent = value;
            // add none class to elements which should be displayed as detailed
            if (['distribution','unique_values'].includes(value))
                th.classList.add("none");
            tr.appendChild(th);
        }

        thead.appendChild(tr);
        return thead;
    }

    _rows(type) {

        var tbody = document.createElement("tbody");

        var element = this.MEASURES.filter(function(e) {
            return (e['type'] === type);
        });
        var columns = element[0]['columns'];

        for (var i=0;i<this.features.length;i++) {
            if (this.features[i]['measure_type'] === type) {
                var tr = document.createElement("tr");
                // empty column for +/-
                tr.appendChild(document.createElement("td"));
                tr.appendChild(this.print_lod_selector(i, type));
                tr.appendChild(this.print_selector(i, type));
                this.type_switch(type, this.features[i], tr, columns);
                tbody.appendChild(tr);
            }
        }
        return tbody;
    }

    type_switch(type, feature, tr, columns) {
        switch (type) {
            case 'nominal':
                for (var j=0;j<columns.length;j++) {
                    var td = document.createElement("td");
                    var name = columns[j];
                    if (feature[name] === undefined)
                        td.textContent = '';
                    else {
                        if (name == "distribution") {
                            if (feature["unique_number"] == 1)
                                td.appendChild(this.values_frequency(feature));
                            else
                               td.appendChild(this.generate_chart(feature["distribution"], name));
                        }
                        else if (this.isNumber(feature[name])) {
                            if (name == "percentage_missing")
                                td.textContent = this.formatNumber(feature[name].toFixed(2)) + "%";
                            else
                                td.textContent = feature[name];
                        }
                        else
                            td.textContent = feature[name];
                    }
                    tr.appendChild(td);
                }
                break;
            case 'ordinal':
                for (var j=0;j<columns.length;j++) {
                    var td = document.createElement("td");
                    var name = columns[j];
                    if (feature[name] === undefined)
                        td.textContent = '';
                    else {
                        if (name == "distribution") {
                            if (feature["unique_number"] == 1)
                                td.appendChild(this.values_frequency(feature));
                            else
                               td.appendChild(this.generate_chart(feature["distribution"], name));
                        }
                        else if (this.isNumber(feature[name])) {
                            if (name == "percentage_missing")
                                td.textContent = this.formatNumber(feature[name].toFixed(2)) + "%";
                            else
                                td.textContent = feature[name];
                        }
                        else
                            td.textContent = feature[name];
                    }
                    tr.appendChild(td);
                }
                break;
            case 'interval':
                for (var j=0;j<columns.length;j++) {
                    var td = document.createElement("td");
                    var name = columns[j];
                    if (feature[name] === undefined)
                        td.textContent = '';
                    else {
                        if (name == "unique_values")
                            td.appendChild(this.draw_uniques_fieldset(feature));
                        else if (this.isNumber(feature[name])) {
                            if (name == "percentage_missing")
                                td.textContent = this.formatNumber(feature[name].toFixed(2)) + "%";
                        }
                        else
                            td.textContent = feature[name];
                    }
                    tr.appendChild(td);
                }
                break;
            case 'clustered':
                for (var j=0;j<columns.length;j++) {
                    var td = document.createElement("td");
                    var name = columns[j];
                    if (feature[name] === undefined)
                        td.textContent = '';
                    else {
                        if (name == "unique_values")
                            td.appendChild(this.draw_uniques_fieldset(feature));
                        else
                            td.textContent = feature[name];
                    }
                    tr.appendChild(td);
                }
                break;
            case 'ratio':
                for (var j=0;j<columns.length;j++) {
                    var td = document.createElement("td");
                    var name = columns[j];
                    if (feature[name] === undefined)
                        td.textContent = '';
                    else {
                        if (["mean"].includes(name))
                            this.draw_slider(td, feature, name);
                        else {
                            var value = feature[name];
                            if (this.isNumber(value)) {
                                if (name == "percentage_missing")
                                    td.textContent = this.formatNumber(value.toFixed(2)) + "%";
                                else
                                    td.textContent = this.formatNumber(value.toFixed(2));
                            }
                            else td.textContent = value;
                        }
                    }
                    tr.appendChild(td);
                }
                break;
        }
    }

    available_measures() {
        var measures = [];
        for (var i=0;i<this.features.length;i++)
            measures.push(this.features[i]['measure_type'])
        return Array.from(new Set(measures));
    }

    display_features_panel(element_id) {
        var root = document.getElementById(element_id);

        root.appendChild(this.createLOD("lod"));
        root.appendChild(this.display_dataset_info());
        $("#dataset_info").DataTable({
            ordering: false,
            searching: false,
            paging: false,
            info: false
        });

        var available_measures = this.available_measures();
        for (var i=0;i<this.MEASURES.length;i++) {
            var type = this.MEASURES[i]['type'];
            if (available_measures.includes(type)) {
                var table = document.createElement("table");
                table.classList.add("display", "compact");
                table.setAttribute("id", "features_table_" + type);
                table.appendChild(this._headers(type));
                table.appendChild(this._rows(type));
                root.appendChild(table);
                $("#features_table_" + type).DataTable({
                    searching: false,
                    paging: false,
                    info: false,
                    responsive: {
                        details: {type: 'inline'}
                    },
                    columnDefs: [{
                        targets: [1, 2],
                        visible: true,
                        orderable: false
                    }]
                });
            }
        }

        var csrf = document.createElement('input');
        csrf.setAttribute("type","hidden");
        csrf.setAttribute("name","csrfmiddlewaretoken");
        var csrftoken = Cookies.get('csrftoken');
        csrf.setAttribute("value",csrftoken);
        root.appendChild(csrf);

        var button = document.createElement("input");
        button.classList.add("button", "small");
        button.setAttribute("id","visualize_btn");
        button.type = "button";
        button.value = "Visualize";
        button.dataset_info = this;
        button.onclick = function(event){

            var form = document.createElement('form');
            form.setAttribute('method', 'post');
            if(typeof visualize_url !== "undefined" )
                form.setAttribute('action', '');
            else
                form.setAttribute('action', visualize_url);
            form.style.display = 'hidden';

            var action = document.createElement("input");
            action.type = "hidden";
            action.name = "formt";
            action.value = "visualize";
            form.appendChild(action);

            var data = {
                dsID: event.target.dataset_info.dsID,
                csrfmiddlewaretoken: csrftoken,
                num_records: Number(event.target.dataset_info.num_records),
                features: JSON.stringify(event.target.dataset_info.features),
                index_name: event.target.dataset_info.index_name,
                lod_activated: event.target.dataset_info.lod_activated,
                lod_value: event.target.dataset_info.lod_value,
                lod_mode: event.target.dataset_info.lod_mode
            };

            for (var key in data ){
                var field = document.createElement("input");
                field.type ="hidden";
                field.name = key;
                field.value = data[key];
                form.appendChild(field);
            }
            document.body.appendChild(form);
            form.submit();
        };
        root.appendChild(button);

        var action = document.createElement("input");
        action.type = "hidden";
        action.name = "formt";
        action.value = "visualize";
        root.appendChild(action);
    }

    formatNumber(num) {
        return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
    }
    
    isNumber (value) {
        return typeof value === 'number' && isFinite(value);
    }
    
    draw_uniques_fieldset(item) {
        var fieldset = document.createElement("fieldset");
        fieldset.classList.add("fieldset");
        fieldset.setAttribute("id","fieldset_"+item["feature_name"]);
        for(var i=0; i<item['unique_values'].length; i++) {
            var div = document.createElement("div");
            var input = document.createElement("input");
            input.setAttribute("id","checkbox_"+item["unique_values"][i]);
            input.type="checkbox";
            input.checked=true;
            var label = document.createElement("label");
            label.setAttribute("for","checkbox_"+item["unique_values"][i]);
            label.innerHTML = item['unique_values'][i];
            div.appendChild(input);
            div.appendChild(label);
            fieldset.appendChild(div);
        }
        return fieldset;
    }
    
    draw_slider(td, item, q) {
        var slider = document.createElement("input");
        slider.type = "range";
        slider.setAttribute("min", item["min"]);
        slider.setAttribute("max", item["max"]);
        slider.value = item[q];
        slider.disabled = "true";
        var div = document.createElement("div");
        div.textContent = this.formatNumber(item[q].toFixed(2));
        div.style.marginLeft = "10px";
        td.appendChild(slider);
        td.appendChild(div);
    }
    
    print_selector(idx, type) {
        var td = document.createElement("td");
        var selector = document.createElement("input");
        selector.setAttribute("id", "select_" + type + "_" + idx);
        selector.setAttribute("type", "checkbox");
        selector.feature_id = idx;
        selector.features = this.features;
        selector.checked = (this.features[idx]["enabled"] === "true");
        selector.addEventListener("click", function(e) {
            e.target.features[e.target.feature_id]["enabled"] = (e.target.checked) ? "true" : "false";
        });
        td.appendChild(selector);
        return td;
    }

    print_lod_selector(idx, type) {
        var td = document.createElement("td");
        var selector = document.createElement("input");
        selector.setAttribute("id", "lod_select_" + type + "_" + idx);
        selector.setAttribute("type", "checkbox");
        selector.feature_id = idx;
        selector.features = this.features;
        selector.checked = (this.features[idx]["lod_enabled"] === "true");
        selector.disabled = (this.lod_activated === "false");
        selector.addEventListener("click", function(e) {
            e.target.features[e.target.feature_id]["lod_enabled"] = (e.target.checked) ? "true" : "false";
        });
        td.appendChild(selector);
        return td;
    }

}