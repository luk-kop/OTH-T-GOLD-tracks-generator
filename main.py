import random
import string
import socket
import time
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional

from ctc_data import CtcFlag, CtcType, CtcCategory
from position_funcs import position_to_geod_format, calculated_position, coords_regex


class IdGenerator:
    """
    Simple ID generator.
    """
    def __init__(self, start=1):
        self.id = start

    def __iter__(self):
        return self

    def __next__(self):
        current_id = self.id
        self.id += 1
        return current_id


class GoldCtc:
    """
    A class representing CTC OTG set.
    """
    name_id = IdGenerator()

    def __init__(self, name: str = 'TEST'):
        self.track_number = f'T{random.randrange(100, 99_999):05d}'
        self.class_name = f'UNEQUATED-{name}{next(GoldCtc.name_id)}'     # to change
        self.trademark = ''
        self.type = CtcType.get_random_name()
        self.category = CtcCategory.get_random_name()
        self.pennant_number = f'{random.choice(["D", "A", "M", "F", "P", ""])}{random.randrange(10, 9_999)}'
        self.flag = CtcFlag.get_random_name()
        self.sconum = ''
        self.selective_id = ''
        self.alert_code = random.choice(['', 'TGT', 'SUS', 'HIT', 'NSP'])
        while True:
            force_code = random.randrange(1, 58)
            # Exclude 33-37
            if force_code not in list(range(33, 38)):
                self.force_code = f'{force_code:02d}'
                break
        self.system_track_no = ''
        self.track_type = ''
        self.average_speed = f'{str(random.randint(0, 50))}'
        self.average_time_on_leg = ''
        self.discrete_id = ''
        self.uid = f'{random.choice(["ORP", "FGS", "LLL", "COM", "LAV", "PLN"])}' \
                   f'{random.randrange(1_000_000, 999_999_999):09d}'
        self.ircs = ''.join(random.sample(string.ascii_uppercase, 4))
        self.suspicion_code = random.choice([f'{random.randrange(1, 11):02d}', ''])
        self.emitter_voice_cs = ''

    def get_all_attr(self):
        return [value for value in self.__dict__.values()]

    def __str__(self):
        separator = '/'
        return f'CTC/{separator.join(self.get_all_attr())}'.rstrip(separator)


class GoldXpos:
    """
    A class representing XPOS OTG set.
    """
    def __init__(self, position: Optional[tuple] = None):
        self._date_time_group = self.date_time_group
        self.month_year = f'{datetime.utcnow().strftime("%b").upper()}{datetime.utcnow().strftime("%y")}'
        self.position = position
        self.sensor_code = random.choice(['', 'RADAR', 'VISUAL', 'UNK', 'PHOTO', 'SRN25', 'IFF', 'IR'])
        self.bearing_of_major_axis = ''
        self.length_of_semi_major_axis = ''
        self.length_of_semi_minor_axis = ''
        self.course = f'{random.randint(0, 359):03d}.{random.randint(0, 9)}T'
        self.speed = f'{random.randint(0, 50)}KTS'
        self.altitude = ''
        self.depth = ''
        self.rdf_rf = ''
        self.source_code = random.choice(['', 'EST', 'NTDS', 'UNK'])
        self.seq_contact_id = ''
        self.photos = ''
        self.total_no_of_contacts = ''

    @property
    def date_time_group(self):
        # TODO: different timestamp for each track
        # Subtract 30 min from utcnow
        date = f'{(datetime.utcnow().replace(second=0) - timedelta(hours=0, minutes=30)).strftime("%d%H%M%S")}'
        return f'{date}Z{self._check_sum(date)}'

    @property
    def position(self):
        """
        Returns position in format - LL:552521N0-0163311E5
        """
        return self._position

    @position.setter
    def position(self, value: tuple):
        if not value:
            # Random position
            latitude = f'{random.randrange(0, 90):02d}{random.randrange(0, 60):02d}{random.randrange(0, 60):02d}'
            longitude = f'{random.randrange(0, 180):03d}{random.randrange(0, 60):02d}{random.randrange(0, 60):02d}'
            latitude_dir = random.choice(['N', 'S'])
            longitude_dir = random.choice(['E', 'W'])
            position = f'LL:{latitude}{latitude_dir}{self._check_sum(latitude)}-' \
                       f'{longitude}{longitude_dir}{self._check_sum(longitude)}'
        else:
            # The position specified by the user
            latitude, latitude_dir, longitude, longitude_dir = value
            position = f'LL:{latitude}{latitude_dir}{self._check_sum(latitude)}-' \
                       f'{longitude}{longitude_dir}{self._check_sum(longitude)}'
        self._position = position

    @staticmethod
    def _check_sum(value: str):
        """
        Calculate checksum
        """
        return sum([int(num) for num in value]) % 10

    def get_all_attr(self):
        return [value for value in self.__dict__.values()]

    def __str__(self):
        separator = '/'
        return f'XPOS/{separator.join(self.get_all_attr())}'.rstrip(separator)


class GoldTrack:
    """
    A class representing a single track
    """
    def __init__(self, position: Optional[tuple] = None):
        self.ctc = GoldCtc()
        self.xpos = GoldXpos(position)

    def __str__(self):
        return f'{self.ctc}\n{self.xpos}\n'


class GoldMessage:
    """
    A class representing GOLD msg to send.
    """
    msg_id = IdGenerator()

    def __init__(self, position_data: dict, track_count: int = 1, msg_originator: str = 'GOLDTX'):
        if position_data['position']:
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

    def __str__(self):
        return f'{self.msg_header}{"".join([str(track) for track in self.gold_tracks])}{self.msg_trailer}'

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
        distance = random.randint(0, tracks_range)
        direction = random.randint(0, 359)
        # Calculate position for next track.
        position_new = calculated_position(latitude, longitude, distance, direction)
        return position_new

    def send_tcp(self, ip_address: str, tcp_port: int, timer: int = 5):
        """
        Send GOLD data with TCP stream to specified host.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_address, tcp_port))
                print(f'\nSending GOLD data with TCP to {ip_address}:{tcp_port}...\n')
                while True:
                    timer_start = time.perf_counter()
                    s.send(self.__str__().encode())
                    # Retry/resend after timer (default 5 sec)
                    time.sleep(timer - (time.perf_counter() - timer_start))
        except (OSError, TimeoutError, ConnectionRefusedError, BrokenPipeError) as err:
            print(f'\nError: {err.strerror}\n')
            sys.exit()

    def send_udp(self, ip_address: str, udp_port: int, timer: int = 5):
        """
        Send GOLD data with UDP stream to specified host.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            print(f'\nSending GOLD data with UDP to {ip_address}:{udp_port}...\n')
            while True:
                timer_start = time.perf_counter()
                try:
                    s.sendto(self.__str__().encode(), (ip_address, udp_port))
                    time.sleep(0.05)
                except OSError as err:
                    print(f'*** Error: {err.strerror} ***')
                    sys.exit()
                # Retry/resend after timer (default 5 sec)
                time.sleep(timer - (time.perf_counter() - timer_start))

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
