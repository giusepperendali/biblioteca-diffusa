// mappa.js — Inizializzazione della mappa dei libri (Leaflet).
// I dati dei marcatori (variabile MARCATORI) sono generati lato server dal
// Controller e inseriti nella pagina dal template mappa.html: questo script
// si limita a disegnare la mappa e i segnaposto con i relativi fumetti.

// Mappa centrata sull'Italia
var mappa = L.map("mappa").setView([42.5, 12.5], 6);

// Sfondo cartografico OpenStreetMap (attribuzione richiesta dalla licenza)
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(mappa);

// I titoli/autori sono inseriti dagli utenti: prima di comporre l'HTML del
// fumetto vanno resi inerti per evitare l'iniezione di codice (XSS).
function testoSicuro(testo) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(testo));
    return div.innerHTML;
}

// Immagini del segnaposto predefinito di Leaflet (pin blu + ombra)
var IMMAGINI_LEAFLET = "https://unpkg.com/leaflet@1.9.4/dist/images/";

// Un segnaposto per ogni citta': il pin blu classico di Leaflet con un
// numerino (contatore dei libri) agganciato in alto a destra, ricostruito
// con L.divIcon da HTML/CSS (stili .segnaposto-* in style.css).
// Il click apre il fumetto con l'elenco dei libri della citta' (il nome
// della citta' e' gia' leggibile sullo sfondo cartografico e nel fumetto).
MARCATORI.forEach(function (punto) {
    var righe = punto.libri.map(function (libro) {
        var stato = libro.disponibile
            ? '<span class="badge bg-success">Disponibile</span>'
            : '<span class="badge bg-secondary">Non disponibile</span>';
        // Utente autenticato: il titolo porta alla scheda del libro.
        // Utente anonimo: il titolo apre la finestra "Accedi o registrati"
        // (modal Bootstrap definita in mappa.html).
        var titolo = UTENTE_AUTENTICATO
            ? "<a href='/libri/" + libro.id + "'>" + testoSicuro(libro.titolo) + "</a>"
            : "<a href='#' data-bs-toggle='modal' data-bs-target='#modalAccesso'>" +
              testoSicuro(libro.titolo) + "</a>";
        // Privacy: per gli utenti non autenticati il server non invia il
        // nome del proprietario (libro.proprietario assente)
        var proprietario = libro.proprietario
            ? " &middot; di " + testoSicuro(libro.proprietario)
            : "";
        return "<li class='mb-2'><strong>" + titolo + "</strong><br>" +
               testoSicuro(libro.autore) + proprietario + "<br>" + stato + "</li>";
    });

    var fumetto = "<div><strong>📍 " + testoSicuro(punto.citta) + " (" +
                  punto.libri.length + ")</strong>" +
                  "<ul class='list-unstyled mb-0 mt-2'>" + righe.join("") + "</ul></div>";

    var icona = L.divIcon({
        className: "",                       // niente stile predefinito di Leaflet
        html: '<div class="segnaposto">' +
              '<img class="segnaposto-ombra" src="' + IMMAGINI_LEAFLET + 'marker-shadow.png" alt="">' +
              '<img src="' + IMMAGINI_LEAFLET + 'marker-icon.png" alt="">' +
              '<span class="segnaposto-conteggio">' + punto.libri.length + "</span>" +
              "</div>",
        iconSize: [25, 41],                  // dimensioni del pin predefinito
        iconAnchor: [12, 41],                // punta del pin sulla posizione
        popupAnchor: [1, -34]                // fumetto sopra il pin
    });

    L.marker([punto.lat, punto.lon], { icon: icona })
        .addTo(mappa)
        .bindPopup(fumetto);
});
