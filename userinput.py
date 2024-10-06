import IR_decoder_NEC

class IRRemoteControl:
    def wait_for_input(self, pi_player):
        input = IR_decoder_NEC.ConvertHex(IR_decoder_NEC.getData())
        if input == "0x3e0e016e9" or input == "0x300ffe21d":
            pi_player.play_next_song()
        elif input == "0x3e0e048b7" or input == "0x300ff629d":
            pi_player.play_next_album()
        elif input == "0x3e0e008f7" or input == "0x300ffc23d":
            pi_player.play_previous_song()
        elif input == "0x300ff02fd":
            pi_player.play_previous_album()
        elif input == "0x3e0e0e01f" or input == "0x300ffa25d":
            pi_player.volume_up()
        elif input == "0x3e0e0d02f" or input == "0x300ff22dd":
            pi_player.volume_down()
        elif input == "0x300ff906f":
            pi_player.song_play_pause()
        elif input == "0x300ffa857":
            pi_player.switch_collection()
        elif len(input) > 5:
            print(f"input {input} not recognized", flush=True)

# this is for testing the system without an IR receiver/remote
class KeyboardControl():
    def wait_for_input(self, pi_player):
        value = input("n=next, p=prev, m=next_album, [=prev_album, v=vol_up, b=vol_down, j=play_pause\n")
        if value == "n":
            pi_player.play_next_song()
        elif value == "m":
            pi_player.play_next_album()
        elif value == "p":
            pi_player.play_previous_song()
        elif value == "[":
            pi_player.play_previous_album()
        elif value == "v":
            pi_player.volume_up()
        elif value == "b":
            pi_player.volume_down()
        elif value == "j":
            pi_player.song_play_pause()
        else:
            print(f"input {value} not recognized", flush=True)
