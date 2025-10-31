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
    fetch('StreuobstGebiete.geojson')
        .then(response => response.json())
        .then(data => {
            // Data is now a GeoJSON object
            // You can use it to add a source and a layer
            addGeoJsonLayerGebiete(data);
        })
        .catch(error => console.error('Error loading GeoJSON:', error));

    fetch('trees.geojson')
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
    "Circled_dot_gray",
    "Tree_from_above",
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

function addGeoJsonLayerGebiete(geoJSONcontent) {
	// Add as source to the map
	map.addSource('gebiete', {
	    'type': 'geojson',
	    'data': geoJSONcontent
	});
	

  map.addLayer({
    "id":"gebiete-fill",
    "type":"fill",
    'source': 'gebiete',
    'layout': {
      "visibility":"visible"
    },
    'paint': {
      //'line-color': '#800',
      'fill-color': 'rgba(247, 179, 31, 1)',
      'fill-opacity': 0.2,
    },
    "minzoom": 5,
  });

  map.addLayer({
    "id":"gebiete-stroke",
    "type":"line",
    'source': 'gebiete',
    'layout': {
      "visibility":"visible"
    },
    'paint': {
      'line-color': 'rgba(188, 188, 188, 1)',
    },
    "minzoom": 5,
  });

  map.addLayer({
    "id":"gebiete-text",
    "type":"symbol",
    'source': 'gebiete',
    'layout': {
       "text-font":["Noto Sans Regular"],
       "text-size":14,
       "text-field":"{Name}",
      "text-allow-overlap": true,
       "visibility":"visible",
    },
    'paint': {
    	"text-color":"#82b",
    },
     "minzoom": 16,
  });
}

function addGeoJsonLayer(geoJSONcontent) {
	// Add as source to the map
	map.addSource('uploaded-source', {
	    'type': 'geojson',
	    'data': geoJSONcontent
	});
	

  map.addLayer({
    "id":"tree-size-circle",
    "type":"symbol",
    'source': 'uploaded-source',
    'layout': {
      "icon-image": "Tree_from_above",
      "icon-size": [
        "interpolate",
        ["exponential", 2],
        ["zoom"],
        14, ["*", 0.0325, ["max", ["coalesce", ["get", "circumference"], 1.0], 0.3]],
        19, ["*", 1, ["max", ["coalesce", ["get", "circumference"], 1.0], 0.3]],
        23, ["*", 16, ["max", ["coalesce", ["get", "circumference"], 1.0], 0.3]],
      ],
      "icon-anchor": "center",
      "icon-allow-overlap": true,
      "visibility":"visible"
    },
	  'paint': {
      "icon-opacity": 1,
    },
     "minzoom":10,
  });

	map.addLayer({
	    "id":"trees",
	    "type":"symbol",
	    'source': 'uploaded-source',
	    'layout': {
        "icon-image": ["coalesce", ["get", "_image"], "Circled_dot_gray"],
        "icon-size": [
          "interpolate",
	  ["exponential", 1.5],
	  ["zoom"],
          10, 0.5,
          20, 1.0,
        ],
	      "icon-allow-overlap": true,
        "visibility":"visible"
	    },
      "minzoom":3,
      //'filter': ["!", ['has', 'circumference']]
      //'filter': ["all", ['has', 'circumference'], ["==", "operator", "Obst- und Gartenbauverein Gerbrunn"]]
      'filter': ["all", ['has', '_image'], ["==", "operator", "Obst- und Gartenbauverein Gerbrunn"]]
	});

	map.addLayer({
	    "id":"trees-text",
	    "type":"symbol",
	    'source': 'uploaded-source',
	    'layout': {
        "text-font":["Noto Sans Regular"],
        "text-size":14,
        "text-field":["coalesce", ["get", "taxon:cultivar"], ["get", "_display_name"]],
        "text-offset": [
          0,
          1.6 
          //0
        ],
	      "text-allow-overlap": true,
        "visibility":"visible",
	    },
	    'paint': {
	    	"text-color":"#111",
	    },
      "minzoom":17,
      'filter': ["==", "operator", "Obst- und Gartenbauverein Gerbrunn"]
	});

	map.addLayer({
	    "id":"trees-text-start-date",
	    "type":"symbol",
	    'source': 'uploaded-source',
	    'layout': {
        "text-font":["Noto Sans Regular"],
        "text-size":14,
        "text-field": ["get", "start_date"],
        "text-offset": [
          0,
          3.0 
          //0
        ],
	      "text-allow-overlap": true,
        "visibility":"visible",
	    },
	    'paint': {
	    	"text-color":"#811",
	    },
      "minzoom":18,
      'filter': ["all", ["==", "operator", "Obst- und Gartenbauverein Gerbrunn"], ["has", "start_date"]]
	});

}

// Add geolocate control to the map.
map.addControl(
    new maplibregl.GeolocateControl({
        positionOptions: {
            enableHighAccuracy: true
        },
        trackUserLocation: true
    })
);
map.addControl(new maplibregl.FullscreenControl());

let nav = new maplibregl.NavigationControl();
map.addControl(nav, 'top-right');


map.on('click', 'trees', function(e) {
    // e.features contains all features at the click location
    if (e.features.length > 0) {
        const feature = e.features[0];
        // Build HTML for popup from feature properties
        let html = '<h3>' + (feature.properties['_display_name'] || 'Baum') + '</h3>';
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
