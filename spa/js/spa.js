function handleFileSelect(evt) {
    evt.stopPropagation();
    evt.preventDefault();

    var files = (evt.type === "change")? evt.target.files: evt.dataTransfer.files; // FileList object.
	
    // files is a FileList of File objects. List some properties.
    var output = [];
    for (var i = 0, f; f = files[i]; i++) {
      output.push('<li><strong>', escape(f.name), '</strong> (', f.type || 'n/a', ') - ',
                  f.size, ' bytes, last modified: ',
                  f.lastModifiedDate ? f.lastModifiedDate.toLocaleDateString() : 'n/a',
                  '</li>');
		
		Papa.parse(f, {
			worker: true,
			skipEmptyLines: true,
			complete: function(results) {
				//console.log(results);
				theData._papa_raw = results;	
				//console.log(theData);	  
				theData._dimNames = theData._papa_raw.data[0].filter((x, i)=> i > 0);
				theData._realData = theData._papa_raw.data.
										filter((x, i)=> i > 0).
										map((x)=>[x[0], x.filter((x, i)=> i > 0)]);
										
				theData._coord = new ParallelCoordinates("ParallelCoordinatesGraph",
                    theData._dimNames,
                    theData._realData,
                    [],
                    [],
                    null,
                    null);
			}
		});
		
    }
    document.getElementById('list').innerHTML = '<ul>' + output.join('') + '</ul>';
}

function handleDragOver(evt) {
	evt.stopPropagation();
	evt.preventDefault();
	evt.dataTransfer.dropEffect = 'copy'; // Explicitly show this is a copy.
}