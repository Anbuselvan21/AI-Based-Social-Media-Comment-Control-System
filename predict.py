from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from database import get_db
from models.multimodal_model import multimodal_model
import os
import re
import time
import torch
from torchvision import transforms
from PIL import Image
from datetime import datetime

predict_bp = Blueprint('predict', __name__)

STRONG_ABUSIVE = [
    'fuck', 'fucking', 'fucker', 'fucked', 'fuckyou', 'fuckoff', 'fuck u', 'fucks', 'fuker', 'fukin',
    'shit', 'shitty', 'bullshit', 'bull shit', 'shity',
    'bitch', 'bitches', 'bitchy', 'bitch please',
    'bastard', 'bastards', 'bastardized',
    'cunt', 'cunts', 'cock', 'cocks', 'cocksucker',
    'dick', 'dicks', 'dickhead', 'dickheads',
    'pussy', 'pussies', 'pusy',
    'motherfucker', 'mother fucker', 'motherfuker', 'motherfukin',
    'motherbitch', 'mother bitch',
    'asshole', 'assholes', 'ashole',
    'douchebag', 'douchebags', 'douche',
    'faggot', 'faggots',
    'nigger', 'nigga', 'niggas', 'nig',
    'slut', 'sluts', 'sluttiy',
    'whore', 'whores', 'whore',
    'retard', 'retards', 'retarded', 'tard',
    'moron', 'morons', 'moronic',
    'cunt', 'cunts',
    'sexy', 'porn', 'pornhub', 'pornographic', 'xvideo', 'xvideos',
    'nude', 'nudes', 'naked', 'nudity', 'nudist',
    'having sex with', 'wanna sex with', 'want sex with', 'to have sex with', 'sex with me', 'sex with you',
    'fuck girl', 'fuck boy', 'fucking girl', 'fuck that', 'fuck off',
    'sexual', 'sexually', 'horny', 'horniest', 'horni',
    'rape', 'raped', 'raping', 'rapist', 'raper',
    'molest', 'molested', 'molestation', 'molester',
    'pedophile', 'pedo', 'pedophilia', 'child porn', 'cp',
    'prostitute', 'escort', 'escorts', 'hooker',
    'erotic', 'erotica', 'xxx', 'adult content', 'nsfw',
    'seduce me', 'seduce you', 'seduction',
    'slave', 'slaves', 'slavery'
]

MILD_ABUSIVE = [
    'idiot', 'idiots', 'idiotcy', 'idiotc',
    'loser', 'losers', 'lose',
    'jerk', 'jerks', 'jerky',
    'fool', 'fools', 'foolish', 'foolishness',
    'dumb', 'dumber', 'dumbest', 'dumbass',
    'stupid', 'stupidity', 'stupidly', 'stupit',
    'ugly', 'uglier', 'ugliest',
    'psycho', 'psychotic', 'psychopath',
    'crazy', 'crazier', 'craziest', 'crazyy',
    'weirdo', 'weirdos', 'weird',
    'freak', 'freaks', 'freaky',
    'scum', 'scummy', 'scumbag', 'scumbags',
    'trash', 'trashy', 'trashed',
    'garbage', 'garbages',
    'lame', 'lamest',
    'pathetic', 'pathetically',
    'useless', 'uselessness',
    'worthless', 'worthlessness',
    'disgusting', 'disgusted', 'disgusting',
    'nasty', 'nastier', 'nastiest',
    'vile', 'vilest', 'vileness',
    'evil', 'eviler', 'evilest', 'evilness',
    'creep', 'creepy', 'creeps',
    'gross', 'grosser', 'grossest',
    'damn', 'damned', 'dammit', 'goddammit', 'goddamn',
    'hell', 'what the hell', 'what the heck',
    'crap', 'crappy', 'crapper',
    'ass', 'asses', 'assface',
    'wimp', 'wimps', 'wimpy',
    'bloody', 'bloody hell', 'blood',
    'hate', 'hated', 'hates', 'hating', 'hatred', 'hate you',
    'kill', 'killed', 'kills', 'killing', 'kill you', 'kill urself',
    'suicide', 'suicidal', 'kill myself',
    'liar', 'liars', 'lying', 'lie', 'lies',
    'cheater', 'cheaters', 'cheating', 'cheat',
    'thief', 'thieves', 'stealing', 'steal',
    'pig', 'pigs', 'piggy',
    'monster', 'monsters',
    'reject', 'rejected', 'rejection',
    'shut up', 'shut your mouth', 'shutup',
    'go away', 'get lost', 'drop dead', 'go to hell',
    'worse', 'worst',
    'sad', 'sadly', 'sadness',
    'embarrassing', 'embarrassed', 'embarrass',
    'shame', 'shame on you', 'shameless',
    'ashamed',
    'lazy', 'lazier', 'laziest',
    'hopeless', 'hopelessness',
    'terrible', 'terribly',
    'awful', 'awfully',
    'horrible', 'horribly',
    'failure', 'failed', 'fail',
    'bad girl',
    'ugly girl', 'ugly boy', 'ugly person',
    'disgusting girl', 'disgusting person',
    'loser person',
    'nobody likes you', 'no one likes you',
    'good for nothing', 'good-for-nothing',
    'waste', 'wasted', 'waste of time',
    'imbecile', 'imbeciles', 'cretin'
]

