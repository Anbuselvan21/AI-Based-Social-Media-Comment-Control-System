import re
import torch
import torch.nn as nn
import os

class TextClassifier(nn.Module):
    def __init__(self, vocab_size=30522, embed_dim=128, num_labels=3):
        super(TextClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.conv1 = nn.Conv1d(embed_dim, 128, 5)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc1 = nn.Linear(128, 64)
        self.fc2 = nn.Linear(64, num_labels)
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, x):
        x = self.embedding(x)
        x = x.permute(0, 2, 1)
        x = torch.relu(self.conv1(x))
        x = self.pool(x).squeeze(-1)
        x = self.dropout(x)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class TextModel:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cpu')
        self.initialized = False
        self.model_loaded = False
        
        self.strong_abusive = [
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
            'whore', 'whores',
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
            'slave', 'slaves', 'slavery',
            'bollocks', 'bollocks',
            'wanker', 'twat', 'slag', 'scumbag', 'scumbags',
            'gobshite', 'pillock', 'bellend', 'tosser', 'nonce',
            'kike', 'spic', 'chink'
        ]
        
        self.mild_abusive = [
            'idiot', 'idiots', 'idiotcy', 'idiotc',
            'loser', 'losers', 'lose',
            'jerk', 'jerks', 'jerky',
            'fool', 'fools', 'foolish', 'foolishness',
            'dumb', 'dumber', 'dumbest', 'dumbass', 'dumbasses',
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
            'disgusting', 'disgusted',
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
            'bloody', 'bloody hell',
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
            'embarrassing', 'embarrassed',
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
        
        self.intermediate = [
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
        
    def initialize(self):
        if self.initialized:
            return
        
        model_path = os.path.join(os.path.dirname(__file__), 'final_multimodal_model.pth')
        
        try:
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                
                self.model = TextClassifier(num_labels=3)
                
                if isinstance(checkpoint, dict):
                    if 'model_state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                    elif 'state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['state_dict'])
                    else:
                        self.model.load_state_dict(checkpoint)
                else:
                    self.model.load_state_dict(checkpoint)
                
                self.model.to(self.device)
                self.model.eval()
                self.model_loaded = True
                print("Loaded final_multimodal_model.pth for text prediction!")
                self.initialized = True
                return
        except Exception as e:
            print(f"Could not load multimodal model for text: {e}")
        
        self.model = TextClassifier(num_labels=3)
        self.model.to(self.device)
        self.model.eval()
        self.model_loaded = False
        self.initialized = True
        print("Using rule-based text classifier")
        
    def predict(self, text):
        self.initialize()
        
        text_lower = text.lower()
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        words = text_clean.split()
        
        strong_count = 0
        mild_count = 0
        intermediate_count = 0
        
        found_strong = []
        found_mild = []
        found_intermediate = []
        
        for word in self.strong_abusive:
            if word in text_lower:
                strong_count += 1
                if word not in found_strong:
                    found_strong.append(word)
        
        for word in self.mild_abusive:
            if word in text_lower:
                mild_count += 1
                if word not in found_mild:
                    found_mild.append(word)
        
        for phrase in self.intermediate:
            if phrase in text_lower:
                intermediate_count += 1
                if phrase not in found_intermediate:
                    found_intermediate.append(phrase)
        
        if strong_count >= 1:
            prediction = 'Abusive'
            confidence = min(98, 80 + strong_count * 10)
            abusive_prob = min(98, 80 + strong_count * 5)
            non_abusive_prob = max(2, 20 - strong_count * 2)
        elif mild_count >= 2:
            prediction = 'Abusive'
            confidence = min(95, 70 + mild_count * 8)
            abusive_prob = min(95, 65 + mild_count * 5)
            non_abusive_prob = max(5, 35 - mild_count * 3)
        elif intermediate_count >= 1:
            prediction = 'Intermediate'
            confidence = min(90, 55 + intermediate_count * 10)
            abusive_prob = min(60, 30 + intermediate_count * 10)
            non_abusive_prob = max(20, 50 - intermediate_count * 5)
        elif mild_count >= 1:
            prediction = 'Intermediate'
            confidence = min(85, 50 + mild_count * 10)
            abusive_prob = min(55, 25 + mild_count * 10)
            non_abusive_prob = max(25, 50 - mild_count * 8)
        else:
            prediction = 'Non-Abusive'
            confidence = 75
            abusive_prob = 10
            non_abusive_prob = 80
        
        intermediate_prob = max(5, 100 - abusive_prob - non_abusive_prob)
        
        return {
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'probabilities': {
                'abusive': round(max(5, abusive_prob), 2),
                'non_abusive': round(max(5, non_abusive_prob), 2),
                'intermediate': round(max(5, intermediate_prob), 2)
            },
            'detected_words': found_strong[:5] if found_strong else found_intermediate[:5] if found_intermediate else found_mild[:5] if found_mild else [],
            'model_used': 'multimodal' if self.model_loaded else 'rule_based'
        }

text_model = TextModel()
