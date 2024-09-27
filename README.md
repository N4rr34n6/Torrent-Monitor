# TorrentMonitor - Comprehensive BitTorrent Peer Tracking Tool

TorrentMonitor is an advanced Python-based tool designed to revolutionize the way you track and monitor peers in BitTorrent networks. With real-time notifications, detailed peer information, and seamless integration with Telegram, this tool offers unparalleled insight into the activities within torrent swarms.

Whether you're an internet researcher, a security analyst, or just interested in monitoring torrent activity, **TorrentMonitor** brings automation, accuracy, and convenience together in a single, powerful tool.

## Why TorrentMonitor?

- **Real-Time Peer Monitoring**: Capture extensive data on every peer connected to your torrent. From IP addresses and geolocation to the client's software and download progress, you get a complete view of network activity.
  
- **Geolocation Precision**: TorrentMonitor leverages the GeoLite2 and DB-IP ASN databases to pinpoint the exact location of peers. This data can be essential for network research, security analysis, and gaining insights into user demographics.

- **Telegram Alerts**: Receive instant notifications via Telegram when specific peer criteria are met (e.g., peers from a particular country, ISP, or region). This makes TorrentMonitor a powerful tool for automated network tracking.

- **Torrent Client Simulation**: TorrentMonitor can **simulate different torrent clients** (e.g., uTorrent, BitTorrent, qBittorrent, Transmission, Deluge) by randomly selecting a new user-agent on each execution. This enhances anonymity and replicates the behavior of various clients in the torrent network, providing more flexibility in peer interactions.

- **Scalability**: Monitor any number of `.torrent` files at once. TorrentMonitor is built to scale efficiently, tracking peers across multiple torrents while maintaining performance.

- **Customizable Filters**: Focus your monitoring efforts by setting filters, such as specific countries or ISPs, to track only the peers you are most interested in.

- **Extensive Reporting**: TorrentMonitor logs all peer data into an SQLite database for long-term analysis and exports this data into CSV files, providing flexibility for further processing or integration with other systems.

## Features

- **Comprehensive Peer Data Collection**: Collect data such as:
  - IP address
  - ISP (Internet Service Provider)
  - Client software (uTorrent, qBittorrent, etc.)
  - Geolocation (country, city, region)
  - Download and upload speeds
  - Number of seeds and peers connected
  - Torrent file info (name, size, progress, etc.)
  
- **Torrent Client Simulation**: Randomly simulate various BitTorrent clients with each session by automatically changing the `user-agent`. This feature can mimic popular clients like:
  - uTorrent 3.5.5
  - BitTorrent 7.10.5
  - qBittorrent 4.3.6
  - Transmission 3.00
  - Deluge 2.0.4
  - Vuze 5.7.7

- **Intelligent Session Management**: Fine-tune session parameters (download/upload speed, connection limits, scraping intervals) for optimized tracking and bandwidth usage.

- **CSV Export & Database Storage**: Automatically store detailed data in an SQLite database for easy querying and export to CSV for detailed analysis.

- **IP Filtering**: Filter out local IP addresses and private ranges to avoid logging irrelevant data.

## Installation

### Prerequisites
- **Python 3.6+**
- **Telegram Account**: Get your Telegram API credentials by following [this guide](https://my.telegram.org/auth).
- **GeoLite2 Database**: Download from [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data).
- **DB-IP ASN Lite Database**: Download from [DB-IP](https://db-ip.com/db/download/ip-to-asn-lite).
- **Transmission-cli**: Ensure that `transmission-cli` is installed on your system for efficient torrent management:
  ```bash
  sudo apt install -y transmission-cli
  ```

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/N4rr34n6/TorrentMonitor.git
   ```

2. **Navigate to the directory**:
   ```bash
   cd Torrent-Monitor
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Telegram**:
   - Open `TorrentMonitor.py` and replace the placeholders for `api_id`, `api_hash`, `phone`, and `recipient` with your actual Telegram API credentials.

5. **Download GeoIP Databases**:
   - Download the `GeoLite2-City.mmdb` and `dbip-asn-lite.mmdb` files from their respective sources.
   - **Important**: Place both files in the **same directory** as the TorrentMonitor script to ensure proper geolocation functionality.

## Usage

To start tracking torrents, provide a folder containing `.torrent` files. Use the following command to run TorrentMonitor:

```bash
python3 TorrentMonitor.py -d TorrentsDir -o Test -g -T 150 -c Spain -db Test.db
```

### Command-line Arguments

| Argument               | Description                                                                 | Default              |
|------------------------|-----------------------------------------------------------------------------|----------------------|
| `-d`, `--torrent_folder`| Specify the folder containing `.torrent` files (required).                   | None                 |
| `-o`, `--output`        | Specify an output file (CSV) to store peer data.                            | None                 |
| `-g`, `--geo`           | Enable geolocation for peers' IPs.                                          | False                |
| `-T`, `--time`          | Time interval (seconds) between peer checks.                                | 30                   |
| `-v`, `--verbose`       | Enable verbose logging for detailed activity logs.                          | False                |
| `-c`, `--country`       | Filter peers by country or ISO code.                                        | None                 |
| `-db`, `--database`     | Specify the SQLite database to use.                                          | `Monitor.db`         |

### Example:

```bash
python3 TorrentMonitor.py -d torrents/ -o peers_log.csv -g -T 60 -v
```

This command tracks all `.torrent` files in the `torrents/` directory, saves peer data into `peers_log.csv`, enables geolocation, and sets the check interval to 60 seconds.

## Database Schema

TorrentMonitor logs peer information into an SQLite database (`Monitor.db`) with two key tables:

1. **report_table**: Logs detailed peer connection information.
2. **info_torrent**: Stores metadata for each monitored torrent file.

### report_table Columns:
- **ip**: Peer IP address
- **port**: Connection port
- **isp**: ISP of the peer
- **client**: Torrent client (e.g., uTorrent, qBittorrent)
- **country**: Country of the peer
- **city**: City of the peer
- **first_seen**: First time the peer was seen
- **last_seen**: Last time the peer was seen
- **torrent**: Torrent file name
- **name**: Torrent name
- **infohash**: Torrent infohash
- **download_speed**: Peer’s download speed
- **upload_speed**: Peer’s upload speed

## Telegram Integration

Once configured, TorrentMonitor sends real-time notifications via Telegram when specific conditions are met, such as detecting a peer from a target country or ISP. This feature enables remote monitoring and instant alerts.

### Setting Up Telegram:
- Replace the `api_id`, `api_hash`, `phone`, and `recipient` in the script with your own credentials.
- Customize notification messages in the `send_notification` function to include peer-specific data points.

## Scalability and Use Cases

TorrentMonitor is ideal for:
- **Network Security**: Identifying suspicious peer connections.
- **Academic Research**: Studying peer behavior in torrent swarms.
- **DMCA Monitoring**: Tracking infringing downloads from specific regions.
- **Torrent Site Admins**: Understanding user demographics and download patterns.

## Future Features

- **Improved Analytics**: Enhanced data visualization and reporting tools.
- **Cross-platform Support**: Ensure compatibility with more OS environments.
- **Custom Alerts**: More granular conditions for triggering Telegram notifications.

## Contributing

We welcome contributions from the community! Feel free to open an issue or submit a pull request if you'd like to improve TorrentMonitor.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for more details.
