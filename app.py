from flask import Flask, render_template, request
import cv2
from deepface import DeepFace
import time
import requests
from bs4 import BeautifulSoup
import regex as re

app = Flask(__name__)

face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
video_duration = 5  # in seconds

def fetch_movies_from_imdb(emotion):
    genre_mapping = {
        'sad': 'comedy',
        'disgust': 'musical',
        'angry': 'family',
        'neutral': 'drama',
        'fear': 'sport',
        'happy': 'thriller',
        'surprised': 'film_noir'
    }

    genre = genre_mapping.get(emotion)
    print(genre)
    movie_data = []
    if genre:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, likeGecko) Chrome/102.0.0.0 Safari/537.36'}
        response = requests.get(f'https://www.imdb.com/search/title/?title_type=feature&genres={genre}&sort=alpha,asc',headers=headers)
        soup = BeautifulSoup(response.content, 'lxml')
        movie_titles = soup.find_all('h3', class_='ipc-title__text')
        movie_ratings = soup.find_all('span', class_='ipc-rating-star ipc-rating-star--base ipc-rating-star--imdb ratingGroup--imdb-rating')
        movie_image = soup.find_all("img", class_='ipc-image')
        image_src_list = []
        for img_tag in movie_image:
            if 'src' in img_tag.attrs:
                image_src_list.append(img_tag['src'])
        print(image_src_list)
        for i in range(min(len(movie_titles), min(len(movie_ratings),len(image_src_list)))):
            title = movie_titles[i].text
            rating = movie_ratings[i].text
            images = image_src_list[i]
            # names=movie_image[i]['loadlate']
            movie_data.append({'title': title, 'image': images, 'rating': rating})
        return movie_data

        
        # for title, rating,image, in zip(movie_titles, movie_ratings,movie_image):
        #     movie_data.append({'title': title.text.strip(), 'rating': rating.text.strip(),'image':image.text.strip()})
    else :
        print("hello")
        
    
        # return movie_data

    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_emotion', methods=['POST'])
def analyze_emotion():
    emotions = []

    cap = cv2.VideoCapture(0)
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
            face_img = frame[y:y+h, x:x+w]
            
            _, img_encoded = cv2.imencode('.jpg', face_img)
            img_bytes = img_encoded.tobytes()
            img_path = 'temp.jpg'
            with open(img_path, 'wb') as f:
                f.write(img_bytes)
            
            result = DeepFace.analyze(img_path=img_path, actions=['emotion'], enforce_detection=False)

            dominant_emotion =(result[0]["dominant_emotion"][:])
            emotions.append(dominant_emotion)

            txt = "Emotion: " + dominant_emotion

            cv2.putText(frame, txt, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow('frame', frame)

        if time.time() - start_time >= video_duration:
            break

        if cv2.waitKey(1) & 0xff == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    most_common_emotion = max(set(emotions), key=emotions.count)

    movie_data = fetch_movies_from_imdb(most_common_emotion)

    return render_template('result.html', emotion=most_common_emotion, movies=movie_data)

if __name__ == '__main__':
    app.run()
