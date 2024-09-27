#!/usr/bin/env python3

import libtorrent as lt
import geoip2.database
from datetime import datetime, timezone
import argparse
import time
import csv 
import os 
import subprocess
import json
import logging
import random
from colorama import Fore, Style, init
import requests
import sqlite3 
import shutil
from telethon.sync import TelegramClient
import telethon
from libtorrent import ip_filter
import getpass 
from telethon.errors import SessionPasswordNeededError

# Obfuscated sensitive data
api_id = 12345678  # Replace with your actual Telegram API ID
api_hash = "your_api_hash_here"  # Replace with your actual Telegram API hash
phone = "+1234567890"  # Replace with your actual phone number
recipient = 1234567890  # Replace with the actual recipient ID

# Initialize Telegram client
client = telethon.TelegramClient('session.session', api_id, api_hash)

client.connect()

if not client.is_user_authorized():
    client.send_code_request(phone)

    try:
        client.sign_in(phone, input('Enter the code: '))
    except telethon.errors.SessionPasswordNeededError:
        password = getpass.getpass("Password: ")
        client.sign_in(password=password)

def send_notification(recipient, peer_dict):
    """
    Send a notification message to a Telegram channel with peer information.
    """
    message = f"✔️ A connected peer has been detected from <code>{peer_dict['country']}</code>:\n"
    message += f"IP: <code>{peer_dict['ip']}</code>\n"
    message += f"Port: <code>{peer_dict['port']}</code>\n"
    message += f"ISP: <code>{peer_dict['isp']}</code>\n"
    message += f"City: <code>{peer_dict['city']}</code>\n"
    message += f"Region: <code>{peer_dict['province']}</code>\n"
    message += f"Client: <code>{peer_dict['client']}</code>\n"
    message += f"Torrent: <code>{peer_dict['name']}</code>\n"
    message += f"Infohash: <code>{peer_dict['infohash']}</code>\n"
    message += f"First seen: <code>{peer_dict['first_seen']}</code>\n"
    message += f"🔚\n"

    channel_id = -1001234567890  # Replace with your actual channel ID
    entity = client.get_entity(channel_id)
    client.send_message(entity, message, parse_mode='html')

