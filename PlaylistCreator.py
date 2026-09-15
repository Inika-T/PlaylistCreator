'''

@author: topaz

'''
import re
import os
import shutil
from spotdl import Spotdl
from moviepy import AudioFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
from config import CLIENT_ID, CLIENT_SECRET

#Global variable
baseImageTextNoArrowPath = "baseImageNoArrows.png"

''' 
Function that creates an array of metadata dictionaries for each song and downloads songs
With spotify playlist input
filename field is used to access location of the downloaded mp3 
'''
    

def spotifyDownload(spotdl, url):
    print ("Searching for the songs...")
    songs = spotdl.search([url])
    print ("Downloading songs...")
    results = spotdl.download_songs(songs) 
    print ("Songs downloaded.")
    metadataList = []
    
    for song, path in results:
        songMetaData = {
          "songname": song.name,
          "artists": ',  '.join(song.artists),
          "duration": song.duration,
          "playlistposition":song.list_position,
          "timestamp":0,
          "filename": str(path),
          "path": path,
          "song_obj": song
        }
        metadataList.append(songMetaData)
    
    #Sometimes spotDL fails download from YouTube and sets filepath as None 
    #But other metadata is still extracted from spotify
    
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        # Creates a list of songs that failed to download (filename is None)
        remaining = [s for s in metadataList if s["filename"] == "None"]
        if not remaining:
            break
        for song in remaining:
            print("Error downloading. Trying again: " + song["songname"])
            re_download, path = spotdl.download(song["song_obj"])
            song["filename"] = str(path)
            song["path"] = path

    # Stop here if anything still failed after all retries
    failed = [s for s in metadataList if s["filename"] == "None"]
    if failed:
        names = ", ".join(s["songname"] for s in failed)

        # maybe delete the mp3 files that were downloaded successfully, since the playlist is incomplete? 
        raise RuntimeError(f"Failed to download after {MAX_RETRIES} tries: {names}")
    
    #Sorting the metadataList according to its position in the playlist given so its not randomized
    metadataList = sorted(metadataList, key=lambda song: song['playlistposition'])
    
    #Iterate through sorted metadataList in order to update the start timestamp field using duration of each song
    cumulativeDuration = 0
    for song in metadataList:
        song["timestamp"] = cumulativeDuration
        cumulativeDuration += song["duration"]
    
    return metadataList
'''
Function that creates song list text and adds it to the raw image  
image_path is the raw image inputted by user as an absolute path
x_position and arrowImagePath are static variables 
'''
def addTextToImage (x_position, arrowImagePath, metadataList, image_path):
    base_image_clip = ImageClip(image_path).resized(width=1920, height=1080)
    
    #Creating the text box as a string 
    #Moviepy cuts off the top half of the first line, so a blank line has been added to the top and bottom
    songListText = " \n"
    
    for song in metadataList:
        songname = song["songname"]
        artists = song["artists"]
        playlistposition = song["playlistposition"]
        
        string1 = f"{playlistposition}. {songname}- {artists}"
        if len(string1) > 42:
            string1 = string1[:38]+"..."
        songListText += string1 + "\n"
        
    songListText += "\n"
    
    if (len(metadataList)>15):
        fontsize = 48
    else:
        fontsize = 50
    
    #Defining parameters for the text box as a text clip
    fontAmatic = os.getcwd()+r"\resources\AmaticSC-Bold.otf"
    songList = TextClip(
        fontAmatic,
        text = songListText, 
        font_size = fontsize, 
        color = '#FFFFFF',
        bg_color = None,
        interline = 10
        )
    
    text_height = songList.h
    #Determining height of the arrow, taking into account the blank lines at top and bottom
    arrowOffset = (text_height)/(len(metadataList)+ 2)
    arrow_image_clip = ImageClip(arrowImagePath).resized(height=arrowOffset)
    
    #Positioning the text clip to right and center, taking into account top half of line being cut off
    y_position = (1080 - text_height) / 2 

    songList = songList.with_position((x_position,y_position))
    
    #Exporting and saving the final image
    final_clip = CompositeVideoClip([base_image_clip,songList])
    final_clip.save_frame(baseImageTextNoArrowPath)
    
    #Calculating actual start point of text, and therefore start point of arrow
    #Because top half of the first blank line is cut off 
    #Note: this may no longer be true with the new version of moviepy, I tweaked something somewhere and have no idea how the math works now 
    y_position = (1080 - (len(metadataList)*arrowOffset)) / 2
    
    return (y_position, arrow_image_clip)
