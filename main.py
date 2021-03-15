import random
import socket
import time
import sys
import argparse
from datetime import datetime

from gold_xctc import IdGenerator, GoldTrack
from position_funcs import position_to_geod_format, calculated_position, coords_regex


class GoldMessage:
    """
    A class representing GOLD msg to send.
    """
    msg_id = IdGenerator()

    def __init__(self, position_data: dict, track_count: int = 1, msg_originator: str = 'GOLDTX'):
        if position_data['position']:
            # Run if the position has been specified.
            position = position_data['position']
            tracks_range = position_data['tracks_range']
            # Convert position to more suitable format
            position_formatted = {'latitude': f'{position[:4]}',
                                  'latitude_dir': f'{position[4]}',
                                  'longitude': f'{position[6:11]}',
                                  'longitude_dir': f'{position[11]}'}
            position_geod = position_to_geod_format(position_formatted)
            self.gold_tracks = [GoldTrack(position=self._generate_position(position_geod, tracks_range)) for _ in range(track_count)]
        else:
            self.gold_tracks = [GoldTrack() for _ in range(track_count)]
        # TODO: 1-14 chars validation
        self.msg_originator = msg_originator

    @property
    def msg_header(self):
        """
        GOLD message header.
        """
        date_hour = datetime.utcnow().strftime("%d%H%M")
        month = datetime.utcnow().strftime("%b").upper()
        year = datetime.utcnow().strftime('%y')
        full_date_header = f'{date_hour}Z {month} {year}'
        return f'ZNR UUUUU\nP {full_date_header}\nFM {self.msg_originator}\nTO ALL\nBT\nUNCLAS\n' \
               f'MSGID/{self.msg_originator}/XCTC/{self.get_msg_id()}/{month}\n'

    @property
    def msg_trailer(self):
        """
        GOLD message trailer.
        """
        return f'ENDAT\nBT\n\n\n\n\n\n\n\nNNNN\n'

    @classmethod
    def get_msg_id(cls):
        return f'{next(GoldMessage.msg_id):04d}'

    @staticmethod
    def _generate_position(position: tuple, tracks_range: int):
        """
        Calculate random position for next track.
        """
        latitude, longitude = position
        # Convert nautical miles to meters
        tracks_range *= 1852
        # Tracks in random range and directions from designated position.
        distance = float(random.randint(0, tracks_range))
        direction = float(random.randint(0, 359))
        # Calculate position for next track.
        position_new = calculated_position(latitude, longitude, distance, direction)
        return position_new

    def update_position(self):
        """
        Update all GOLD tracks position on demand - from last position time to current time.
        """
        for track in self.gold_tracks:
            # Old position in format - LL:195201N8-1673841E0
            position_old = track.xpos.position
            # Convert old position to more suitable format
            latitude = f'{position_old[3:5]}{int(position_old[5:7]) + (int(position_old[7:9]) / 60)}'
            latitude_dir = f'{position_old[9]}'
            longitude = f'{position_old[12:15]}{int(position_old[15:17]) + (int(position_old[17:19]) / 60)}'
            longitude_dir = f'{position_old[19]}'
            position_formatted = {'latitude': latitude,
                                  'latitude_dir': latitude_dir,
                                  'longitude': longitude,
                                  'longitude_dir': longitude_dir}
            # Obtain position in Geod format
            position_geod = position_to_geod_format(position_formatted)
            date_time_old = track.xpos.date_time_group_datetime()
            date_time_new = datetime.utcnow()
            # The time that has elapsed since the last fix
            time_delta = (date_time_new - date_time_old).total_seconds()
            # Knots to m/s conversion.
            speed_ms = float(track.xpos.speed[:-3]) * 0.514444
            # Distance in meters.
            distance = speed_ms * time_delta
            direction = float(track.xpos.course[:-1])
            position_new = calculated_position(position_geod[0], position_geod[1], distance, direction)
            # Update position
            track.xpos.position = position_new
            # Update time of updated position
            track.xpos.date_time_group = date_time_new
            # Mark GOLD track as changed
            track.changed = True

    def send_tcp(self, ip_address: str, tcp_port: int, timer: int = 10):
        """
        Send GOLD data with TCP stream to specified host.
        """
        try:
            print(f'\nSending GOLD data with TCP to {ip_address}:{tcp_port}...\n')
            while True:
                timer_start = time.perf_counter()
                # Every new packet with GOLD data represents a new TCP connection
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip_address, tcp_port))
                    # Send packets only with new or changed tracks
                    if self.gold_tracks_to_send:
                        s.send(self.__str__().encode())
                        self.mark_sent_tracks()
                    # Retry/resend after timer (default 10 sec)
                    time.sleep(timer - (time.perf_counter() - timer_start))
                    # Update position
                    self.update_position()
        except (OSError, TimeoutError, ConnectionRefusedError, BrokenPipeError) as err:
            print(f'\nError: {err.strerror}\n')
            sys.exit()

    def send_udp(self, ip_address: str, udp_port: int, timer: int = 10):
        """
        Send GOLD data with UDP stream to specified host.
        """
        print(f'\nSending GOLD data with UDP to {ip_address}:{udp_port}...\n')
        while True:
            timer_start = time.perf_counter()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                try:
                    # Send packets only with new or changed tracks
                    if self.gold_tracks_to_send:
                        s.sendto(self.__str__().encode(), (ip_address, udp_port))
                        self.mark_sent_tracks()
                        time.sleep(0.05)
                except OSError as err:
                    print(f'*** Error: {err.strerror} ***')
                    sys.exit()
                # Retry/resend after timer (default 10 sec)
                time.sleep(timer - (time.perf_counter() - timer_start))
                # Update position
                self.update_position()

    def __str__(self):
        """
        Render only new or changed GOLD tracks.
        """
        return f'{self.msg_header}{"".join([str(track) for track in self.gold_tracks_to_send])}{self.msg_trailer}'

    @property
    def gold_tracks_to_send(self):
        """
        Returns only new or changed GOLD tracks.
        """
        return [track for track in self.gold_tracks if track.changed]

    def mark_sent_tracks(self):
        """
        Mark already sent GOLD tracks as unchanged.
        """
        for track in self.gold_tracks_to_send:
            track.changed = False

    def __len__(self):
        """
        Returns number of GOLD tracks in message.
        """
        return len(self.gold_tracks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='The script generates random OTH-T GOLD tracks')
    parser.add_argument('-n', '--number', default=1, type=int, help='GOLD tracks count (default: 1)')
    parser.add_argument('-c', '--coords', type=coords_regex, help='GOLD track position (default: random)')
    parser.add_argument('-r', '--range', default=0, type=int,
                        help='Max track distance in nautical miles from the specified position (default: 0)')
    parser.add_argument('-t', '--proto', default='tcp', choices=['tcp', 'udp'],
                        help='Choose UDP transport protocol (default: tcp)')
    parser.add_argument('-p', '--port', default=2020, type=int, help='Remote host port (default: 2020)')
    parser.add_argument('ip_address', help='Remote host ip address/hostname')
    args = parser.parse_args()

    # Get data from argparse
    track_number = args.number
    transport_protocol = args.proto
    ip_address = args.ip_address
    port_number = args.port
    position_data = {'position': args.coords, 'tracks_range': args.range}

    try:
        if track_number > 1 and position_data['tracks_range'] == 0 and position_data['position']:
            print('Error: Range should be greater than 0 if the number of tracks is greater than 1.')
            raise KeyboardInterrupt
        msg = GoldMessage(position_data=position_data, track_count=track_number)
        print('*** Press "Ctrl + c" to exit ***')
        if transport_protocol == 'tcp':
            msg.send_tcp(ip_address, port_number)
        else:
            msg.send_udp(ip_address, port_number)
    except KeyboardInterrupt:
        sys.exit()
