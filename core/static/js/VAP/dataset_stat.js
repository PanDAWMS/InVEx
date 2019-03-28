/**
 * Created by maria on 24/03/2019.
 */

class DatasetStats {
    
    constructor(ds_id,ds_name,filepath,num_records,index_name,features) {
        this.ds_id = ds_id;
        this.ds_name = ds_name;
        this.filepath = filepath;
        this.num_records = num_records;
        this.index_name = index_name;
        this.features = features;
        this.MEASURES = [{'type':'ratio','columns':["feature_name","feature_type","min","mean","max","std","percentage_missing"]},
                         {'type':'ordinal','columns':["feature_name","feature_type","unique_number","percentage_missing","distribution"]},
                         {'type':'nominal','columns':["feature_name","unique_number","percentage_missing","distribution"]},
                         {'type':'interval','columns':["feature_name","unique_values","percentage_missing"]},
                         {'type':'clustered','columns':["feature_name","percentage_missing","unique_values"]}];
    }

    display_dataset_info() {
        var dataset_info = [{"row_name":"Dataset Name","value":this.ds_name},
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

    values_frequency(item) {
        var table = document.createElement("table");
        table.setAttribute("id","frequency_"+item['feature_name']);
        if ('distribution' in item) {
            var distribution = item['distribution'];
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


    measure_headers(type) {

        var thead = document.createElement("thead");
        var tr = document.createElement("tr");
        var selector = document.createElement("th");
        selector.textContent = "select";
        tr.appendChild(selector);
        var element = this.MEASURES.filter(function(e) {
          return e['type'] == type;
        });
        element[0]['columns'].forEach(create_row);
        function create_row(value, index, array) {
            var th = document.createElement("th");
            th.textContent = value;
            if (['distribution','unique_values'].includes(value))
                th.classList.add("none");
            tr.appendChild(th);
        }
        thead.appendChild(tr);
        return thead;
    }

    measure_values(type) {

        var tbody = document.createElement("tbody");

        var element = this.MEASURES.filter(function(e) {
          return e['type'] == type;
        });
        var columns = element[0]['columns'];

        for (var i=0;i<this.features.length;i++) {
            if (this.features[i]['measure_type'] == type) {
                var tr = document.createElement("tr");
                tr.appendChild(this.print_selector(i));
                this.type_switch(type, this.features[i], tbody, tr, columns);
                tbody.appendChild(tr);
            }
        }
        return tbody;
    }

    type_switch(type, feature, tbody, tr, columns) {
        switch (type) {
            case 'nominal':
                for (var j=0;j<columns.length;j++) {
                    var td = document.createElement("td");
                    var name = columns[j];
                    if (feature[name] === undefined)
                        td.textContent = '';
                    else {
                        if (name == "distribution")
                            td.appendChild(this.values_frequency(feature));
                        else if (this.isNumber(feature[name])) {
                            if (name == "percentage_missing")
                                td.textContent = this.formatNumber(feature[name].toFixed()) + "%";
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
                        if (name == "distribution")
                            td.appendChild(this.values_frequency(feature));
                        else if (this.isNumber(feature[name])) {
                            if (name == "percentage_missing")
                                td.textContent = this.formatNumber(feature[name].toFixed()) + "%";
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
                                td.textContent = this.formatNumber(feature[name].toFixed()) + "%";
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
                                    td.textContent = this.formatNumber(value.toFixed()) + "%";
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

        root.appendChild(this.display_dataset_info());

        $("#dataset_info").DataTable({searching: false, paging: false, info: false});

        var available_measures = this.available_measures();

        for (var i=0;i<this.MEASURES.length;i++) {
            var type = this.MEASURES[i]['type'];
            if (available_measures.includes(type)) {
                var table = document.createElement("table");
                table.classList.add("display","compact");
                table.setAttribute("id", "features_table_" + type);
                table.style.width = "100%";
                table.appendChild(this.measure_headers(type));
                table.appendChild(this.measure_values(type));
                root.append(table);
                $('#features_table_' + type).DataTable({searching: false,
                                                        paging: false,
                                                        info: false,
                                                        responsive: true

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
        button.classList.add("button","small");
        button.setAttribute("id","visualize_btn");
        button.type = "button";
        button.value = "Visualize";
        button.dataset_info = this;
        button.onclick = function(event){

            var form = document.createElement('form');
            form.setAttribute('method', 'post');
            form.setAttribute('action', '');
            form.style.display = 'hidden';

            var action = document.createElement("input");
            action.type = "hidden";
            action.name = "formt";
            action.value = "visualize";
            form.appendChild(action);

            var data = {
                ds_id: event.target.dataset_info.ds_id,
                ds_name: event.target.dataset_info.ds_name,
                filepath: event.target.dataset_info.filepath,
                csrfmiddlewaretoken: csrftoken,
                num_records: event.target.dataset_info.num_records,
                features: JSON.stringify(event.target.dataset_info.features),
                index_name: event.target.dataset_info.index_name
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
        var span = document.createElement("span");
        span.textContent = this.formatNumber(item[q].toFixed(2));
        span.style.marginLeft = "10px";
        td.appendChild(slider);
        td.appendChild(span);
    }

    
    print_selector(idx) {
        var td = document.createElement("td");
        var selector = document.createElement("input");
        selector.setAttribute("id","select_"+idx);
        selector.feature_id = idx;
        selector.features = this.features;
        selector.setAttribute("type","checkbox");
        if (this.features[idx]['enabled'] == 'true')
            selector.checked = true;
        else selector.checked = false;
        selector.addEventListener("click", function(event) {
            var idx = event.target.feature_id;
            if (event.target.checked)
                event.target.features[idx]['enabled'] = 'true';
            else
                event.target.features[idx]['enabled'] = 'false';
        });
        td.appendChild(selector);
        return td;
    }


}