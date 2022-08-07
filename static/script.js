const wlansDiv = document.querySelector('div.wlan');
const numWlans = document.querySelector('span#num-wlans');
const wlansTable = document.querySelector('table.wlan-table tbody');

const probingDiv = document.querySelector('div.probing');
const numProbing = document.querySelector('span#num-probing');
const probingTable = document.querySelector('table.probing-table tbody');

const startSpan = document.querySelector('span#start');
const stopSpan = document.querySelector('span#stop');

let i = 0;
let myInterval;
let isRunning = false

startSpan.addEventListener('click', start);
stopSpan.addEventListener('click', stop);
// window.addEventListener('load', start, console.log('started'));

async function start() {
    // Don't want to use setInterval because server response
    // time won't be exact and this could lead to duplicate
    // GET requests which could eventually crash the server
    isRunning = true;
    while (isRunning) {
        await timeout(1000);
        console.log('Sending GET...');
        await getUpdateFromFlask().then((data) => {
            console.log('Status: ', data[0]);
            if (data[0] === 200) {
                console.log('Got 200 and data back');
                console.log(data[1]);
                createTables(data[1]);
            }
            else if (data[1] !== 200) {
                console.log('Got other than 200 response');
                isRunning = false;
            }
        })
        await timeout(2000);
    }

    // let data = await getFakeWLANData();
    // createTables(data);

}

function stop() {
    console.log('Stopped');
    isRunning = false;
}

async function getUpdateFromFlask() {
    let response = await fetch('/update');
    // let response = await fetch('https://api.chucknorris.io/jokes/random');
    let status = response.status;
    let data = await response.json()
    return [status, data];
}

function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getFakeWLANData() {
    // Server needs to send only arrays - no tuples
    let response = [
        { // found wlans
            'f0:72:ea:43:08:5a': {
                'assoc_clients': [
                    ['1c:f2:9a:6d:86:e6', 'Google_6d:86:e6', 51.0, '2437'],
                    ['1c:f2:9a:6d:86:e6', 'Google_6d:86:e6', 63.0, '2437']
                ]
            },
            'e8:91:20:f7:b3:c9': {
                'assoc_clients': [
                    ['e8:91:20:f7:b3:c8', 'Motorola_f7:b3:c8', 57.0, '2447']
                ]
            },
            // '2c:58:4f:ba:61:dd': {
            //     'assoc_clients': [
            //         ['2c:58:4f:ba:61:df', 'ARRISGro_ba:61:df', 71.5, '5745']
            //     ]
            // },
            // '60:38:e0:b8:49:8a': {
            //     'assoc_clients': [
            //         ['30:e3:7a:c2:a0:3d', 'IntelCor_c2:a0:3d', 40.0, '5180']
            //     ]
            // },
            // 'f0:72:ea:43:08:55': {
            //     'assoc_clients': [
            //         ['1c:f2:9a:6d:86:e6', 'Google_6d:86:e6', 51.0, '2437'],
            //         ['1c:f2:9a:6d:86:e6', 'Google_6d:86:e6', 63.0, '2437']
            //     ]
            // },
        },
        [ // currently associated clients
            ['1c:f2:9a:6d:86:e6', 'Google_6d:86:e6', 63.0, '2437'],
            ['e8:91:20:f7:b3:c8', 'Motorola_f7:b3:c8', 57.0, '2447'],
            ['30:e3:7a:c2:a0:3d', 'IntelCor_c2:a0:3d', 40.0, '5180'],
            ['2c:58:4f:ba:61:df', 'ARRISGro_ba:61:df', 71.5, '5745'],
            ['1c:f2:9a:6d:86:e6', 'Google_6d:86:e6', 51.0, '2437']
        ],
        [ // currently probing clients
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 45.0, '2422'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 51.0, '2437'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 38.0, '2417'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 36.0, '2417'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 40.0, '2417'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 51.0, '2437'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 38.0, '2417'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 36.0, '2417'],
            ['b8:27:eb:17:e6:f0', 'Raspberr_17:e6:f0', 46.0, '2427']
        ]
    ]

    return response;
}


function createTables(data) {
    let wlans = data[0];
    let wlansCount = Object.keys(wlans).length;
    let probing = data[2]

    // Make sure new wlans data has networks first
    // Otherwise keep existing table loaded
    if (wlansCount >= 1 && isRunning) {
        numWlans.innerHTML = wlansCount;
        wlansTable.querySelectorAll('td').forEach(td => td.remove());

        Object.entries(wlans).forEach((wlan, i) => {
            let bssid = wlan[0];
            let clients = wlan[1]['assoc_clients'];

            clients.forEach(client => {
                console.log(client);
                let row = document.createElement('tr');
                row.innerHTML = `
                    <td>${bssid}</td>
                    <td>${client[0]}</td>
                    <td>${client[1]}</td>
                    <td>-${client[2]} dBm</td>
                    <td>${client[3]} MHz</td>
                    `
                // Even rows should get zebra striping
                if (i % 2 === 0) { row.classList.add('grey-row') }
                wlansTable.append(row);
            })

        });
    }

    // Make sure new probing data has clients first
    // Otherwise keep existing table loaded
    if (probing.length >= 1 && isRunning) {
        numProbing.innerHTML = probing.length;
        probingTable.querySelectorAll('td').forEach(td => td.remove());

        probing.forEach((probe, i) => {
            let row = document.createElement('tr');
            row.innerHTML = `
                <td>${probe[0]}</td>
                <td>${probe[1]}</td>
                <td>-${probe[2]} dBm</td>
                <td>${probe[3]} MHz</td>
                `
            // Even rows here (odd rows in table) should get zebra striping
            if (i % 2 === 0) { row.classList.add('grey-row') }
            probingTable.append(row);
        })
    }

}