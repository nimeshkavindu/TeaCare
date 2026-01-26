import tensorflow as tf
import pickle
import numpy as np
import cv2
from PIL import Image, ImageOps
from llama_cpp import Llama
import io
import os

class AIModelService:
    _instance = None
    model = None
    class_names = []
    llm = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self):
        print("Loading AI Models...")
        try:
            self.model = tf.keras.models.load_model('models/tea_leaf_convnext.keras')
            with open('models/class_names.pkl', 'rb') as f:
                self.class_names = pickle.load(f)
            
            # Load LLM
            self.llm = Llama(
                model_path="models/qwen2.5-0.5b-instruct-q4_k_m.gguf", 
                n_ctx=2048, n_threads=4, verbose=False
            )
            print("AI Models Loaded Successfully")
        except Exception as e:
            print(f"AI Load Error: {e}")

    def is_blurry(self, image_bytes, threshold=35.0):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        score = cv2.Laplacian(img, cv2.CV_64F).var()
        return score < threshold

    def predict_image(self, image_bytes):
        if not self.model: raise Exception("Model not loaded")
        
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image = image.resize((224, 224))
        img_orig = np.asarray(image)
        img_rot = np.asarray(image.rotate(90))
        img_flip = np.asarray(ImageOps.mirror(image))
        batch = np.array([img_orig, img_rot, img_flip])

        predictions = self.model.predict(batch)
        avg_score = np.mean(predictions, axis=0)
        final_score = tf.nn.softmax(avg_score)
        class_idx = np.argmax(final_score)
        
        return self.class_names[class_idx], float(np.max(final_score)) * 100

ai_manager = AIModelService.get_instance()