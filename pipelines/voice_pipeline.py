
import io

import librosa
import numpy as np
from functools import lru_cache
import torch
import soundfile as sf


@lru_cache(maxsize=1)
def load_voice_encoder():
    from speechbrain.inference.speaker import EncoderClassifier
    from speechbrain.utils.fetching import LocalStrategy

    return EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb-win",
        local_strategy=LocalStrategy.COPY_SKIP_CACHE,
    )


def _load_audio(audio_bytes):
    audio_file = io.BytesIO(audio_bytes)

    try:
        audio, sr = sf.read(audio_file, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        return audio
    except Exception:
        audio_file.seek(0)
        audio, _ = librosa.load(audio_file, sr=16000)
        return audio


def _get_speechbrain_embedding(audio_bytes):
    encoder = load_voice_encoder()
    audio = _load_audio(audio_bytes)
    wav = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
    embedding = encoder.encode_batch(wav).squeeze(0).squeeze(0).detach().cpu().numpy()
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return None
    return (embedding / norm).tolist()


def get_voice_embedding(audio_bytes):
    try:
        return _get_speechbrain_embedding(audio_bytes)
    except Exception as e:
        print('Voice recog error')
        return None
    

def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    if new_embedding is None or not candidates_dict:
        return None, 0.0
    
    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding:
            similarity = np.dot(new_embedding, stored_embedding)
            if similarity> best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threshold:
        return best_sid, best_score
    
    return None, best_score



def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):

    try:
        encoder = load_voice_encoder()

        audio = _load_audio(audio_bytes)
        sr = 16000
        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}


        for start, end in segments:

            if (end-start) < sr * 0.5:
                continue
            segment_audio = audio[start:end]
            wav = torch.tensor(segment_audio, dtype=torch.float32).unsqueeze(0)
            embedding = encoder.encode_batch(wav).squeeze(0).squeeze(0).detach().cpu().numpy()

            norm = np.linalg.norm(embedding)
            if norm == 0:
                continue
            embedding = embedding / norm


            sid, score = identify_speaker(embedding, candidates_dict, threshold)

            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results
    except Exception as e:
        print('Bulk process error')
        return {}