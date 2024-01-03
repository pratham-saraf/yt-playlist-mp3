import os
import uvicorn
import tempfile
from zipfile import ZipFile
import shutil
from fastapi import  FastAPI, HTTPException 
from fastapi.responses import Response , FileResponse
from pytube import Playlist, YouTube
from moviepy.editor import AudioFileClip
from pydantic import BaseModel
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import hashlib

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def delete_all_content_in_directory(directory_path):
  """Deletes all content in a directory.

  Args:
    directory_path: The path to the directory to delete all content in.
  """

  for file in os.listdir(directory_path):
    file_path = os.path.join(directory_path, file)
    if os.path.isfile(file_path):
      os.unlink(file_path)
    elif os.path.isdir(file_path):
      shutil.rmtree(file_path)

class PlaylistData(BaseModel):
    url: str

@app.get("/", response_class=FileResponse)
def read_root():
   return FileResponse("index.html")

@app.post("/download_playlist")
async def download_playlist(data: PlaylistData, background_tasks: BackgroundTasks):
    print("got a req")

    # Add the download_and_convert function as a background task
    background_tasks.add_task(download_and_convert, data.url)

    return {"message": "Download and conversion started"}

async def download_and_convert(url: str):
    print("download started")
    # delete everything inside downloads folder first
    delete_all_content_in_directory("./downloads")
    try:
        # Create a temporary directory
        url_hash = hashlib.md5(url.encode()).hexdigest()
        temp_dir = "./downloads/" + str(url_hash)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.mkdir(temp_dir)  # remove dir if it already exists
        else:
            os.mkdir(temp_dir)
        
        print(temp_dir)

        playlist = Playlist(url)

        # Download each video from the playlist
        for url in playlist.video_urls:
            video = YouTube(url)
            stream = video.streams.filter(only_audio=True).first()
            stream.download(temp_dir)
        
        # Convert MP4 files to MP3
            for file in os.listdir(temp_dir):
                if file.endswith('.mp4'):
                    mp4_path = os.path.join(temp_dir, file)
                    mp3_path = os.path.join(temp_dir, os.path.splitext(file)[0] + '.mp3')
                    audio_clip = AudioFileClip(mp4_path)
                    audio_clip.write_audiofile(mp3_path)
                    os.remove(mp4_path)

        # Create a Zip file
        zip_path = './downloads/' + url_hash + '/playlist.zip'
        with ZipFile(zip_path, 'w') as zip_file:
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    zip_file.write(os.path.join(temp_dir, file), file)

        # remove all mp3 files
        for file in os.listdir(temp_dir):
            if file.endswith('.mp3'):
                os.remove(os.path.join(temp_dir, file))

    except Exception as e:
        print(f"An error occurred: {e}")

@app.get("/download_file/{url:path}")
async def download_file(url: str):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    path = './downloads/' + url_hash + "/playlist.zip"
    if Path(path).exists():
        response = FileResponse(path)
        # remove the zip file after it has been read
        # os.remove(path)
        return response
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/health" , status_code=200)
def health_check():
    return True

if __name__ == '__main__':
    uvicorn.run(app,  host='0.0.0.0')