'''
Function that creates an array of images 
With each image having an arrow pointing to the respective song
y_position should be the start point of the first arrow 
'''
def addArrowsToImages(x_position, y_position,
                    arrow_image_clip,
                    metadataList):
    
    print("Creating images with arrows...")
    base_image_clip = ImageClip(baseImageTextNoArrowPath)

    arrowOffset = arrow_image_clip.h
    arrowWidth = arrow_image_clip.w
    
    #x_position of the arrow 
    x_position = x_position - arrowWidth - 15
    
    #Creating the images and updating the arrowImages array 
    arrowImages = []
    i = 1
    
    for song in metadataList:
        arrow_image_clip = arrow_image_clip.with_position((x_position,y_position))
        
        imageWithArrow = CompositeVideoClip([base_image_clip,arrow_image_clip])
        file = "imageWithArrow"+str(i)+".png"
        
        i+=1
        
        imageWithArrow.save_frame(file)
        
        arrowImages.append(file)
        
        #Calculating arrow position with course correction
        #While calculating y position, floats are truncated, leading to smaller than actual values
        if (8<i<12):
            y_position = y_position + arrowOffset + 1
        else:
            y_position = y_position + arrowOffset
    
    return (arrowImages)
'''
Function that concatenates the downloaded mp3's and the downloaded images with arrows
Into a single mp4 file and exports 
'''
def mergeFiles (arrowImages,metadataList, playlist_name):
    
    videoclips = []
    i = 0
    
    #Creating an array of videoclips with the correct audio and image(with arrow)
    print ("Creating videoclips...")  
    for song in metadataList:
        #Extract appropriate information 
        songpath = song["filename"]
        duration = song["duration"]
        arrowImagePath = arrowImages[i]
        i+=1
        
        #Create image and audio clip 
        audio_clip = AudioFileClip(songpath)
        image_clip = ImageClip(arrowImagePath).with_duration(duration)
        
        #Create and append video clip 
        video_clip = image_clip.with_audio(audio_clip)
        video_clip = video_clip.with_fps(1)
        videoclips.append(video_clip)
    
    print ("Concatenating and exporting final videoclip.")
    #Concatenate and export final videoclip using videoclips array     
    final_video_clip = concatenate_videoclips(videoclips, method="compose")
    final_video_clip.write_videofile(
        playlist_name+"vid"+".mp4",
        codec = 'mpeg4',
        audio_codec = 'aac',
        bitrate='5000k',
        audio_bitrate='4000k', #high bitrate chosen to prioritize audio quality 
        temp_audiofile = 'temp-audio.m4a', 
        remove_temp = True 
        )

# Function that prints the timestamp of each song in an object metadataList (not relevant to rest of code)
def printTimestampsList (metadataList):     
    for x in metadataList:
        songname = x["songname"]
        timestamp = x["timestamp"]
        playlistposition = x["playlistposition"]
        
        minutes = timestamp // 60
        seconds = timestamp % 60
        
        print(f"{playlistposition}. {minutes}:{seconds:02d} - {songname} by {x['artists']}")


    print ("Spotify link: "+ playlistlink)
    print ("We now have a discord! We now have a discord! https://discord.gg/fmkVDa4MBG")
    print ("If you want to support what I do, you can donate on kofi, which is basically like a tip jar because none of my content is monetizable. Anything is appreciated! https://ko-fi.com/rogueskye")