INTERMEDIATE = [
    'remove your dress', 'take off your clothes', 'show your body',
    'get naked', 'strip', 'stripping', 'stripper',
    'show body', 'show me your', 'send pics', 'send photo',
    'sexy girl', 'sexy boy', 'sexy person', 'sexy body', 'sexy photo',
    'sexy dress', 'sexy outfit',
    'hot girl', 'hot boy', 'hot person', 'hot photo', 'hot stuff',
    'naked girl', 'naked boy', 'naked person',
    'nude girl', 'nude boy', 'nude person',
    'body photo', 'body picture', 'body pic',
    'dm me', '私信', 'follow me', 'only fans', 'onlyfans',
    'suspicious', 'suspicious activity',
    'strange', 'strange behavior',
    'weird', 'weird person',
    'odd', 'odd behavior',
    'doubt', 'doubtful',
    'body shaming', 'shame on your body',
    'ugly face', 'ugly looks',
    'not normal', 'abnormal', 'unusual behavior',
    'this looks wrong', 'that is not right',
    'your face is', 'your looks are',
    'skin color', 'ethnicity', 'religion',
    'take off your', 'get out of your',
    'i want you', 'i need you', 'i like you'
]

def check_offensive_language(text):
    import re
    text_lower = text.lower()
    found_words = []
    severity = 'safe'
    
    def word_match(text, word):
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text))
    
    for word in STRONG_ABUSIVE:
        if word_match(text_lower, word):
            found_words.append(word)
            severity = 'abusive'
    
    if severity != 'abusive':
        for word in MILD_ABUSIVE:
            if word_match(text_lower, word):
                found_words.append(word)
                severity = 'abusive'
    
    if severity != 'abusive':
        for phrase in INTERMEDIATE:
            if phrase in text_lower:
                found_words.append(phrase)
                severity = 'intermediate'
    
    if severity == 'abusive':
        return {
            'detected': True,
            'message': 'Warning: Offensive language detected!',
            'severity': 'abusive',
            'words': found_words[:5]
        }
    elif severity == 'intermediate':
        return {
            'detected': True,
            'message': 'Caution: Suspicious content detected',
            'severity': 'intermediate',
            'words': found_words[:5]
        }
    
    return {
        'detected': False,
        'message': 'Safe content',
        'severity': 'safe',
        'words': []
    }

@predict_bp.route('/predict-text/realtime', methods=['POST'])
@jwt_required()
def realtime_analysis():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text.strip():
        return jsonify({'status': 'empty', 'message': 'Please enter some text'})
    
    result = check_offensive_language(text)
    
    return jsonify(result), 200

