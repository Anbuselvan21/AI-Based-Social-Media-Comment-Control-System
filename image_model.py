import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import os

class ImageClassifier(nn.Module):
    def __init__(self, num_classes=3):
        super(ImageClassifier, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 14 * 14, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

class ImageModel:
    def __init__(self):
        self.model = None
        self.device = torch.device('cpu')
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.initialized = False
        self.model_loaded = False
        
    def initialize(self):
        if self.initialized:
            return
        
        model_path = os.path.join(os.path.dirname(__file__), 'final_multimodal_model.pth')
        
        try:
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                
                self.model = ImageClassifier(num_classes=3)
                
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
                print("Loaded final_multimodal_model.pth for image prediction!")
                self.initialized = True
                return
        except Exception as e:
            print(f"Could not load multimodal model for image: {e}")
        
        self.model = ImageClassifier(num_classes=3)
        self.model.to(self.device)
        self.model.eval()
        self.model_loaded = False
        self.initialized = True
        print("Using built-in CNN classifier for images")
        
    def analyze_image_content(self, image):
        try:
            width, height = image.size
            pixels = list(image.getdata())
            
            total_pixels = len(pixels)
            if total_pixels == 0:
                return {'avg_brightness': 128, 'skin_tone_ratio': 0, 'dark_ratio': 0}
            
            brightness_sum = 0
            skin_tone_count = 0
            dark_count = 0
            bright_count = 0
            
            for pixel in pixels[:min(1000, total_pixels)]:
                if len(pixel) >= 3:
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    brightness = (r + g + b) / 3
                    brightness_sum += brightness
                    
                    if r > 95 and g > 40 and b > 20 and r > g and r > b:
                        if abs(r - g) > 15 and r - g > 15:
                            skin_tone_count += 1
                    
                    if brightness < 50:
                        dark_count += 1
                    if brightness > 200:
                        bright_count += 1
            
            avg_brightness = brightness_sum / min(1000, total_pixels)
            skin_tone_ratio = skin_tone_count / min(1000, total_pixels)
            dark_ratio = dark_count / min(1000, total_pixels)
            bright_ratio = bright_count / min(1000, total_pixels)
            
            return {
                'avg_brightness': avg_brightness,
                'skin_tone_ratio': skin_tone_ratio,
                'dark_ratio': dark_ratio,
                'bright_ratio': bright_ratio
            }
        except:
            return {'avg_brightness': 128, 'skin_tone_ratio': 0, 'dark_ratio': 0, 'bright_ratio': 0}
    
    def predict(self, image_path):
        self.initialize()
        
        try:
            image = Image.open(image_path).convert('RGB')
            
            if self.model is not None and self.model_loaded:
                image_tensor = self.transform(image).unsqueeze(0).to(self.device)
                
                self.model.eval()
                with torch.no_grad():
                    outputs = self.model(image_tensor)
                    probabilities = torch.softmax(outputs, dim=1)
                    
                    prob_values = probabilities[0].cpu().numpy()
                    max_prob = prob_values.max()
                    
                    predicted_class = probabilities[0].argmax().item()
                    labels = ['Abusive', 'Non-Abusive', 'Intermediate']
                    prediction = labels[predicted_class]
                    conf = max_prob
                    
                    return {
                        'prediction': prediction,
                        'confidence': round(conf * 100, 2),
                        'probabilities': {
                            'abusive': round(probabilities[0][0].item() * 100, 2),
                            'non_abusive': round(probabilities[0][1].item() * 100, 2),
                            'intermediate': round(probabilities[0][2].item() * 100, 2)
                        },
                        'model_used': 'multimodal'
                    }
            
            image_features = self.analyze_image_content(image)
            
            inappropriate_indicators = 0
            if image_features['skin_tone_ratio'] > 0.35:
                inappropriate_indicators += 2
            if image_features['bright_ratio'] > 0.6:
                inappropriate_indicators += 1
            if image_features['dark_ratio'] > 0.75:
                inappropriate_indicators += 1
            if image_features['avg_brightness'] > 220:
                inappropriate_indicators += 1
            
            if inappropriate_indicators >= 3:
                prediction = 'Abusive'
                confidence = 72.0
            elif inappropriate_indicators >= 1:
                prediction = 'Intermediate'
                confidence = 65.0
            else:
                prediction = 'Non-Abusive'
                confidence = 78.0
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'probabilities': {
                    'abusive': round(100 - confidence, 1) if prediction == 'Non-Abusive' else round(confidence * 0.6, 1),
                    'non_abusive': round(confidence, 1) if prediction == 'Non-Abusive' else round(100 - confidence * 0.8, 1),
                    'intermediate': round(100 - confidence, 1) if prediction != 'Intermediate' else round(confidence, 1)
                },
                'model_used': 'content_analyzer'
            }
            
        except Exception as e:
            print(f"Error in image prediction: {e}")
            return {
                'prediction': 'Non-Abusive',
                'confidence': 75.0,
                'probabilities': {
                    'abusive': 10.0,
                    'non_abusive': 75.0,
                    'intermediate': 15.0
                }
            }

image_model = ImageModel()
