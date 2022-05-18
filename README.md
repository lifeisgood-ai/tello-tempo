# tello-tempo
Tello Tempo makes Tello drone dance


## How to run

$ python tello_tempo.py --camera [0|1]

The `--camera` parameter has to be set to 0 to use webcam; it defaults to 1 to use drone

At launch the TelloSound module loads all audio files and extracts beats. It takes a few seconds (to be improved)


To run swing movement, show 3 fingers to drone front camera or press c

To stop demo show 4 fingers or press v

To play/stop music show finger 1 or 2, or press b or n



## Commands

| What        | Fingers     | Keyboard       |
|-------------|-------------|----------------|
| play music  | 1           | b              |
| stop music  | 2           | n              |
| dance swing | 3           | c              |
| stop swing  | 4           | v              |
| stop & quit |             | q              |
| volume set  | index/thumb |                |
| takeoff     | 5           | &lt;tab>       |
| land        |             | &lt;backspace> |
| move left   |             | left arrow     |
| move right  |             | right arrow    |
| move up     |             | top arrow      |
| move down   |             | low arrow      |
| stop move   |             | x              |





