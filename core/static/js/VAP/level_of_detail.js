/**
 * Created by Maria on 19.02.2019.
 */
function createLOD(id, activated, lod_value) {
            var top_element = document.getElementById(id);
            var input = document.createElement("input");
            input.type = "checkbox";
            input.setAttribute("name", "activated");
            input.classList.add("lod_activation");
            input.setAttribute("id", "lod_activation_" + id);

            var label = document.createElement("label");
            label.innerText = "Activate Level-of-Detail Generator for large data samples";

            var div = document.createElement("div");
            div.style.display = "none";

            var div_label = document.createElement("label");
            div_label.innerText = "Level-of-Detail";

            var div_grid = document.createElement("div");
            div_grid.classList.add("grid-x")
            div_grid.classList.add("grid-margin-x");
            var div_cell_slider = document.createElement("div");
            div_cell_slider.classList.add("cell");
            div_cell_slider.classList.add("small-2");
            var slider = document.createElement("input");
            slider.type = "range";
            slider.setAttribute("min", "1");
            slider.setAttribute("max", "1000");
            slider.setAttribute("step", "10");
            slider.setAttribute("id", "lod_slider_" + id);
            div_cell_slider.appendChild(slider);

            var div_cell_value = document.createElement("div");
            div_cell_value.classList.add("cell");
            div_cell_value.classList.add("small-2");
            var slider_value = document.createElement("input");
            slider_value.type = "number";
            slider_value.setAttribute("name", "lod_value");
            slider_value.setAttribute("id", "sliderOutput_" + id);
            div_cell_value.appendChild(slider_value);

            div_grid.appendChild(div_cell_slider);
            div_grid.appendChild(div_cell_value);

            div.appendChild(div_label);
            div.appendChild(div_grid);

            top_element.appendChild(input);
            top_element.appendChild(label);
            top_element.appendChild(div);

            if (slider_value && input) {
                slider_value.value = slider.value;
                    slider.addEventListener("change", function(event) {
                        slider_value.value = event.srcElement.value;
                    });
                    slider_value.addEventListener("change", function(event) {
                        slider.value = event.srcElement.value;
                    });
                input.addEventListener( "click", function(event) {
                    if (event.srcElement.checked) {
                        if (div.style.display == 'none') {
                            div.style.display = 'block';
                        }
                    } else {
                        div.style.display = 'none';
                    }
                });
            }

            if (activated == true) {
                input.checked = true;
                div.style.display = 'block';
                slider.value = lod_value;
                slider_value.value = lod_value;
            }
        }