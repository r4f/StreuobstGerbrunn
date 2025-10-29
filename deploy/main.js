const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/bright',
  center: [10.0, 49.78],
  zoom: 14.5,
  maxBounds: [
    [9.972,49.768],
    [10.04,49.794],
  ],
  pitch: 0, // Sets the initial view to be straight down
  maxPitch: 0, // Prevents the user from changing the pitch
  bearing: 0,
})
map.dragRotate.disable();
map.touchZoomRotate.disableRotation();
map.keyboard.disableRotation();

function createSvgString(width) {
  return `<svg width="${width}" height="80" viewBox="0 0 ${width} 80" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="${width}" height="80" fill="#1D8348" stroke="#1D8348" />
  </svg>`;
}

for (let i = 1; i <= 10; i++) {
  const rectWidth = i * 10;
  // Create an Image object from the SVG string
  const svgString = createSvgString(rectWidth);
  const img = new Image(rectWidth, 100);
  img.onload = () => map.addImage(`trunk${rectWidth}`, img);
  img.src = 'data:image/svg+xml;base64,' + btoa(svgString);
}

map.on('load', () => {
    // Use fetch() to get the local GeoJSON file
    fetch('trees.geojson') // Replace with your file name
        .then(response => response.json())
        .then(data => {
            // Data is now a GeoJSON object
            // You can use it to add a source and a layer
            addGeoJsonLayer(data);
        })
        .catch(error => console.error('Error loading GeoJSON:', error));
});

fruit_images = [
    "apple",
    "cherry",
    "pear",
    "plum",
    "walnut",
    "peach",
    "quince",
    "fig",
    "Circled_dot",
]
for (const fruit of fruit_images) {
  fetch(`images/${fruit}.svg`)
  .then(response => response.text())
  .then(svgText => {
    // Convert SVG text to an image object
    const svg = new Blob([svgText], {type: 'image/svg+xml'});
    const url = URL.createObjectURL(svg);
    const img = new Image();
    img.onload = function() {
    	map.addImage(fruit, img);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  });
}


function addGeoJsonLayer(geoJSONcontent) {
	// Add as source to the map
	map.addSource('uploaded-source', {
	    'type': 'geojson',
	    'data': geoJSONcontent
	});
	
	map.addLayer({
	    "id":"tree-size",
	    "type":"symbol",
	    'source': 'uploaded-source',
	    'layout': {
	       	"icon-image": [
		    "step",
	       	    ["get", "circumference"],
		    "trunk10",
		    0.10, "trunk20",
		    0.20, "trunk30",
		    0.30, "trunk40",
		    0.40, "trunk50",
		    0.50, "trunk60",
		    0.60, "trunk70",
		    0.70, "trunk80",
		    0.80, "trunk90",
		    0.90, "trunk100",
		],
	       	"icon-anchor": "center",
	       	//"icon-size": {"base": 1, "stops": [[3, 0.7], [10, 1.0], [20, 1.2]]},
           	"icon-size": {"base": 1, "stops": [[18, 0.3], [20, 0.4]]},
	//"icon-size": 0.2,
	       	  //[["get", "circumference"], 1],
	       	  //"max",
	       	  //0.5,
	       	  //["get", "circumference"],
	       	//],
	       	"icon-allow-overlap": true,
	       	"visibility":"visible"
	    },
      "paint": {
        "icon-translate": [0, 30],
      },
      "minzoom":19,
      'filter': [
        "all",
        ['has', 'circumference'],
        ['==', '$type', 'Point']
      ]
	});

	map.addLayer({
	    "id":"trees",
	    "type":"symbol",
	    'source': 'uploaded-source',
	    'layout': {
        "icon-image": ["coalesce", ["get", "_image"], "Circled_dot"],
        "icon-size": {"base": 1, "stops": [[3, 0.3], [10, 0.6], [20, 1.0]]},
	      "icon-allow-overlap": true,
        "visibility":"visible"
	    },
      "minzoom":3,
	    'filter': ['==', '$type', 'Point']
	});

	map.addLayer({
	    "id":"trees-text",
	    "type":"symbol",
	    'source': 'uploaded-source',
	    'layout': {
        "text-font":["Noto Sans Regular"],
        "text-size":14,
        "text-field":"{_display_name}",
        "text-offset": [
          0,
          -2 
        ],
	      "text-allow-overlap": true,
        "visibility":"visible",
	    },
	    'paint': {
	    	"text-color":"#333",
	    },
      "minzoom":15,
	    'filter': ['==', '$type', 'Point']
	});
}

map.on('click', 'trees', function(e) {
    // e.features contains all features at the click location
    if (e.features.length > 0) {
        const feature = e.features[0];
        // Build HTML for popup from feature properties
        let html = '<h3>' + (feature.properties['display_name'] || 'Baum') + '</h3>';
        html += '<ul>';
        for (const key in feature.properties) {
    	if ((key === 'display_name') || (key === 'class')) {
    		continue
    	}
            html += `<li><b>${key}</b>: ${feature.properties[key]}</li>`;
        }
        html += '</ul>';
        // Show popup at clicked location
        new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map);
    }
});
map.on('mouseenter', 'trees', function() {
    map.getCanvas().style.cursor = 'pointer';
});
map.on('mouseleave', 'trees', function() {
    map.getCanvas().style.cursor = '';
});
