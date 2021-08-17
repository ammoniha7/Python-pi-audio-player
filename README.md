# PiPlayer
A basic audio player for the raspberry pi that can be controlled with an IR remote using the NEC protocol.

## Dependencies
### External Dependencies
sox
``` shell
sudo apt install sox libsox-fmt-all
```

### Python Dependencies
gTTS
```shell
pip3 install gTTS
```

### Infrared Sensor
https://www.amazon.com/gp/product/B06XYNDRGF/ref=ppx_yo_dt_b_asin_title_o07_s01?ie=UTF8&psc=1
The sensor has three leads, when looking at it with the black facing you, from left to right its pinout is (output pin, ground, vcc).
Those leads are to be hooked up to the pi on the pi's 5v output pin to sensors vcc pin, the pi's ground to the sensors ground, and the pi's GPIO #11 (can be changed in the code) to the sensors output pin.