class TorrentTracker:
    def __init__(self, torrent_folder, output, geo, database):
        self.torrent_folder = torrent_folder
        self.output = output
        self.geo = geo
        self.database = database
        self.user_agents = ['uTorrent 3.5.5', 'BitTorrent 7.10.5', 'qBittorrent 4.3.6', 
                            'Transmission 3.00', 'Deluge 2.0.4', 'Vuze 5.7.7']
        self.session_settings = {
            'user_agent': random.choice(self.user_agents),
            'listen_interfaces': '0.0.0.0:6881,[::]:6881,0.0.0.0:6882,[::]:6882',
            'download_rate_limit': 10000,
            'upload_rate_limit': 0,
            'connections_limit': 800,
            'alert_mask': lt.alert.category_t.all_categories,
            'outgoing_interfaces': '',
            'announce_to_all_tiers': True,
            'announce_to_all_trackers': True,
            'auto_manage_interval': 5,
            'auto_scrape_interval': 0,
            'auto_scrape_min_interval': 0,
            'max_failcount': 1,
            'aio_threads': 8,
            'checking_mem_usage': 2048,
        }
        
        self.session = lt.session()
        self.session.apply_settings(self.session_settings)
        f = ip_filter()
        f.add_rule("192.168.0.0", "192.168.255.255", 1)
        f.add_rule("10.0.0.0", "10.255.255.255", 1)
        f.add_rule("192.168.1.0", "192.168.1.255", 1)
        f.add_rule("127.0.0.0", "127.0.0.255", 1)
        self.session.set_ip_filter(f)
        random_user_agent = random.choice(self.user_agents)
        self.session_settings['user_agent'] = random_user_agent
        self.session.apply_settings(self.session_settings) 
        self.reader = geoip2.database.Reader('GeoLite2-City.mmdb')
        self.logger = logging.getLogger('TorrentTracker') 
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.seen_peers = set()

        init()

    def add_torrent(self, torrent_path):
        """
        Add a torrent file to the session.
        """
        try:
            random_user_agent = random.choice(self.user_agents)
            self.session_settings['user_agent'] = random_user_agent
            self.session.apply_settings(self.session_settings) 
            handle = self.session.add_torrent({'ti': lt.torrent_info(torrent_path), 
                                               'save_path': 'Downloads', 
                                               'user_agent': random_user_agent})
            return handle
        except Exception as e:
            self.logger.error(f"Error creating torrent handler for {torrent_path}: {e}")

    def get_geo_info(self, ip):
        """
        Get geographical information for an IP address.
        """
        cmd = f"./mmdbinspect -db GeoLite2-City.mmdb {ip}"
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
        json_output = json.loads(result.stdout.decode('utf-8'))
        return json_output[0]['Records'][0]['Record']

    def get_isp_info(self, ip):
        """
        Get ISP information for an IP address.
        """
        cmd = f"./mmdbinspect -db dbip-asn-lite.mmdb {ip}"
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
        json_output = json.loads(result.stdout.decode('utf-8'))
        try:
            isp_info = json_output[0]['Records'][0]['Record']
        except TypeError:
            isp_info = 'N/A'
        return isp_info

    def format_time(self, timestamp):
        """
        Format a timestamp to a readable string.
        """
        return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')

    def remove_prefix(self, ip):
        """
        Remove IPv6 prefix from an IP address if present.
        """
        if ip.startswith("::ffff:"):
            return ip[7:]
        else:
            return ip

    def main(self):
        """
        Main method to run the torrent tracker.
        """
        if os.path.exists('notified_peers.txt'):
            os.remove('notified_peers.txt')

        try:
            with open('notified_peers.txt', 'w') as f:
                pass
            self.logger.info("File 'notified_peers.txt' created successfully.")
        except Exception as e:
            self.logger.error(f"Error creating 'notified_peers.txt' file: {e}")
        
        fieldnames = ['ip', 'port', 'isp', 'client', 'countryISO', 'country', 'city', 'region', 'province',
                      'first_seen', 'last_seen', 'torrent', 'name', 'infohash', 'total_size', 
                      'num_pieces', 'piece_size', 
                      'downloaded_pieces', 
                      'download_speed', 
                      'upload_speed',
                      'num_seeds',
                      'num_peers',
                      'estimated_time',
                      'state'
                      ]  
        
        if not os.path.exists(self.torrent_folder): 
            self.logger.error(f"The folder {self.torrent_folder} does not exist or cannot be read.")
            exit(1) 
        
        torrent_files = [f for f in os.listdir(self.torrent_folder) if f.endswith('.torrent')]
        
        if not torrent_files:
            self.logger.warning(f"The folder {self.torrent_folder} is empty. There are no torrent files to track.")
            exit(1) 

        handles = []
        for f in torrent_files:
            try:
                handle = self.add_torrent(os.path.join(self.torrent_folder, f))
                handles.append(handle)
            except Exception as e:
                self.logger.error(f"The torrent file {f} is not valid or cannot be added to the session: {e}")

        self.logger.info(f'Starting to track {len(handles)} torrents') 
        
        if self.output:
            if not os.path.exists(f"{self.output}.csv"): 
                try:
                    with open(f"{self.output}.csv", 'a+', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                except Exception as e:
                    self.logger.error(f"The output path {self.output}.csv is not valid or cannot be written to: {e}")
                    exit(1) 
            else:
                f = open(f"{self.output}.csv", 'a+', newline='') 
            
            conn = sqlite3.connect(self.database)
            cur = conn.cursor() 
            cur.execute("""CREATE TABLE IF NOT EXISTS report_table (
                ip TEXT,
                port INTEGER,
                isp TEXT,
                client TEXT,
                countryISO TEXT,
                country TEXT,
                city TEXT,
                region TEXT,
                province TEXT,
                first_seen TEXT,
                last_seen TEXT,
                torrent TEXT,
                name TEXT,
                infohash TEXT,
                total_size INTEGER,
                num_pieces INTEGER,
                piece_size INTEGER,
                downloaded_pieces INTEGER,
                download_speed INTEGER,
                upload_speed INTEGER,
                num_seeds INTEGER,
                num_peers INTEGER,
                estimated_time TEXT,
                state TEXT
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS info_torrent (
                torrent_infohash TEXT PRIMARY KEY,
                details TEXT
            )""")
            conn.commit() 

        seen_times = {}

        cur.execute("SELECT ip, port, infohash, first_seen FROM report_table")
        for row in cur.fetchall():
            ip, port, infohash, first_seen = row
            seen_times[(ip, port, infohash)] = {'first_seen': first_seen, 'last_seen': first_seen}

        response = requests.get('http://ifconfig.me') 
        if response.status_code == 200: 
            my_ip = response.text
            self.logger.info(f"Working with IP \033[30;47m{Fore.YELLOW + Style.BRIGHT + my_ip + Style.RESET_ALL}\033[0m. This IP address will not be saved in the database.") 
        else:
            self.logger.error(f"Unable to obtain public IP. Status code: {response.status_code}")
            exit(1) 

        for f in torrent_files: 
            try:
                result = subprocess.run(['transmission-show', os.path.join(self.torrent_folder, f)], capture_output=True) 
                details = result.stdout.decode('utf-8') 
                infohash = lt.torrent_info(os.path.join(self.torrent_folder, f)).info_hash() 
                cur.execute("INSERT OR IGNORE INTO info_torrent (torrent_infohash, details) VALUES (?, ?)", (str(infohash), details)) 
                conn.commit() 
            except Exception as e:
                self.logger.error(f"Unable to obtain details of torrent file {f}: {e}")

        notified_peers = set()

        try:
            with open('notified_peers.txt', 'r+') as f: 
                peer_tuple = ()
                for line in f:
                    line = line.rstrip() 
                    peer_tuple = tuple(line.split(','))
                    if peer_tuple[-1] == 'None': 
                        f.seek(0) 
                        for line2 in f:
                            if line2 != line:
                                f.write(line2) 
                        f.truncate() 
                        f.write(','.join(str(x) for x in peer_tuple) + '\n') 
                    notified_peers.add(peer_tuple)
                if peer_tuple not in notified_peers:
                    f.write(','.join(str(x) for x in peer_tuple))

        except FileNotFoundError:
            self.logger.info("The notified peers file does not exist. A new one will be created.")

        try:
            while True:
                for i, handle in enumerate(handles):
                    status = handle.status()

                    self.logger.debug(f"Processing torrent {status.name} - {status.progress * 100:.2f}% completed")

                    peers = handle.get_peer_info()
                    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
                    if peers:
                        peer_dict = {}
                        for peer_info in peers:
                            ip, port = peer_info.ip
                            ip = self.remove_prefix(ip)

                            if ip == my_ip:
                                continue
                            
                            infohash = handle.info_hash()

                            cur.execute("SELECT max(first_seen) FROM report_table WHERE ip = ? AND port = ? AND infohash = ?", (ip, port, str(infohash))) 
                            result = cur.fetchone()
                            if result and result[0]: 
                                first_seen = result[0] 
                            else:
                                first_seen = today 
                            try:
                                client = peer_info.client
                            except UnicodeDecodeError:
                                client = 'Unknown'
                            if not client: 
                                client = 'unknown' 
                            peer_tuple = (ip, port, client, infohash, first_seen)

                            max_retries = 2
                            retries = 0
                            while retries < max_retries:
                                try:
                                    geo_info = self.get_geo_info(ip)
                                    country = geo_info['country']['names']['en']
                                    country_iso = geo_info['country']['iso_code']
                                    city = geo_info['city']['names']['en'] if 'city' in geo_info else ''

                                    if 'subdivisions' in geo_info:
                                        if len(geo_info['subdivisions']) > 1:
                                            region = geo_info['subdivisions'][0]['names']['en']
                                            province = geo_info['subdivisions'][1]['names']['en']
                                        elif len(geo_info['subdivisions']) == 1:
                                            region = geo_info['subdivisions'][0]['names']['en']
                                            province = ''
                                    else:
                                        region = ''
                                        province = ''
                                    break
                                except TypeError:
                                    retries += 1
                                    self.logger.warning(f"Unable to get geographic information for IP {ip}. Retrying... ({retries}/{max_retries})")
                            else:
                                self.logger.error(f"Unable to get geographic information for IP {ip} after {max_retries} attempts.")
                                country = 'N/A'
                                country_iso = 'N/A'
                                city = 'N/A'
                                region = 'N/A'
                                province = 'N/A'

                            isp_info = self.get_isp_info(ip)
                            if isinstance(isp_info, dict):
                                isp = isp_info['autonomous_system_organization']
                            else:
                                isp = isp_info

                            try:
                                client = peer_info.client
                            except UnicodeDecodeError:
                                client = 'Unknown'
                            infohash = handle.info_hash()
                            total_size = handle.torrent_file().total_size()
                            num_pieces = handle.torrent_file().num_pieces()
                            piece_size = handle.torrent_file().piece_length()
                            downloaded_pieces = peer_info.downloading_piece_index

                            progress = peer_info.progress
                            if downloaded_pieces == -1 and progress == 1:
                                peer_dict['downloaded_pieces'] = downloaded_pieces
                                peer_dict['state'] = 'completed'
                            elif downloaded_pieces == -1 and progress < 1:
                                peer_dict['downloaded_pieces'] = downloaded_pieces
                                peer_dict['state'] = 'stopped'
                            else:
                                peer_dict['downloaded_pieces'] = downloaded_pieces
                                peer_dict['state'] = 'downloading'

                            download_speed = peer_info.payload_down_speed
                            upload_speed = peer_info.payload_up_speed

                            num_seeds = status.num_seeds
                            num_peers = status.num_peers

                            if download_speed > 0:
                                estimated_time_seconds = (total_size - downloaded_pieces * piece_size) / download_speed
                                estimated_time_string = time.strftime('%H:%M:%S', time.gmtime(estimated_time_seconds))
                            else:
                                estimated_time_string = 'infinite'

                            torrent_name = handle.torrent_file().name()

                            peer_dict = {
                                'ip': ip, 'port': port, 'isp': isp, 'client': client, 'countryISO': country_iso,
                                'country': country, 'city': city, 'region': region, 'province': province,
                                'first_seen': first_seen, 
                                'last_seen': today, 'torrent': torrent_files[i], 'name': torrent_name, 
                                'infohash': str(infohash), 
                                'total_size': total_size, 'num_pieces': num_pieces,
                                'piece_size': piece_size, 'downloaded_pieces': downloaded_pieces,
                                'download_speed': download_speed, 
                                'upload_speed': upload_speed,
                                'num_seeds': num_seeds,
                                'num_peers': num_peers,
                                'estimated_time': estimated_time_string,
                                'state': peer_dict['state']
                            }

                            if (ip, port, str(infohash)) in seen_times:
                                peer_dict['first_seen'] = seen_times[(ip, port, str(infohash))]['first_seen']
                            else:
                                seen_times[(ip, port, str(infohash))] = {'first_seen': today, 'last_seen': today}
                                peer_dict['first_seen'] = today
                                peer_dict['last_seen'] = today

                            if country == args.country:
                                peer_tuple = (ip, port, client, infohash, first_seen)
                                if peer_tuple not in notified_peers:
                                    with open('notified_peers.txt', 'r') as f:
                                        peer_string = ','.join(str(x) for x in peer_tuple)
                                        if peer_string in f.read():
                                            pass
                                        else:

                                            # This section would contain sensitive or custom logic
                                            # It has been removed for privacy and security reasons
                                            # You can implement your own custom logic here

                                            try:
                                                self.logger.info(f"Notification sent via Telegram.")
                                                send_notification(recipient, peer_dict)

                                                # Additional custom logic can be implemented here
                                                # This section has been removed for privacy and security reasons

                                            except Exception as e:
                                                self.logger.error(f"Error sending Telegram notification: {e}")
                                            notified_peers.add(peer_tuple)
                                            with open('notified_peers.txt', 'a') as f:
                                                f.write(','.join(str(x) for x in peer_tuple) + '\n')

                            if args.country is None or country == args.country:
                                if self.output:
                                    with open(f"{self.output}.csv", 'a+', newline='') as f:
                                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                                        writer.writerow(peer_dict)
                                    cur.execute("INSERT INTO report_table VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", list(peer_dict.values())) 
                                    conn.commit() 

                                if downloaded_pieces == -1:
                                    self.logger.info(Fore.RED + f"Peer {Fore.BLUE + ip + Fore.RED} has completed downloading the torrent {torrent_name}. The peer is in the province of {Fore.BLUE + province + Fore.RED}." + Style.RESET_ALL)
                                else:
                                    self.logger.info(Fore.GREEN + f"New data inserted for peer {Fore.BLUE + ip + Fore.GREEN} and torrent {torrent_name}. The peer is in the province of {Fore.BLUE + province + Fore.GREEN} and has downloaded {downloaded_pieces} out of {num_pieces} pieces. The download speed is {download_speed} bytes per second and the estimated time to complete the download is {estimated_time_string}." + Style.RESET_ALL)

                time.sleep(int(args.time))
                
        except KeyboardInterrupt:
            self.logger.info("\nCleaning up")
            if self.output:
                f.close()
                conn.close() 
                download_path = 'Downloads' 
                try:
                    for root, dirs, files in os.walk(download_path):
                        for file in files:
                            os.remove(os.path.join(root, file))
                        for dir in dirs:
                            shutil.rmtree(os.path.join(root, dir))
                    self.logger.info("Content of 'Downloads' folder deleted successfully.")
                except Exception as e:
                    self.logger.error(f"Could not delete content of 'Downloads' folder: {e}")

            if self.geo:
                self.reader.close()
                download_path = 'Downloads' 
                try:
                    for root, dirs, files in os.walk(download_path):
                        for file in files:
                            os.remove(os.path.join(root, file))
                        for dir in dirs:
                            shutil.rmtree(os.path.join(root, dir))
                    self.logger.info("Content of 'Downloads' folder deleted successfully.")
                except Exception as e:
                    self.logger.error(f"Could not delete content of 'Downloads' folder: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--torrent_folder", help="Folder containing torrent files", required=True)
    parser.add_argument("-o", "--output", help="Output path", default=False)     
    parser.add_argument("-g", "--geo", help="Enable IP geolocation", default=False, action='store_true')     
    parser.add_argument("-T", "--time", help="Wait time between peer downloads", default=30)         
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", default=False, action='store_true')
    parser.add_argument("-c", "--country", help="Country or ISO code to save data", default=None)  
    parser.add_argument("-db", "--database", help="Database to use", default="Monitor.db")
    args = parser.parse_args()

    t = TorrentTracker(args.torrent_folder, args.output, args.geo, args.database)
    if args.verbose:
        t.logger.setLevel(logging.DEBUG)
    t.main()
