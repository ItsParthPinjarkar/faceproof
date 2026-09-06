import os
import logging
import cv2
import numpy as np
import insightface
import hashlib
import json
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class FaceEngine:
    """
    InsightFace-based face detection and ArcFace encoding engine.
    Uses buffalo_l model (LFW 99.83%, 512-D ArcFace embeddings).
    """

    def __init__(self, model_name: str = 'buffalo_l', det_size: tuple = (640, 640)):
        self.model_name = model_name
        self.det_size = det_size
        self.app = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy-load the InsightFace model on first use."""
        if not self._initialized:
            logger.info(f"Loading InsightFace model: {self.model_name}")
            self.app = insightface.app.FaceAnalysis(
                name=self.model_name,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            self.app.prepare(ctx_id=0, det_size=self.det_size)
            self._initialized = True
            logger.info("FaceEngine initialized successfully")

    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect all faces in an image. Returns list of face dicts with
        'bbox', 'landmark_2d', 'embedding', 'gender', 'age', 'score'.
        """
        self._ensure_initialized()

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image from {image_path}")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = self.app.get(img_rgb)

        results = []
        for face in faces:
            result = {
                'bbox': face['bbox'].tolist(),
                'landmark_2d': face['landmark_2d'].tolist() if 'landmark_2d' in face else [],
                'landmark_3d': face['landmark_3d'].tolist() if 'landmark_3d' in face else [],
                'embedding': face['embedding'].astype(float),
                'gender': int(face.get('gender', -1)),
                'age': int(face.get('age', 0)),
                'score': float(face.get('det_score', 0)),
                'normed_embedding': face.get('normed_embedding', None)
            }
            results.append(result)

        logger.info(f"Detected {len(results)} face(s) in {image_path}")
        return results

    def detect_primary_face(self, image_path: str) -> Dict[str, Any]:
        """
        Detect and return the largest/most prominent face from the image.
        Returns the face dict with 'encoding' (512-D numpy array).
        """
        faces = self.detect_faces(image_path)
        if not faces:
            raise ValueError("No face detected in the image")

        # Pick the face with the largest bounding box area
        primary = max(faces, key=lambda f: (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1]))
        primary['encoding'] = primary.pop('embedding')
        return primary

    def compute_face_hash(self, face: Dict[str, Any]) -> str:
        """
        Generate a deterministic SHA-256 hash from the face encoding.
        Uses the normed embedding for consistency.
        """
        import json
        # Use the first 8 dimensions as a compact fingerprint representation
        encoding = face.get('normed_embedding') or face['encoding']
        if hasattr(encoding, 'tolist'):
            encoding_list = encoding.tolist()
        else:
            encoding_list = list(encoding)
        encoding_str = json.dumps(encoding_list, sort_keys=True)
        return hashlib.sha256(encoding_str.encode('utf-8')).hexdigest()

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        e1 = np.array(embedding1).flatten()
        e2 = np.array(embedding2).flatten()
        norm1 = np.linalg.norm(e1)
        norm2 = np.linalg.norm(e2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(e1, e2) / (norm1 * norm2))


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        engine = FaceEngine()
        face = engine.detect_primary_face(sys.argv[1])
        face_hash = engine.compute_face_hash(face)
        print(f"Face encoding dimension: {len(face['encoding'])}")
        print(f"Face hash: {face_hash}")
        print(f"Gender: {face.get('gender', 'N/A')}, Age: {face.get('age', 'N/A')}")
