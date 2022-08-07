from datetime import datetime
from time import sleep
import subprocess
import re

close_macs = []
is_active = True
capture_iface = 'wlan1'
min_dbm = 50

# # ----------Capturing specific frame types----------
# Want Data frames (Data and QoS-Data only) and Management frames (ProbeReqs only)
# subtype Data || subtype QoS-Data || subtype ProbeReq
# probe request are type 0 subtype 4
# data are type 2 subtype 0
# qos data are type 2 subtype 8

# # ----------Specifying specific fields----------
# # Got rid of: protocol, packet length, type (could not find field)
# frame.number
# frame.time
# wlan.bssid
# NEW wlan.bssid_resolved
# wlan.sa
# wlan.sa_resolved
# wlan.da
# wlan.da_resolved
# radiotap.dbm_antsignal (was old dbm1)
# wlan_radio.signal_dbm (was old dbm2)
# wlan.fc.type ()
# wlan.fc.subtype (0 is data, 4 is probe req, 8 is QoS data)

# -----tshark command-----
# sudo tshark -i wlan1 -f "subtype Data || subtype QoS-Data || subtype ProbeReq" 
#-T fields -e wlan.bssid -e frame.len


# def get_probe_reqs():
#     print(f'start get_probe_reqs() at {datetime.now()}')

#     # Capture probe requests only
#     probe_reqs = [
#         'sudo',
#         'tshark',
#         '-T',
#         'tabs',
#         '-i',
#         capture_iface,
#         '-a',
#         'duration:3',
#         'type',
#         'data',
#     ]

#     raw_probe_reqs = (subprocess.Popen(probe_reqs, stdout=subprocess.PIPE)
#         .communicate()[0])

#     raw_probe_reqs = (raw_probe_reqs.decode('utf-8') if type(raw_probe_reqs)
#         == bytes else raw_probe_reqs)

#     raw_probe_reqs = raw_probe_reqs.split('\n')
#     # print(raw_probe_reqs)

#     cleaned_frames = []
#     for frame in raw_probe_reqs[0:-1]:
#         split_frame = frame.split('\t')
#         split_frame[0] = split_frame[0].strip()
#         del split_frame[-1:]
#         cleaned_frames.append(split_frame)

#     # print(cleaned_frames)


def get_raw_frames():
    # print(f'start get_rawframes()) at {datetime.now()}')
    commands = [
        'sudo',
        'tshark',
        '-T',
        'tabs',
        '-i',
        capture_iface,
        '-a',
        'duration:5',  # 5 sec capture + 1 sec processing?
        '-Tfields',
        '-e', 
        'frame.number',
        '-e',
        'frame.time',
        '-e',
        'wlan.bssid',
        '-e',
        'wlan.bssid_resolved',
        '-e',
        'wlan.sa',
        '-e',
        'wlan.sa_resolved',
        '-e',
        'wlan.da',
        '-e',
        'wlan.da_resolved',
        '-e',
        'radiotap.dbm_antsignal',
        '-e',
        'wlan_radio.signal_dbm',
        '-e',
        'wlan.fc.type',
        '-e',
        'wlan.fc.subtype',
        '-e',
        'wlan_radio.frequency',
        '-f',
        'subtype Data || subtype QoS-Data || subtype ProbeReq',
    ]

    frames = subprocess.Popen(
        commands, stdout=subprocess.PIPE).communicate()[0]

    frames = (frames.decode('utf-8') if type(frames) == bytes
              else frames)

    return frames.split('\n')


def get_avg_dbm(frame):
    sig_dbms = []
    avg_dbm = None

    # Split and add first dBM value to list
    sig_dbms += ([dbm.strip().lower() for dbm in frame[8].split(',')
                  if dbm.strip().lower() != '0'])

    # Add second dBm value to list
    sig_dbms += ([dbm.strip().lower() for dbm in [frame[9]]
                  if dbm.strip().lower() != '0'])

    sig_dbms = list(set(sig_dbms))

    # Match the dBm value and the strip minus sign and convert to int
    sig_dbms = ([int((re.match('-[0-9]{1,3}', dbm)[0])[1:]) for dbm
                 in sig_dbms if re.match('-[0-9]{1,3}', dbm) != None])

    # Average all dBms
    try:
        avg_dbm = sum(sig_dbms) / len(sig_dbms)
    except ZeroDivisionError:
        avg_dbm = 0

    return avg_dbm


