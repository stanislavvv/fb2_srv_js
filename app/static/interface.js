// navigation links text
const linkTexts = {
    'start': 'HOME',
    'self': 'RELOAD',
    'up': 'UP',
    'next': 'NEXT',
    'prev': 'PREV'
};

function updateNavigationPath(path) {
    window.history.pushState(null, '', `#${path}`);
}

function fetchOPDSData(url) {
    let xmlHttp = new XMLHttpRequest();

    // Ensure URL starts with a slash
    url = url.replace(/^(\/*)/g, '');

    xmlHttp.open("GET", `/${url}`, true);

    xmlHttp.onload = function() {
        if(xmlHttp.status === 200) {
            parseAndRenderXML(xmlHttp.responseXML);
            updateNavigationPath(`/${url}`);  // Update navigation path with the fetched URL
        } else {
            alert('Failed to fetch OPDS data');
        }
    };
    xmlHttp.send();
}

function navigateLink(link) {
    fetchOPDSData(link);  // Fetch new data and update history
}

function parseAndRenderXML(xmlDoc) {
    // title from opds
    let titleElement = xmlDoc.getElementsByTagName("title")[0];
    const titleText = titleElement.textContent;
    document.querySelectorAll("#title").forEach(elem => {
        elem.textContent = titleText;
    });

    // navigation from opds
    let navigationSection = document.getElementById('navigation-section');
    navigationSection.innerHTML = '';
    Array.from(xmlDoc.getElementsByTagName("link")).forEach(link => {
        if ((link.parentNode.tagName !== "entry") && 
            (link.getAttribute('rel') !== "search")) {
            let a = document.createElement("a");
            a.href = '#' + link.getAttribute('href');
            const relValue = link.getAttribute('rel');
            a.textContent = linkTexts[relValue] || relValue || link.getAttribute('href');

            // Navigate using the new fetchOPDSData function with the hash path
            a.onclick = function () {
                navigateLink(link.getAttribute('href')); return false;
            };

            if (navigationSection.firstChild) {
                navigationSection.appendChild(document.createTextNode(" "));
            }
            navigationSection.appendChild(a);
        }
    });

    // search if in opds
    let searchLink = Array.from(xmlDoc.getElementsByTagName("link"))
                           .find(l => l.getAttribute('rel') === 'search');
    if (searchLink) {
        document.getElementById('search-section').style.display = '';
    } else {
        document.getElementById('search-section').style.display = 'none';
    }

    // entry rendering (simple list)
    let contentSection = document.getElementById('content');
    contentSection.classList.add('rowlist_single');
    contentSection.innerHTML = '';

    Array.from(xmlDoc.getElementsByTagName("entry")).forEach(entry => {
        let title = entry.getElementsByTagName("title")[0].textContent;
        let linkHref = '';
        Array.from(entry.getElementsByTagName("link")).forEach(link => {
            if ((link.getAttribute('type') === 'application/atom+xml;profile=opds-catalog' ||
                link.getAttribute('type').startsWith('application/atom')) &&
                link.getAttribute('rel') != 'search'
            ) {
                linkHref = link.getAttribute('href');
            }
        });

        let d = document.createElement("div");
        let a = document.createElement("a");
        d.classList.add('col1')
        a.href = '#' + linkHref;
        a.textContent = title;
        a.onclick = function () { navigateLink(linkHref); return false; };
        d.appendChild(a);
        contentSection.appendChild(d);
    });
}

function performSearch() {
    let searchTerm = document.getElementById('search-input').value;
    if (searchTerm.trim()) {
        window.location.href = '/opds/search?searchTerm=' + encodeURIComponent(searchTerm);
    } else {
        alert("Введите поисковой запрос");
    }
}

window.onload = function() {
    // Check the hash in the URL and fetch data for it

    let hashPath = window.location.hash.substring(1);  // Remove the leading '#'
    if (hashPath) {
        fetchOPDSData(hashPath);
    } else {
        fetchOPDSData('/opds/');  // Default fallback if no hash is present
    }
};

window.onpopstate = function(event) {
    let hashPath = window.location.hash.substring(1);  // Remove the leading '#'
    if (hashPath) {
        fetchOPDSData(hashPath);
    } else {
        fetchOPDSData('/opds/');  // Default fallback if no hash is present
    }
};
