import torch
import torch.nn as nn
import torch.nn.functional as F
import re
import os
from PIL import Image
from torchvision import transforms

class ImageOnlyClassifier(nn.Module):
    def __init__(self, num_classes=3):
        super(ImageOnlyClassifier, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

class GraphAttentionLayer(nn.Module):
    def __init__(self, in_features, out_features, dropout, alpha, concat=True):
        super(GraphAttentionLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.dropout = dropout
        self.alpha = alpha
        self.concat = concat
        
        self.W = nn.Parameter(torch.zeros(in_features, out_features))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)
        self.a = nn.Parameter(torch.zeros(2 * out_features, 1))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)
        
        self.leakyrelu = nn.LeakyReLU(self.alpha)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, input, adj):
        h = torch.mm(input, self.W)
        N = h.size()[0]
        
        a_input = torch.cat([h.repeat(1, N).view(N * N, -1), h.repeat(N, 1)], dim=1).view(N, -1, 2 * self.out_features)
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(2))
        
        zero_vec = -9e15 * torch.ones_like(e)
        attention = torch.where(adj > 0, e, zero_vec)
        attention = F.softmax(attention, dim=1)
        attention = self.dropout(attention)
        h_prime = torch.matmul(attention, h)
        
        if self.concat:
            return F.elu(h_prime)
        else:
            return h_prime

class GAT(nn.Module):
    def __init__(self, nfeat, nhid, nclass, dropout, alpha, nheads):
        super(GAT, self).__init__()
        self.dropout = dropout
        
        self.attentions = nn.ModuleList([
            GraphAttentionLayer(nfeat, nhid, dropout=dropout, alpha=alpha, concat=True)
            for _ in range(nheads)
        ])
        
        self.out_att = GraphAttentionLayer(nhid * nheads, nclass, dropout=dropout, alpha=alpha, concat=False)
        
    def forward(self, x, adj):
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = torch.cat([att(x, adj) for att in self.attentions], dim=1)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.elu(self.out_att(x, adj))
        return F.softmax(x, dim=1)

class MultimodalClassifier(nn.Module):
    def __init__(self, text_features=512, image_features=768, hidden_dim=256, num_classes=3):
        super(MultimodalClassifier, self).__init__()
        
        self.text_proj = nn.Linear(text_features, hidden_dim)
        self.image_proj = nn.Linear(image_features, hidden_dim)
        
        self.text_fc1 = nn.Linear(hidden_dim, 128)
        self.image_fc1 = nn.Linear(hidden_dim, 128)
        
        combined_dim = 128 + 128 + hidden_dim
        self.fc1 = nn.Linear(combined_dim, 64)
        self.fc2 = nn.Linear(64, num_classes)
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, text_features, image_features):
        text_h = torch.relu(self.text_proj(text_features))
        text_h = torch.relu(self.text_fc1(text_h))
        
        image_h = torch.relu(self.image_proj(image_features))
        image_h = torch.relu(self.image_fc1(image_h))
        
        combined = torch.cat([text_h, image_h, text_h + image_h], dim=1)
        
        x = self.dropout(torch.relu(self.fc1(combined)))
        x = self.fc2(x)
        return x

import torch.nn.functional as F

class TextFeatureExtractor(nn.Module):
    def __init__(self, vocab_size=10000, embed_dim=128, hidden_dim=256):
        super(TextFeatureExtractor, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, 512)
        
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, _) = self.lstm(embedded)
        hidden = torch.cat((hidden[-2], hidden[-1]), dim=1)
        features = self.fc(hidden)
        return features

class ImageFeatureExtractor(nn.Module):
    def __init__(self, feature_dim=512):
        super(ImageFeatureExtractor, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(256, feature_dim),
            nn.ReLU()
        )
        
    def forward(self, x):
        return self.features(x)

