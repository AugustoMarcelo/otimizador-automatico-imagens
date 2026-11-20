"""Diagnóstico de exposição e correção automática com NumPy e OpenCV."""

import cv2
import numpy as np


def _validar_imagem(imagem: np.ndarray) -> None:
    if (not isinstance(imagem, np.ndarray) or imagem.dtype != np.uint8
            or imagem.ndim != 3 or imagem.shape[2] != 3 or imagem.size == 0):
        raise ValueError('A imagem deve ser uma matriz BGR uint8 não vazia.')


def diagnosticar(imagem: np.ndarray) -> dict:
    """Classifica pela média de cinza e retorna o histograma de 256 níveis."""
    _validar_imagem(imagem)
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    media = float(np.mean(cinza))
    if media < 100:
        diagnostico = 'subexposta'
    elif media > 200:
        diagnostico = 'superexposta'
    else:
        diagnostico = 'normal'
    histograma = cv2.calcHist([cinza], [0], None, [256], [0, 256])
    return {
        'diagnostico': diagnostico,
        'media': media,
        'desvio_padrao': float(np.std(cinza)),
        'histograma': histograma.ravel().astype(int).tolist(),
    }


def _tabela_gama(gamma: float) -> np.ndarray:
    if not np.isfinite(gamma) or gamma <= 0:
        raise ValueError('Gama deve ser um número finito maior que zero.')
    niveis = np.arange(256, dtype=np.float32) / 255.0
    return np.clip(np.power(niveis, 1.0 / gamma) * 255.0, 0, 255).astype(np.uint8)


def ajustar_gama(imagem: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    """Aplica saída = 255 * (entrada / 255) ** (1 / gamma) via LUT."""
    _validar_imagem(imagem)
    return cv2.LUT(imagem, _tabela_gama(gamma))


def _selecionar_gama(histograma: list[int]) -> float:
    """Busca gama para aproximar a média de cinza de 128 sem achatar a LUT."""
    pesos = np.asarray(histograma, dtype=np.float64)
    if not np.any(pesos[1:255]):
        return 1.0
    pesos /= pesos.sum()
    niveis = np.arange(256, dtype=np.float64) / 255.0
    inferior, superior = 0.02, 10.0
    for _ in range(32):
        gamma = (inferior + superior) / 2
        media_prevista = float(np.dot(np.power(niveis, 1 / gamma) * 255, pesos))
        if media_prevista < 128:
            inferior = gamma
        else:
            superior = gamma
    return (inferior + superior) / 2


def otimizar(imagem: np.ndarray) -> tuple[np.ndarray, dict]:
    """Corrige exposição e contraste; imagens normais permanecem idênticas."""
    antes = diagnosticar(imagem)
    if antes['diagnostico'] == 'normal':
        return imagem.copy(), {
            'antes': antes, 'depois': antes, 'gamma': 1.0, 'clahe': False,
        }

    gamma = _selecionar_gama(antes['histograma'])
    ycrcb = cv2.cvtColor(imagem, cv2.COLOR_BGR2YCrCb)
    luminancia, cr, cb = cv2.split(ycrcb)
    luminancia = cv2.LUT(luminancia, _tabela_gama(gamma))
    aplicar_clahe = np.count_nonzero(antes['histograma']) > 1
    if aplicar_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contraste = clahe.apply(luminancia)
        luminancia = cv2.addWeighted(luminancia, 0.5, contraste, 0.5, 0)
    corrigida = cv2.cvtColor(cv2.merge((luminancia, cr, cb)), cv2.COLOR_YCrCb2BGR)

    return corrigida, {
        'antes': antes,
        'depois': diagnosticar(corrigida),
        'gamma': gamma,
        'clahe': bool(aplicar_clahe),
    }
