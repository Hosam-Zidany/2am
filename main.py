import os
import yt_dlp
import instaloader
from dotenv import load_dotenv
import requests
import shutil
import random
from pytube import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters


load_dotenv()  # loads environment variables from .env file

TOKEN = os.getenv('TOKEN')
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0'
]

proxies = {
    'http': 'http://172.67.207.121:80',
    'https': 'https://13.40.239.130:1080'
}


async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Send me a link to download the video or photo!')

async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    if not is_valid_url(url):
        return  # Do not send any response if the message is not a valid link
    if "reel" in url.lower():
        await download_video(url, update.effective_chat.id, context)
    elif "youtube" in url.lower() or "youtu.be"in url.lower():
        await download_youtube_video(url, update.effective_chat.id, context)
    else:
        await download_images(url, update.effective_chat.id, context)

def is_valid_url(url):
    # Basic URL validation (you can improve this)
    return url.startswith('http://') or url.startswith('https://')

async def download_video(url, chat_id, context):
    file_name = None
    try:
        # Set up yt-dlp options for video
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Download best video and audio
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # Save to downloads folder
            'noplaylist': True,  # Download only single video
        }

        # Create downloads directory if it doesn't exist
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Download the media
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        # Send the video file
        with open(file_name, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)

        # Clean up the file after sending
        if file_name and os.path.exists(file_name):
            os.remove(file_name)
            shutil.rmtree('downloads')
            os.makedirs('downloads')  # Recreate the downloads directory
    except Exception as e:
        print(f"An error occurred while downloading media: {e}")
        await context.bot.send_message(chat_id=chat_id, text='An error occurred while downloading the media.')
async def download_images(url, chat_id, context):
    # Create an instance of Instaloader
    loader = instaloader.Instaloader()

    # Extract the shortcode from the URL
    shortcode = url.split("/")[-2]

    try:
        # Create downloads directory if it doesn't exist
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Download the post using the shortcode
        loader.download_post(instaloader.Post.from_shortcode(loader.context, shortcode), target='downloads')

        # Check the downloads directory for image files
        await check_and_send_images(chat_id, context)
    except Exception as e:
        print(f"An error occurred while downloading images: {e}")
        await context.bot.send_message(chat_id=chat_id, text='An error occurred while downloading images.')


async def download_youtube_video(url, chat_id, context):
    try:
        # Create downloads directory if it doesn't exist
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        # Set a random User-Agent header
        user_agent = random.choice(user_agents)
        headers = {'User-Agent': user_agent}

        # Fetch the YouTube video page with our custom headers and proxy server
        response = requests.get(url, headers=headers, proxies=proxies)

        # Parse the HTML and extract the video URL
        yt = YouTube(url)

        # Download the video
        video_stream = yt.streams.get_highest_resolution()  # Get the highest resolution stream
        file_name = video_stream.download(output_path='downloads')

        # Send the video file
        with open(file_name, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)

        # Clean up the file after sending
        if os.path.exists(file_name):
            os.remove(file_name)
    except Exception as e:
        print(f"An error occurred while downloading YouTube video: {e}")
        await context.bot.send_message(chat_id=chat_id, text='An error occurred while downloading the YouTube video.')
async def check_and_send_images(chat_id, context):
    # Check the downloads directory for image files and send them
    for filename in os.listdir('downloads'):
        if filename.endswith(('.jpg', '.jpeg', '.png')):  # Check for image file extensions
            file_path = os.path.join('downloads', filename)
            with open(file_path, 'rb') as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo)
                shutil.rmtree('downloads')
                os.makedirs('downloads')  # Recreate the downloads directory

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