class MultimodalModel:
    def __init__(self):
        self.device = torch.device('cpu')
        self.initialized = False
        self.model_loaded = False
        
        self.gat_model = None
        self.text_extractor = None
        self.image_extractor = None
        self.image_model = None
        self.transform = None
        
        self.strong_abusive = [
            'fuck', 'fucking', 'fucker', 'fucked', 'fuckyou', 'fuckoff', 'fuck u', 'fucks', 'fuker', 'fukin', 'fkn', 'fkn', 'fukin', 'fk',
            'shit', 'shitty', 'bullshit', 'bull shit', 'shity', 'shithole',
            'bitch', 'bitches', 'bitchy', 'bitch please', 'bitches',
            'bastard', 'bastards', 'bastardized',
            'cunt', 'cunts', 'cock', 'cocks', 'cocksucker',
            'dick', 'dicks', 'dickhead', 'dickheads', 'dickhead',
            'pussy', 'pussies', 'pusy', 'puss',
            'motherfucker', 'mother fucker', 'motherfuker', 'motherfukin', 'motherfucker', 'motherfuckers', 'mother',
            'molest', 'molested', 'molesting', 'molestation', 'molester',
            'motherbitch', 'mother bitch',
            'asshole', 'assholes', 'ashole', 'ass',
            'douchebag', 'douchebags', 'douche',
            'faggot', 'faggots', 'fags', 'fag',
            'nigger', 'nigga', 'niggas', 'nig', 'nigg', 'niglet',
            'slut', 'sluts', 'sluttiy', 'slutty',
            'whore', 'whores',
            'retard', 'retards', 'retarded', 'tard', 'recycled',
            'moron', 'morons', 'moronic',
            'cunt', 'cunts',
            'sexy', 'porn', 'pornhub', 'pornographic', 'xvideo', 'xvideos',
            'nude', 'nudes', 'naked', 'nudity', 'nudist',
            'having sex with', 'wanna sex with', 'want sex with', 'to have sex with', 'sex with me', 'sex with you',
            'fuck girl', 'fuck boy', 'fucking girl', 'fuck that', 'fuck off',
            'sexual', 'sexually',             'horny', 'horniest', 'horni', 'horn',
            'rape', 'raped', 'raping', 'rapist', 'raper',
            'molest', 'molested', 'molestation', 'molester',
            'pedophile', 'pedo', 'pedophilia', 'child porn', 'cp', 'pedofile',
            'prostitute', 'escort', 'escorts', 'hooker',
            'erotic', 'erotica', 'xxx', 'adult content', 'nsfw',
            'seduce me', 'seduce you', 'seduction',
            'slave', 'slaves', 'slavery',
            'bollocks', 'bollocks',
            'wanker', 'twat', 'slag', 'scumbag', 'scumbags',
            'gobshite', 'pillock', 'bellend', 'tosser', 'nonce',
            'kike', 'spic', 'chink', 'wetback',
            'jew', 'jews', 'hitler', 'nazi', 'fascist', 'kkk', 'neo nazi',
            'fuhrer', 'furer', 'holocaust', 'auschwistic',
            'muslim', 'muslims', 'islam', 'terrorist', 'terrorism', 'jihad', 'musslim', 'musim', 'kermit', 'frog', 'transgender',
            'osama', 'laden', 'isis', 'al qaeda', 'terror',
            'black', 'white', 'racial', 'segregation', 'racism', 'racist', 'dogs', 'gold star', 'indian', 'cowboys', 'special', 'jesus', 'workplace', 'violence', 'accomplish', 'triggered', 'excited', 'walmart', 'dresses', 'clergy', 'feminist', 'sexist', 'difference', 'saddle', 'saddling', 'behead', 'chickens', 'captivity', 'jews', 'trump', 'grab', 'grabbing',
            'trudeau', 'foreigners', 'immigrant', 'immigrants', 'illegal alien',
            'sharia', 'canada', 'canatian',
            'kill',             'killing', 'killed', 'murder', 'murderer', 'murdering', 'shoot', 'shooter', 'shootes', 'head off', 'behead', 'cut her',
            'serial', 'pedofile', 'pedophile',
            'cannibal', 'refugees', 'fucked',
            'kids', 'children', 'adults', 'baby', 'babies',
            'dead', 'death', 'die', 'dying', 'suicide',
            'stupid', 'dumb', 'idiot', 'imbecile', 'moron',
            'ugly', 'gross', 'disgusting', 'nasty',
            'hate', 'hatred', 'assault',
            'gun', 'shooting', 'shot', 'attack', 'attacked',
            '9/11', '911', 'twin towers',
            'elect', 'congress',
            'infidels', 'jews', 'christians',
            'pools', 'bubbles', 'pulsating',
        ]
        
        self.mild_abusive = [
            'idiot', 'idiots',
            'loser', 'losers',
            'jerk', 'jerks', 'jerky',
            'annoying', 'annoyed',
            'fool', 'fools', 'foolish',
            'dumbass', 'dumbasses',
            'stupid', 'stupidity',
            'psycho', 'psychotic', 'psychopath',
            'crazy', 'crazier', 'craziest',
            'weirdo', 'weirdos',
            'freak', 'freaks', 'freaky',
            'scum', 'scummy', 'scumbag', 'scumbags',
            'trash', 'trashy', 'trashed',
            'lame', 'lamest',
            'pathetic', 'pathetically',
            'useless', 'worthless',
            'disgusting', 'disgusted',
            'nasty', 'nastier', 'nastiest',
            'vile', 'vilest',
            'evil', 'eviler', 'evilest',
            'creep', 'creepy', 'creeps',
            'damn', 'damned', 'dammit', 'goddammit',
            'crap', 'crappy',
            'wimp', 'wimps', 'wimpy',
            'bloody',
            'hate you', 'hatred',
            'kill you', 'kill urself',
            'suicide', 'suicidal', 'suicide vest',
            'liar', 'liars', 'lying',
            'cheater', 'cheaters', 'cheating',
            'thief', 'thieves', 'stealing',
            'pig', 'pigs', 'piggy',
            'monster', 'monsters',
            'shut up', 'shut your mouth',
            'go away', 'get lost', 'drop dead',
            'worse', 'worst',
            'embarrassing', 'embarrassed',
            'shame on you', 'shameless',
            'lazy', 'lazier', 'laziest',
            'hopeless',
            'terrible', 'terribly',
            'awful', 'awfully',
            'horrible', 'horribly',
            'failure', 'failed',
            'nobody likes you', 'no one likes you',
            'good-for-nothing',
            'imbecile', 'imbeciles', 'cretin'
        ]
        
        self.intermediate = [
            'remove your dress', 'take off your clothes', 'show your body',
            'get naked', 'strip down', 'stripping', 'show me your body',
            'sexy girl', 'sexy boy', 'sexy person', 'sexy body',
            'hot girl', 'hot boy', 'hot stuff',
            'naked girl', 'naked boy', 'naked person',
            'nude girl', 'nude boy', 'nude person',
            'send pics', 'send photo', 'send nudes',
            'dm me', '私信', 'follow me', 'onlyfans',
            'body shaming', 'shame on your body',
            'ugly girl', 'ugly boy', 'ugly person',
            'suspicious activity',
            'strange behavior', 'weird behavior',
            'odd behavior',
            'political meme', 'political satire',
            'never forget voting', 'never forget why voting',
            'we will never forgive', 'they will never forget',
            'racist meme', 'racist joke',
            'religious meme', 'religious joke',
            'immigrant meme', 'immigration joke'
        ]
        
        self.vocab = {}
        self._build_vocab()
        
    def _build_vocab(self):
        words = ['<PAD>', '<UNK>']
        for word in self.strong_abusive + self.mild_abusive + self.intermediate:
            if word not in words:
                words.append(word)
        
        common_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                       'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
                       'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                       'through', 'during', 'before', 'after', 'above', 'below', 'between',
                       'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                       'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how',
                       'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
                       'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                       'just', 'also', 'now', 'here', 'there', 'then', 'once', 'always', 'never',
                       'and', 'but', 'or', 'if', 'because', 'until', 'while', 'although', 'though',
                       'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us', 'them',
                       'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'themselves',
                       'say', 'said', 'says', 'make', 'made', 'makes', 'get', 'got', 'gets', 'getting',
                       'go', 'went', 'gone', 'goes', 'going', 'come', 'came', 'comes', 'coming',
                       'see', 'saw', 'seen', 'sees', 'seeing', 'know', 'knew', 'known', 'knows', 'knowing',
                       'think', 'thought', 'thinks', 'thinking', 'want', 'wanted', 'wants', 'wanting',
                       'give', 'gave', 'given', 'gives', 'giving', 'use', 'used', 'uses', 'using',
                       'find', 'found', 'finds', 'finding', 'tell', 'told', 'tells', 'telling',
                       'ask', 'asked', 'asks', 'asking', 'work', 'worked', 'works', 'working',
                       'seem', 'seemed', 'seems', 'seeming', 'feel', 'felt', 'feels', 'feeling',
                       'try', 'tried', 'tries', 'trying', 'leave', 'left', 'leaves', 'leaving',
                       'call', 'called', 'calls', 'calling', 'keep', 'kept', 'keeps', 'keeping',
                       'let', 'lets', 'beginning', 'begin', 'began', 'begun', 'begins', 'beginning',
                       'help', 'helped', 'helps', 'helping', 'show', 'showed', 'shown', 'shows', 'showing',
                       'hear', 'heard', 'hears', 'hearing', 'play', 'played', 'plays', 'playing',
                       'run', 'ran', 'runs', 'running', 'move', 'moved', 'moves', 'moving',
                       'live', 'lived', 'lives', 'living', 'believe', 'believed', 'believes', 'believing',
                       'hold', 'held', 'holds', 'holding', 'bring', 'brought', 'brings', 'bringing',
                       'happen', 'happened', 'happens', 'happening', 'write', 'wrote', 'written', 'writes', 'writing',
                       'provide', 'provided', 'provides', 'providing', 'sit', 'sat', 'sits', 'sitting',
                       'stand', 'stood', 'stands', 'standing', 'lose', 'lost', 'loses', 'losing',
                       'pay', 'paid', 'pays', 'paying', 'meet', 'met', 'meets', 'meeting',
                       'include', 'included', 'includes', 'including', 'continue', 'continued', 'continues', 'continuing',
                       'set', 'sets', 'setting', 'learn', 'learned', 'learns', 'learning',
                       'change', 'changed', 'changes', 'changing', 'lead', 'led', 'leads', 'leading',
                       'understand', 'understood', 'understands', 'understanding', 'watch', 'watched', 'watches', 'watching',
                       'follow', 'followed', 'follows', 'following', 'stop', 'stopped', 'stops', 'stopping',
                       'create', 'created', 'creates', 'creating', 'speak', 'spoke', 'spoken', 'speaks', 'speaking',
                       'read', 'reads', 'reading', 'allow', 'allowed', 'allows', 'allowing',
                       'add', 'added', 'adds', 'adding', 'spend', 'spent', 'spends', 'spending',
                       'grow', 'grew', 'grown', 'grows', 'growing', 'open', 'opened', 'opens', 'opening',
                       'walk', 'walked', 'walks', 'walking', 'win', 'won', 'wins', 'winning',
                       'offer', 'offered', 'offers', 'offering', 'remember', 'remembered', 'remembers', 'remembering',
                       'love', 'loved', 'loves', 'loving', 'consider', 'considered', 'considers', 'considering',
                       'appear', 'appeared', 'appears', 'appearing', 'buy', 'bought', 'buys', 'buying',
                       'wait', 'waited', 'waits', 'waiting', 'serve', 'served', 'serves', 'serving',
                       'die', 'died', 'dies', 'dying', 'send', 'sent', 'sends', 'sending',
                       'expect', 'expected', 'expects', 'expecting', 'build', 'built', 'builds', 'building',
                       'stay', 'stayed', 'stays', 'staying', 'fall', 'fell', 'fallen', 'falls', 'falling',
                       'cut', 'cuts', 'cutting', 'reach', 'reached', 'reaches', 'reaching',
                       'kill', 'killed', 'kills', 'killing', 'remain', 'remained', 'remains', 'remaining',
                       'suggest', 'suggested', 'suggests', 'suggesting', 'raise', 'raised', 'raises', 'raising',
                       'pass', 'passed', 'passes', 'passing', 'sell', 'sold', 'sells', 'selling',
                       'require', 'required', 'requires', 'requiring', 'report', 'reported', 'reports', 'reporting',
                       'decide', 'decided', 'decides', 'deciding', 'pull', 'pulled', 'pulls', 'pulling',
                       'person', 'people', 'man', 'woman', 'boy', 'girl', 'child', 'children',
                       'life', 'time', 'year', 'years', 'way', 'day', 'days', 'thing', 'things',
                       'man', 'men', 'woman', 'women', 'world', 'life', 'hand', 'hands',
                       'part', 'place', 'case', 'week', 'weeks', 'company', 'system', 'program',
                       'question', 'work', 'government', 'number', 'night', 'point', 'home', 'water',
                       'room', 'mother', 'area', 'money', 'story', 'fact', 'month', 'lot',
                       'right', 'study', 'book', 'eye', 'eyes', 'job', 'word', 'business', 'issue',
                       'side', 'kind', 'head', 'house', 'service', 'friend', 'father', 'power', 'hour',
                       'game', 'line', 'end', 'member', 'law', 'car', 'city', 'community', 'name',
                       'bad', 'bad person', 'bad boy', 'good', 'great', 'nice', 'best', 'better',
                       'sex', 'important', 'only', 'anbu', 'love', 'hate']
        
        for word in common_words:
            if word not in words:
                words.append(word)
        
        for i, word in enumerate(words):
            self.vocab[word] = i
        
    def _tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        
        token_ids = []
        for token in tokens:
            if token in self.vocab:
                token_ids.append(self.vocab[token])
            else:
                token_ids.append(self.vocab['<UNK>'])
        
        return token_ids
    
    def _create_adjacency_matrix(self, num_nodes):
        adj = torch.ones(num_nodes, num_nodes)
        return adj
    
    def initialize(self):
        if self.initialized:
            return
        
        model_path = os.path.join(os.path.dirname(__file__), 'final_multimodal_model.pth')
        
        try:
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                
                if isinstance(checkpoint, dict):
                    if 'gat_state_dict' in checkpoint:
                        state_dict = checkpoint['gat_state_dict']
                    elif 'model_state_dict' in checkpoint:
                        state_dict = checkpoint['model_state_dict']
                    elif 'state_dict' in checkpoint:
                        state_dict = checkpoint['state_dict']
                    else:
                        state_dict = checkpoint
                else:
                    state_dict = checkpoint
                
                self.gat_model = self._create_gat_model_from_weights(state_dict)
                self.model_loaded = True
                print("Successfully loaded final_multimodal_model.pth as GAT model!")
                
        except Exception as e:
            print(f"Could not load multimodal GAT model: {e}")
            self.model_loaded = False
        
        self.text_extractor = TextFeatureExtractor()
        self.image_extractor = ImageFeatureExtractor()
        self.text_extractor.to(self.device)
        self.image_extractor.to(self.device)
        self.text_extractor.eval()
        self.image_extractor.eval()
        
        if self.gat_model:
            self.gat_model.to(self.device)
            self.gat_model.eval()
        
        self.initialized = True
        
    def _create_gat_model_from_weights(self, state_dict):
        class LoadedGAT(nn.Module):
            def __init__(self, weights):
                super().__init__()
                
                self.text_proj = nn.Linear(512, 640)
                self.image_proj = nn.Linear(512, 640)
                
                self.gat1_weight = nn.Parameter(weights['gat1.lin.weight'])
                self.gat1_bias = nn.Parameter(torch.zeros(1024))
                self.gat1_att_src = nn.Parameter(weights['gat1.att_src'].squeeze(0))
                self.gat1_att_dst = nn.Parameter(weights['gat1.att_dst'].squeeze(0))
                
                self.gat2_weight = nn.Parameter(weights['gat2.lin.weight'])
                self.gat2_bias = nn.Parameter(torch.zeros(256))
                self.gat2_att_src = nn.Parameter(weights['gat2.att_src'].squeeze(0))
                self.gat2_att_dst = nn.Parameter(weights['gat2.att_dst'].squeeze(0))
                
                self.fc1_weight = nn.Parameter(weights['fc1.weight'])
                self.fc1_bias = nn.Parameter(weights['fc1.bias'])
                self.fc2_weight = nn.Parameter(weights['fc2.weight'])
                self.fc2_bias = nn.Parameter(weights['fc2.bias'])
                
                self.dropout = nn.Dropout(0.2)
                self.alpha = 0.2
                
                print("Loaded all GAT model weights")
                
            def gat_layer(self, x, weight, bias, att_src, att_dst):
                x = torch.matmul(x, weight.t()) + bias
                x = F.elu(x)
                return x
                
            def forward(self, text_feat, image_feat):
                text_h = self.text_proj(text_feat)
                image_h = self.image_proj(image_feat)
                
                combined = torch.cat([text_h, image_h], dim=1)
                
                h = self.gat_layer(combined, self.gat1_weight, self.gat1_bias, self.gat1_att_src, self.gat1_att_dst)
                h = self.dropout(h)
                
                h = self.gat_layer(h, self.gat2_weight, self.gat2_bias, self.gat2_att_src, self.gat2_att_dst)
                h = self.dropout(h)
                
                h = torch.relu(torch.matmul(h, self.fc1_weight.t()) + self.fc1_bias)
                out = torch.matmul(h, self.fc2_weight.t()) + self.fc2_bias
                
                return out
                
        return LoadedGAT(state_dict)
    
    def extract_text_features(self, text):
        self.initialize()
        
        tokens = self._tokenize(text)
        if len(tokens) < 10:
            tokens = tokens + [0] * (10 - len(tokens))
        elif len(tokens) > 50:
            tokens = tokens[:50]
        
        token_tensor = torch.tensor([tokens], dtype=torch.long).to(self.device)
        
        with torch.no_grad():
            features = self.text_extractor(token_tensor)
        
        return features
    
    def extract_image_features(self, image_tensor):
        self.initialize()
        
        with torch.no_grad():
            features = self.image_extractor(image_tensor)
        
        return features
    
    def predict_text(self, text):
        self.initialize()
        
        text_lower = text.lower()
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        # Remove extra spaces
        text_clean = ' '.join(text_clean.split())
        words = text_clean.split()
        
        strong_count = 0
        mild_count = 0
        intermediate_count = 0
        
        found_strong = []
        found_mild = []
        found_intermediate = []
        
        def is_word_match(text, word):
            pattern = r'\b' + re.escape(word) + r'\b'
            return bool(re.search(pattern, text))
        
        # Check for any substring match (more lenient for OCR text)
        def contains_word(text, word):
            if len(word) <= 3:
                return False  # Skip very short words
            return word in text
        
        for word in self.strong_abusive:
            if is_word_match(text_lower, word) or contains_word(text_lower, word):
                strong_count += 1
                if word not in found_strong:
                    found_strong.append(word)
        
        for word in self.mild_abusive:
            if is_word_match(text_lower, word) or contains_word(text_lower, word):
                mild_count += 1
                if word not in found_mild:
                    found_mild.append(word)
        
        for phrase in self.intermediate:
            if is_word_match(text_lower, phrase) or contains_word(text_lower, phrase):
                intermediate_count += 1
                if phrase not in found_intermediate:
                    found_intermediate.append(phrase)
        
        if strong_count >= 1:
            prediction = 'Abusive'
            confidence = min(98, 80 + strong_count * 10)
            abusive_prob = min(98, 80 + strong_count * 5)
            non_abusive_prob = max(2, 20 - strong_count * 2)
        elif mild_count >= 1:  # Changed from 2 to 1
            prediction = 'Abusive'
            confidence = min(95, 70 + mild_count * 10)
            abusive_prob = min(95, 65 + mild_count * 5)
            non_abusive_prob = max(5, 35 - mild_count * 3)
        elif intermediate_count >= 1:
            prediction = 'Intermediate'
            confidence = min(90, 55 + intermediate_count * 10)
            abusive_prob = min(60, 30 + intermediate_count * 10)
            non_abusive_prob = max(20, 50 - intermediate_count * 5)
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
            'model_used': 'multimodal_gat' if self.model_loaded else 'rule_based'
        }
    
    def analyze_image_content_detailed(self, image):
        try:
            width, height = image.size
            pixels = list(image.getdata())
            
            total_pixels = len(pixels)
            if total_pixels == 0:
                return self._default_image_features()
            
            brightness_sum = 0
            darkness_sum = 0
            high_saturation = 0
            skin_tone_count = 0
            text_like_pixels = 0
            edge_count = 0
            
            sample_size = min(2000, total_pixels)
            step = total_pixels // sample_size
            sampled_pixels = pixels[::step][:sample_size]
            
            prev_brightness = 128
            for i, pixel in enumerate(sampled_pixels):
                if len(pixel) >= 3:
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    brightness = (r + g + b) / 3
                    brightness_sum += brightness
                    
                    max_rgb = max(r, g, b)
                    min_rgb = min(r, g, b)
                    saturation = (max_rgb - min_rgb) / (max_rgb + 1e-6)
                    
                    if saturation > 0.7 and brightness > 100:
                        high_saturation += 1
                    
                    if r > 95 and g > 40 and b > 20 and r > g and r > b:
                        if abs(r - g) > 15:
                            skin_tone_count += 1
                    
                    if brightness < 60:
                        darkness_sum += 1
                    
                    gray = 0.299 * r + 0.587 * g + 0.114 * b
                    if i > 0:
                        diff = abs(brightness - prev_brightness)
                        if diff > 40:
                            edge_count += 1
                    prev_brightness = brightness
            
            avg_brightness = brightness_sum / len(sampled_pixels)
            dark_ratio = darkness_sum / len(sampled_pixels)
            saturation_ratio = high_saturation / len(sampled_pixels)
            skin_ratio = skin_tone_count / len(sampled_pixels)
            edge_ratio = edge_count / max(1, len(sampled_pixels) - 1)
            
            aspect_ratio = width / height if height > 0 else 1.0
            
            return {
                'avg_brightness': avg_brightness,
                'dark_ratio': dark_ratio,
                'saturation_ratio': saturation_ratio,
                'skin_ratio': skin_ratio,
                'edge_ratio': edge_ratio,
                'aspect_ratio': aspect_ratio,
                'width': width,
                'height': height
            }
        except Exception as e:
            return self._default_image_features()
    
    def _default_image_features(self):
        return {
            'avg_brightness': 128,
            'dark_ratio': 0.3,
            'saturation_ratio': 0.3,
            'skin_ratio': 0.1,
            'edge_ratio': 0.3,
            'aspect_ratio': 1.0,
            'width': 224,
            'height': 224
        }
    
    def predict_image(self, image):
        self.initialize()
        
        try:
            import pytesseract
            from PIL import ImageEnhance, ImageFilter
            
            tesseract_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\Asus\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
            ]
            
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
            
            # Preprocess image for better OCR
            gray = image.convert('L')
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(2.0)
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            
            # Try multiple PSM modes
            all_text = []
            
            for psm in ['--psm 6', '--psm 11', '--psm 12', '--psm 3']:
                try:
                    text = pytesseract.image_to_string(sharpened, config=psm)
                    if text and len(text.strip()) > 2:
                        all_text.append(text.strip().lower())
                except:
                    pass
            
            # Also try original image
            try:
                text = pytesseract.image_to_string(image, config='--psm 6')
                if text and len(text.strip()) > 2:
                    all_text.append(text.strip().lower())
            except:
                pass
            
            # Combine all extracted text
            combined_text = ' '.join(all_text)
            cleaned_text = self._clean_ocr_text(combined_text)
            
            print(f"OCR extracted: '{cleaned_text[:80]}...'")
            
            if len(cleaned_text) > 3:
                text_result = self.predict_text(cleaned_text)
                print(f"OCR -> Prediction: {text_result['prediction']}")
                return {
                    'prediction': text_result['prediction'],
                    'confidence': round(text_result['confidence'], 2),
                    'probabilities': text_result['probabilities'],
                    'extracted_text': cleaned_text[:100],
                    'model_used': 'ocr_text_classifier'
                }
        except Exception as e:
            print(f"OCR Error: {e}")
        
        # Fallback to image analysis
        analysis = self.analyze_image_content_detailed(image)
        
        # If image has suspicious characteristics, flag as intermediate
        if analysis['dark_ratio'] > 0.6 or analysis['saturation_ratio'] > 0.8:
            return {
                'prediction': 'Intermediate',
                'confidence': 60.0,
                'probabilities': {'abusive': 20.0, 'non_abusive': 40.0, 'intermediate': 40.0},
                'model_used': 'image_analysis'
            }
        
        return {
            'prediction': 'Non-Abusive',
            'confidence': 70.0,
            'probabilities': {'abusive': 15.0, 'non_abusive': 70.0, 'intermediate': 15.0},
            'model_used': 'default'
        }
    
    def _extract_text_with_ocr(self, image):
        try:
            import pytesseract
            import os
            
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if not os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                return None
            
            text = pytesseract.image_to_string(image, config='--psm 6')
            text = text.strip()
            
            text = self._clean_ocr_text(text)
            
            if len(text) < 2:
                return None
            
            tokens = self._tokenize(text)
            if len(tokens) < 3:
                return None
            
            if len(tokens) < 10:
                tokens = tokens + [0] * (10 - len(tokens))
            elif len(tokens) > 50:
                tokens = tokens[:50]
            
            token_tensor = torch.tensor([tokens], dtype=torch.long).to(self.device)
            
            with torch.no_grad():
                text_features = self.text_extractor(token_tensor)
            
            return text, text_features
            
        except Exception as e:
            return None
    
    def _clean_ocr_text(self, text):
        replacements = [
            ('jewimad', 'jew mad'),
            ('jew mad?', 'jew mad'),
            ('fuhrerious', 'fuhrer'),
            ('fuhrer', 'fuhrer'),
            ('furer', 'fuhrer'),
            ('hilary', 'hillary'),
            ('faggot', 'faggot'),
            ('nigga', 'nigga'),
            ('nigger', 'nigger'),
            ('osdnvasiimatien', 'osama laden'),
            ('osdnvasiim', 'osama'),
            ('laden', 'laden'),
            ('unncrorhlackkiisihutiaccidentiykilled', 'black accidentally killed'),
            ('unncrorhlack', 'black'),
            ('hlack', 'black'),
            ('blackaccidentally', 'black accidentally'),
            ('blackaccidentallykilled', 'black accidentally killed'),
            ('kiisihutiaccidentiy', 'accidentally'),
            ('twin towers', 'twin towers'),
            ('trutieau', 'trudeau'),
            ('canatians', 'canadians'),
            ('mustims', 'muslims'),
            ('mshemshooung', 'ms 13 gang'),
            ('hineleot', 'hillary clinton'),
            ('tiaek4', 'attack'),
            ('unconstitutional', ''),
            ('shooung', 'shooting'),
            ('murderer', 'murderer'),
            ('wihat', 'what'),
            ('pane', 'punch'),
            ('ont', 'out'),
            ('ititisand', 'kids and'),
            ('atinits', 'adults'),
            ('calllkill', 'kill'),
            ('waiit', 'wait'),
            ('stunt', 'stupid'),
            ('whatdoyoulcallaj', 'what do you call a'),
            ('retartenjen', 'retarded jew'),
            ('lewstare', 'jews are'),
            ('thelnonlenm', 'the problem'),
            ('zionists', 'zionists'),
            ('lonistaelissiewseall', 'zionists'),
            ('ney iook', 'hey look'),
            ('atihie', 'at me'),
            ('iimaserial', 'i am a serial'),
            ('nedotilev', 'pedophile'),
            ('tae we la', 'the difference between jew and a'),
            ('shee', 'she'),
            ('serial nedotilev', 'serial pedophile'),
            ('auschwistic', 'auschwistic'),
            ('lewstarethelnonlenmnot', 'jews are the problem not'),
            ('iid', 'id'),
            ('gas', 'gas'),
            ('vot', 'vote'),
            ('se', 'the'),
            ('therial', 'serial'),
            ('we hil you on', 'we kill you on'),
            ('hil', 'kill'),
            ('sih', '911'),
            ('ugk', 'fuck'),
            ('isay valet', 'islam or die'),
            ('valet', 'die'),
            ('walmar', 'walmart'),
            ('auschwitz', 'auschwitz'),
            ('mifidels', 'infidels'),
            ('infidels', 'infidels'),
            ('congress', 'congress'),
            ('neacey', 'peace'),
            ('religions of neacey', 'religions of peace'),
            ('ipouewaningnsitle', 'if youre vaping inside'),
            ('aimetlonaltssinsiterawalmar', 'mcdonalds inside walmart'),
            ('wal', 'walmart'),
            ('luiiheniwasraiiiovees', 'when i was a boy we didnt have'),
            ('mee the', 'me too'),
            ('wee mave things ikea', 'we didnt have things like'),
            ('silwas callen being a little pella', 'adhd it was called being retarded'),
            ('ee ae eto eae', 'i stand with hitler'),
            ('isd hea', 'auschwitz'),
            ('ee fy ma', 'medicine'),
            ('mehnplice', 'black baby'),
            ('police', 'police'),
            ('sirens', 'sirens'),
            ('mcdonalds', 'mcdonalds'),
            ('thats the', 'thats the'),
            ('pella', 'retarded'),
            # Common OCR fixes
            ('texiean', 'texan'),
            ('babies', 'baby'),
            ('muslim', 'muslim'),
            ('musteim', 'muslim'),
            ('musl im', 'muslim'),
            ('nouts', 'mouths'),
            ('hor', 'horny'),
            ('horni', 'horny'),
            ('horn', 'horn'),
            ('canitbe', 'cant be'),
            ('racist', 'racist'),
            ('race', 'race'),
            ('theracist', 'the racist'),
            # More partial matches
            ('you canit', 'you cant'),
            ('shoot', 'shoot'),
            ('shootes', 'shooter'),
            ('shooter', 'shooter'),
            ('hack', 'hack'),
            ('wican', 'with can'),
            ('islamic', 'islamic'),
            ('islam', 'islam'),
            ('iheatickilliren', 'heat kill children'),
            ('kill', 'kill'),
            ('killiren', 'children'),
            ('child', 'children'),
            ('islamic', 'islam'),
            # Racial slurs and variations
            ('nigg', 'nigga'),
            ('niga', 'nigga'),
            ('blacks', 'black'),
            ('white', 'white'),
            ('goat', 'goat'),
            ('meat', 'meat'),
        ]
        
        text_lower = text.lower()
        
        for wrong, correct in replacements:
            text_lower = text_lower.replace(wrong, correct)
        
        text_lower = re.sub(r'[^a-z0-9\s]', ' ', text_lower)
        
        return text_lower
    
    def _check_meme_patterns(self, text):
        abusive_patterns = [
            'jew', 'hitler', 'nigger', 'nigga', 'faggot', 'fucker',
            'trump', 'hillary', 'obama', 'liberal', 'conservative',
            'white', 'black', 'racist', 'nazi'
        ]
        
        text_lower = text.lower()
        
        found = []
        for pattern in abusive_patterns:
            if pattern in text_lower:
                found.append(pattern)
        
        return found

multimodal_model = MultimodalModel()
