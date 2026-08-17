import http.server
import json
import glob
import random
import os
import sys
import winsound
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import game_dir, log_dir

audio_dir = os.path.join(game_dir(), "migi", "csgo", "addons", "p_GuanXiaoyu_Voice", "sound", "player", "vo")
death_sounds = glob.glob(os.path.join(audio_dir, '**', '*death*.wav'), recursive=True)
grenade_sounds = glob.glob(os.path.join(audio_dir, '**', '*grenade*.wav'), recursive=True)

def play_sound(sound_list):
    if not sound_list: return
    sound_path = random.choice(sound_list)
    try:
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        pass

class GSIServer(http.server.BaseHTTPRequestHandler):
    previous_health = 100
    previous_grenades = []

    def log_message(self, format, *args): pass

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        payload = json.loads(body.decode('utf-8'))
        
        # LOG EVERYTHING TO A FILE FOR DEBUGGING
        with open(os.path.join(log_dir(), "gsi_payload_debug.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
            
        self.process_payload(payload)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def process_payload(self, payload):
        player = payload.get('player', {})
        if not player: return
            
        player_state = player.get('state', {})
        player_weapons = player.get('weapons', {})
        
        current_health = player_state.get('health', 0)
        if GSIServer.previous_health > 0 and current_health == 0:
            play_sound(death_sounds)

        current_grenades = [w.get('name') for w in player_weapons.values() if 'grenade' in w.get('name', '') or 'flashbang' in w.get('name', '')]
        for g_name in GSIServer.previous_grenades:
            if g_name not in current_grenades:
                play_sound(grenade_sounds)

        GSIServer.previous_health = current_health
        GSIServer.previous_grenades = current_grenades

if __name__ == '__main__':
    server_address = ('127.0.0.1', 3000)
    httpd = http.server.HTTPServer(server_address, GSIServer)
    httpd.serve_forever()
