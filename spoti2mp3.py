import os
import time
import yt_dlp
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy


# spotify api 
SPOTIPY_CLIENT_ID = 'id'
SPOTIPY_CLIENT_SECRET = 'secret'

# ffmpeg 
FFMPEG_LOCATION = r'ffmpeg'

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID, 
    client_secret=SPOTIPY_CLIENT_SECRET
))

def download_song(track_name, output_path, use_proxy=False):
    print(f"Searching for: {track_name}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'ffmpeg_location': FFMPEG_LOCATION,
        'noplaylist': True,
        'ignoreerrors': True,
    }
    
    if use_proxy:
        print("err451 - Using alternative method to bypass restrictions...")
        ydl_opts.update({
            'nocheckcertificate': True,
            'age_limit': 99,
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{track_name}", download=False)
            if info and 'entries' in info and info['entries']:
                entry = info['entries'][0]
                if entry:
                    print(f"Found: {entry.get('title', 'Unknown title')}")
                    ydl.download([entry['webpage_url']])
                    print(f"201 - Successfully downloaded: {track_name}")
                    return True
            
        if not use_proxy:
            print("err502 – Standard download failed. Trying alternative method...")
            return download_song(track_name, output_path, True)
        else:
            print(f"err422 - Automatic search failed for: {track_name}")
            manual = input("Would you like to manually enter a YouTube URL for this song? (y/n): ")
            if manual.lower() == 'y':
                url = input("Enter YouTube URL: ")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                print(f"201 - Successfully downloaded from manual URL")
                return True
            
            retry = input("Would you like to retry with a different search term? (y/n): ")
            if retry.lower() == 'y':
                new_term = input(f"Enter new search term for '{track_name}': ")
                return download_song(new_term, output_path, False)
            return False
            
    except Exception as e:
        print(f"err502 - Error downloading {track_name}: {str(e)}")
        retry = input("Would you like to retry with a different search term? (y/n): ")
        if retry.lower() == 'y':
            new_term = input(f"Enter new search term for '{track_name}': ")
            return download_song(new_term, output_path, False)
        return False

def get_spotify_playlist_tracks(playlist_url):
    try:
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        
        for item in results['items']:
            if item['track']:
                tracks.append(item['track'])
        
        while results['next']:
            results = sp.next(results)
            for item in results['items']:
                if item['track']:
                    tracks.append(item['track'])
                    
        return tracks
    except Exception as e:
        if "cache" in str(e).lower():
            print("err214 - Note: Spotify cache warning - this is normal and won't affect functionality")
        else:
            print(f"err500 - Error fetching playlist: {str(e)}")
        
        if tracks:
            return tracks
        
        return []

def get_spotify_track_info(track_url):
    try:
        track_id = track_url.split('/')[-1].split('?')[0]
        track = sp.track(track_id)
        return track
    except Exception as e:
        print(f"err500 - Error fetching track info: {str(e)}")
        return None

def main():
    print("=== Spotify to MP3 Downloader ===")
    print("1. Download playlist")
    print("2. Download single track")
    
    choice = input("Select an option (1/2): ")
    
    output_path = input("Enter download directory path: ")
    if not os.path.exists(output_path):
        create_dir = input(f"Directory '{output_path}' doesn't exist. Create it? (y/n): ")
        if create_dir.lower() == 'y':
            os.makedirs(output_path)
        else:
            print("Download canceled.")
            return
    
    if choice == "1":
        playlist_url = input("Enter Spotify playlist URL: ")
        tracks = get_spotify_playlist_tracks(playlist_url)
        
        if not tracks:
            print("err404 - No tracks found in playlist or invalid playlist URL.")
            return
            
        print(f"Found {len(tracks)} tracks in playlist.")
        download_all = input(f"Download all {len(tracks)} tracks? (y/n): ")
        
        if download_all.lower() != 'y':
            start_idx = int(input("Start from which track number? (1 to start from beginning): ")) - 1
            end_idx = int(input(f"End at which track number? (1-{len(tracks)}): "))
            tracks = tracks[max(0, start_idx):min(len(tracks), end_idx)]
        
        downloaded = 0
        skipped = 0
        
        for index, track in enumerate(tracks):
            if track is None or 'name' not in track or 'artists' not in track:
                print(f"err422 - Skipping track at position {index+1} (invalid track data)")
                skipped += 1
                continue
                
            track_name = f"{track['name']} - {track['artists'][0]['name']}"
            print(f"\nProcessing {index+1}/{len(tracks)}: {track_name}")
            
            if download_song(track_name, output_path):
                downloaded += 1
            else:
                skipped += 1
            
            if (index + 1) % 5 == 0 and index + 1 < len(tracks):
                print("429 - Pausing for 5 seconds to avoid rate limiting...")
                time.sleep(5)
        
        print(f"\n200 - Download complete! Downloaded: {downloaded}, Skipped: {skipped}")
        
    elif choice == "2":
        track_url = input("Enter Spotify track URL: ")
        track = get_spotify_track_info(track_url)
        
        if track and 'name' in track and 'artists' in track:
            track_name = f"{track['name']} - {track['artists'][0]['name']}"
            print(f"Found track: {track_name}")
            download_song(track_name, output_path)
        else:
            print("err404 - Invalid track URL or track not found.")
    else:
        print("err400 - Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nerr499 - Download canceled by user.")
    except Exception as e:
        print(f"err500 - An unexpected error occurred: {str(e)}")
    finally:
        input("\nPress Enter to exit...")