def clean_frames(frames):
    cleaned = []

    if frames[-1] == '':
        for frame in frames[0:-1]:
            split_frame = [f.strip() for f in frame.split('\t')]
            cleaned.append(split_frame)

    for frame in cleaned:
        frame[8] = get_avg_dbm(frame)
        del frame[9]
    return cleaned


def process_frames(frames):
    currently_assoc = []
    currently_probing = []

    # # Filter frames by min dBm
    # filtered = [frame for frame in frames if frame[8] <= min_dbm]
    # print('len filtered: ', len(filtered))
    # print(filtered)

    # Get unique BSSIDs and exclude broadcasts
    unique_bssids = list(
        set([frame[2] for frame in frames if frame[2] != 'ff:ff:ff:ff:ff:ff']))
    # print('unique bssids: ', unique_bssids)

    # Create wlans dict to update with associated clients next
    nearby_wlans = {frame: {'assoc_clients': []} for frame in unique_bssids}


    for frame in frames:
        client_info = [
            frame[4],  # src mac
            frame[5],  # src mac resolved
            frame[8],  # avg dbm
            frame[11], # frequency in Hz (2432 is 2.432 MHz)
        ]

        # Data are type 2 subtype 0 and QoS are type 2 subtype 8
        if (frame[9] == '2') and (frame[10] == '0' or frame[10] == '8'):
            # print('this is a Data/QoS frame: ')

            # Add MAC to client list if MAC is not BSSID and MAC not already in client list
            # Only src MACs appear to be legit clients (dest MACs seem to be broadcast and multicast only)
            if ((frame[4] != frame[2]) and (frame[4] not in nearby_wlans[frame[2]]['assoc_clients'])
                    and (frame[4] not in currently_assoc)):
                nearby_wlans[frame[2]]['assoc_clients'].append(client_info)
                currently_assoc.append(client_info)

        # Probe requests are type 0 subtype 4
        if (frame[9] == '0') and (frame[10] == '4'):
            # print('this is a Probe Request frame: ')

            # Add MAC to probing list if not a BSSID, already associated, or already added to probing
            if frame[4] not in nearby_wlans.keys() and frame[4] not in currently_assoc and frame[4] not in currently_probing:
                currently_probing.append(client_info)


    # # Some probing devices are also associated - need to fix that
    # # Some tuples are duplicates with only avg dbm being different

    # sleep(1.00)

    return [nearby_wlans, currently_assoc, currently_probing]


def find_wlans_and_probes():

    # is_active = True
    raw_frames = []
    cleaned_frames = []
    processed_frames = []

    try:
        # Stop network manager
        stop_net_mngr = (subprocess.Popen(['sudo', 'systemctl', 'stop', 'NetworkManager'])
                         .communicate()[0])
    except:
        print('there was an error stopping network manager')

    # Take interface down
    set_iface_down = (subprocess.Popen(['sudo', 'ifconfig', capture_iface, 'down'])
                      .communicate()[0])

    # Set monitor mode
    set_iface_mon = (subprocess.Popen(['sudo', 'iwconfig', capture_iface, 'mode',
                                       'monitor']).communicate()[0])

    # Take interface up
    set_iface_up = (subprocess.Popen(['sudo', 'ifconfig', capture_iface, 'up'])
                    .communicate()[0])

    # while is_active:
    #     raw_frames = get_raw_frames()
    #     cleaned_frames = clean_frames(raw_frames)
    #     results = process_frames(cleaned_frames)
    #     is_active = False
    #     return results

    raw_frames = get_raw_frames()
    # print('len raw_frames: ', len(raw_frames))

    # Raw frames can have len of 1 and still be empty
    if (len(raw_frames) >= 2) or (len(raw_frames) == 1 
        and raw_frames[0] != ''):
        cleaned_frames = clean_frames(raw_frames)
        # print('len cleaned_frames: ', cleaned_frames)

    if len(cleaned_frames) >=1:
        processed_frames = process_frames(cleaned_frames)
        # print('len processed_frames: ', processed_frames)

    if len(processed_frames) >= 1:
        print('nearby_wlans:\n', processed_frames[0], '\n')
        print('currently_assoc:\n', processed_frames[1], '\n')
        print('currently_probing:\n', processed_frames[2], '\n')
        return processed_frames
    else:
        print('no processed frames')
        return 'no data'


# find_wlans_and_probes()


# def get_new_joke():
#     response = requests.get('https://api.chucknorris.io/jokes/random')
#     return response.json()