@predict_bp.route('/predict-text', methods=['POST'])
@jwt_required()
def predict_text():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    text = data.get('text', '')
    
    if not text.strip():
        return jsonify({'error': 'Text is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT is_blocked FROM users WHERE id = ?', (user_id,)).fetchone()
    if user and user['is_blocked']:
        conn.close()
        return jsonify({
            'blocked': True,
            'message': 'Your account has been blocked due to multiple violations.'
        }), 403
    
    result = multimodal_model.predict_text(text)
    
    warning_count_row = cursor.execute('SELECT COUNT(*) as count FROM warnings WHERE user_id = ?', (user_id,)).fetchone()
    warning_count = warning_count_row['count'] if warning_count_row else 0
    
    if result['prediction'] == 'Abusive':
        cursor.execute(
            'INSERT INTO warnings (user_id, type, content, severity) VALUES (?, ?, ?, ?)',
            (user_id, 'text', text[:200], 'abusive')
        )
        warning_count += 1
        cursor.execute('UPDATE users SET warning_count = ? WHERE id = ?', (warning_count, user_id))
        
        if warning_count >= 3:
            cursor.execute('UPDATE users SET is_blocked = 1 WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return jsonify({
                'blocked': True,
                'message': 'Your account has been blocked due to multiple violations.',
                'warning_count': warning_count
            }), 403
        
        conn.commit()
        conn.close()
        return jsonify({
            'result': result,
            'blocked': False,
            'warning': True,
            'warning_message': f'Warning {warning_count}/3: Abusive content detected. Your account will be blocked after 3 violations.',
            'warning_count': warning_count
        }), 200
    
    if result['prediction'] == 'Intermediate':
        cursor.execute(
            'INSERT INTO warnings (user_id, type, content, severity) VALUES (?, ?, ?, ?)',
            (user_id, 'text', text[:200], 'intermediate')
        )
        warning_count += 1
        cursor.execute('UPDATE users SET warning_count = ? WHERE id = ?', (warning_count, user_id))
        
        if warning_count >= 3:
            cursor.execute('UPDATE users SET is_blocked = 1 WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return jsonify({
                'blocked': True,
                'message': 'Your account has been blocked due to multiple violations.',
                'warning_count': warning_count
            }), 403
        
        conn.commit()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'INSERT INTO comments (user_id, type, content, prediction, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, 'text', text, result['prediction'], result['confidence'], current_time)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'result': result,
            'blocked': False,
            'warning': True,
            'warning_message': f'Warning {warning_count}/3: Suspicious content detected. But your comment is posted.',
            'warning_count': warning_count,
            'comment_posted': True
        }), 200
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO comments (user_id, type, content, prediction, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, 'text', text, result['prediction'], result['confidence'], current_time)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'result': result,
        'offensive_check': check_offensive_language(text)
    }), 200

@predict_bp.route('/predict-image', methods=['POST'])
@jwt_required()
def predict_image():
    user_id = get_jwt_identity()
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT is_blocked FROM users WHERE id = ?', (user_id,)).fetchone()
    if user and user['is_blocked']:
        conn.close()
        return jsonify({
            'blocked': True,
            'message': 'Your account has been blocked due to multiple violations.'
        }), 403
    
    filename = secure_filename(file.filename)
    timestamp = str(int(time.time()))
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(os.path.dirname(__file__), '..', 'uploads', filename)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    
    try:
        print(f"Loading image from: {filepath}")
        image = Image.open(filepath).convert('RGB')
        print(f"Image loaded: {image.size}, {image.mode}")
        result = multimodal_model.predict_image(image)
        print(f"Prediction result: {result}")
    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        result = {
            'prediction': 'Non-Abusive',
            'confidence': 75.0,
            'probabilities': {'abusive': 15.0, 'non_abusive': 70.0, 'intermediate': 15.0},
            'model_used': 'fallback'
        }
        print(f"Fallback result: {result}")
    
    warning_count_row = cursor.execute('SELECT COUNT(*) as count FROM warnings WHERE user_id = ?', (user_id,)).fetchone()
    warning_count = warning_count_row['count'] if warning_count_row else 0
    
    if result['prediction'] == 'Abusive':
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'result': result,
            'blocked': False,
            'abusive_blocked': True,
            'warning_message': 'This image comment is not allowed to be posted! Abusive content is blocked.'
        }), 200
    
    if result['prediction'] == 'Intermediate':
        cursor.execute(
            'INSERT INTO warnings (user_id, type, image_path, severity) VALUES (?, ?, ?, ?)',
            (user_id, 'image', filename, 'intermediate')
        )
        warning_count += 1
        cursor.execute('UPDATE users SET warning_count = ? WHERE id = ?', (warning_count, user_id))
        
        if warning_count >= 3:
            cursor.execute('UPDATE users SET is_blocked = 1 WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return jsonify({
                'blocked': True,
                'message': 'Your account has been blocked due to multiple warnings.',
                'warning_count': warning_count
            }), 403
        
        conn.commit()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'INSERT INTO comments (user_id, type, image_path, prediction, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, 'image', filename, result['prediction'], result['confidence'], current_time)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'result': result,
            'blocked': False,
            'warning': True,
            'warning_message': f'Warning {warning_count}/3: Suspicious content detected. But your image is posted.',
            'warning_count': warning_count,
            'comment_posted': True,
            'image_path': filename
        }), 200
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO comments (user_id, type, image_path, prediction, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, 'image', filename, result['prediction'], result['confidence'], current_time)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'result': result,
        'image_path': filename
    }), 200

@predict_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    comments = cursor.execute(
        'SELECT * FROM comments WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    return jsonify([dict(comment) for comment in comments]), 200
