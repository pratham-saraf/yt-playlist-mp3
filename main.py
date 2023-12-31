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
from fastapi.middleware.cors import CORSMiddleware




origins = ["*"]


active_connections = []

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

class PlaylistData(BaseModel):
   url: str

@app.get("/", response_class=FileResponse)
def read_root():
   return FileResponse("index.html")

@app.post("/download_playlist")
async def download_playlist(data: PlaylistData ):
    print("got a req")
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        playlist = Playlist(data.url)


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
        zip_path = os.path.join(temp_dir, 'playlist.zip')
        with ZipFile(zip_path, 'w') as zip_file:
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    zip_file.write(os.path.join(temp_dir, file), file)

        with open(zip_path, "rb") as f:
            zip_bytes = f.read()

        # remove the temp directory
        shutil.rmtree(temp_dir)

        return Response(content=zip_bytes, media_type="application/zip")

    except Exception as e:
        raise HTTPException(status_code=493, detail=str(e))

if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='0.0.0.0')

