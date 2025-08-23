# Wheel of Fortune Demo

Displays Wheel of Fortune game show board

Fills in WOF board with simulated letter guesses

## Usage

```
run pbk_wheel_of_fortune.py
```

## Demonstrates

- Fixed pitch character font board sprite images
- Accessing sprite character images via letter id

## Requires

- Tested on a Raspberry pico 2w
- modules/pbk_ili9488.py
- modules/sprite_handler.py

## Files

- pbk_wheel_of_fortune.py
  - demonstration application
- wheel_of_fortune.py
  - WOF module that controls the game board
- wof-char120x76.raw
  - Displays a smaller WOF board characters that could be used on small displays
  - set SMALL to True in wheel_of_fortune.py
- wof-char240x152.raw
  - Full sized WOF board characters
- mpremote.sh
  - linux bash script to run demo via mpremote
  - May not run because of additional memory requirements
- README.md
  - This documentation file
