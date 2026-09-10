# Playlist Creator

Turn a Spotify playlist into a video.
- Downloads each song from a Spotify playlist link
- Lays the track list over a background image of your choice (or a default)
- Moves an arrow down the list to highlight the current song
- Exports one MP4 with the audio and visuals combined
- Prints timestamps for each track

## Requirements

- Python 3.11 or newer
- [ffmpeg](https://ffmpeg.org/) — used to process the audio and video
- The Python packages listed in `requirements.txt`
- A free Spotify developer account for API keys

1. Download this repository and open the folder.

2. Install the Python packages (spotdl and moviepy):
```
   pip install -r requirements.txt
```

3. Make sure ffmpeg is installed. If you use Anaconda, the easiest way is:
```
   conda install -c conda-forge ffmpeg
```

4. Add your Spotify API keys: copy `config.example.py`, rename the copy to
   `config.py`, and paste in your own keys from the
   [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

## Usage

Run the script:
```
python PlaylistCreator.py
```

It asks you for three things:

1. **Playlist link** — a Spotify playlist URL
2. **Image path** — a background image for the video. Leave space to the right for the track list.
3. **Playlist name** — used to name the finished video file

When it finishes, you'll have a `<playlist name>vid.mp4` in the folder.

## Troubleshooting

**Every song fails with "YT-DLP download error":** the download tool is out of
date. Update it and try again:
```
pip install --upgrade yt-dlp
```

**A few songs fail but most work:** YouTube sometimes throttles rapid
downloads. Wait a few minutes and rerun.

## Credits

Font: [Amatic SC](https://github.com/googlefonts/AmaticSC), used under the SIL
Open Font License (see `resources/OFL.txt`).