def cleanWorkspace (metadataList, arrowImages):
    print ("Deleting unnecessary files...")
    for song in metadataList:
        file = song["filename"]
        os.remove(file)
        
    for file in  arrowImages:
        os.remove(file)
        
    os.remove(baseImageTextNoArrowPath)
    print ("Finished.")

'''
Function that gets the playlist link from the user
Reads the last-used link from a text file to use as the default
Pressing enter with no input reuses the default, otherwise validates and saves the new link
'''
def validateSpotifyLink():
    defaultLinkPath = os.getcwd()+r"\resources\defaultPlaylist.txt"

    #Read the last-used link from the file to use as the default
    with open(defaultLinkPath, "r", encoding="utf-8") as f:
        defaultLink = f.read().strip()

    # Regular expression for Spotify playlist links
    pattern = r"^https://open\.spotify\.com/playlist/[a-zA-Z0-9]+(\?si=[a-zA-Z0-9]+)?$"

    Flag = False
    while not Flag:
        playlistlink = input(f"Input the playlist link (press enter for default/previous link): ")

        if len(playlistlink.strip()) == 0:
            playlistlink = defaultLink

        playlistlink = playlistlink.strip()

        if re.match(pattern, playlistlink):
            Flag = True
        else:
            print("Invalid playlist link. Please try again.")

    #Save the chosen link back to the file so it becomes the default next run
    with open(defaultLinkPath, "w", encoding="utf-8") as f:
        f.write(playlistlink)

    return playlistlink

'''
Function that gets the image path from the user
Pressing enter with no input uses the default image
Validates the path and file type, then saves the choice as the new default for next run
'''
def validateImagePath(defaultImage):
    Flag = False
    while not Flag:
        image_path = input("Input the path to the image (press enter for default/previous image): ")
        if (image_path == None or len(image_path) == 0):
            image_path = defaultImage

        # Strip whitespace
        image_path = image_path.strip()

        # Strip surrounding quotes if present (both " and ')
        if len(image_path) >= 2 and image_path[0] in ('"', "'") and image_path[-1] == image_path[0]:
            image_path = image_path[1:-1]

        if os.path.isfile(image_path) and image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            Flag = True
        else:
            print("Invalid image path. Please try again.")

    # Save the chosen image as the new default for next run.
    # Skip if the user just reused the existing default (avoids SameFileError).
    if os.path.abspath(image_path) != os.path.abspath(defaultImage):
        shutil.copyfile(image_path, defaultImage)

    return image_path
    

if __name__ == '__main__':
    #Static variables
    x_position = 1260 #Maybe take this as an input as well, depending on where the actual image is
    arrowImagePath = os.getcwd()+r"\resources\right-arrow.png"
    defaultImage = os.getcwd()+r"\resources\defaultImage.png"
    
    # Variables to collect from the user
    playlistlink = validateSpotifyLink()
    image_path = validateImagePath(defaultImage)
    playlist_name = str(input(r"Input the playlist name: "))
    
    # Setup spotDl
    spotdl = Spotdl(CLIENT_ID, CLIENT_SECRET)
    
    # Download songs and create list of metadata 
    #try/except this as well? 
    metadataList = spotifyDownload(spotdl, playlistlink)
    
    #Creates a base image with no arrows
    #Returns top y position of the text box, and image clip object of arrow
    
    y_position, arrow_image_clip = addTextToImage(x_position, arrowImagePath, metadataList, image_path)
    
    #Creates an array of image clips 
    #With an arrow pointing to the appropriate song 
    arrowImages = addArrowsToImages(x_position, y_position, arrow_image_clip, metadataList)
    
    #Merges the image clips and the audio clips together
    mergeFiles(arrowImages,metadataList, playlist_name)

    #Prints timestamps
    printTimestampsList(metadataList)
    
    #Deleting the unnecessary files from the workspace
    cleanWorkspace(metadataList, arrowImages) 
         
    exit(0)
