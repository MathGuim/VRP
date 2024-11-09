async function getRoutes(locations, nVehicles) {

    locations["n_vehicles"] = nVehicles;

    return fetch("http://localhost:8000/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(locations),
    })
    .then(response => {
        const resp = response.json();
        return resp
    })
}

const locations = {coordinates: []}

const map = L.map("map").setView([-15.793889, -47.882778], 4);

const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
}).addTo(map);

const popup = L.popup()
    .setLatLng([-15.793889, -47.882778])
    .setContent("Selecione locais no mapa")
    .openOn(map);

function onMapClick(e) {

    locations.coordinates.push(e.latlng);

    let { lat, lng } = e.latlng;

    lat = lat.toFixed(2);
    lng = lng.toFixed(2);

    popup
        .setLatLng(e.latlng)
        .setContent(`Clique em ${lat}, ${lng}`)
        .openOn(map);

    let newMarker = new L.marker(e.latlng).addTo(map);
}

document.querySelector("#run").addEventListener("click", async (e) => {

    const nVehicles = document.getElementById("n-vehicles")

    let routes = await getRoutes(locations, nVehicles.value);

    const vehicleColors = {
        0: "red",
        1: "blue",
        2: "green",
        3: "purple",
        4: "yellow"
    };

    for (const vehicle in routes) {
        const route = routes[vehicle];
        if (route.length !== 0) {
            const path = L.polyline(route, {
                color: vehicleColors[vehicle]
            }).addTo(map);
            map.addLayer(path);
        }
    }

    locations.coordinates = []

})

map.on("click", onMapClick);

