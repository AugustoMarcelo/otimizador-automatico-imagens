import unittest
from pathlib import Path

import cv2
import numpy as np

from otimizador import ajustar_gama, diagnosticar, otimizar


RAIZ = Path(__file__).resolve().parents[1]


class DiagnosticoTests(unittest.TestCase):
    def test_classifica_limiares_e_conta_histograma(self):
        for nivel, esperado in [(99, 'subexposta'), (100, 'normal'),
                                (200, 'normal'), (201, 'superexposta')]:
            with self.subTest(nivel=nivel):
                resultado = diagnosticar(np.full((8, 8, 3), nivel, np.uint8))
                self.assertEqual(resultado['diagnostico'], esperado)
                self.assertEqual(resultado['media'], nivel)
                self.assertEqual(sum(resultado['histograma']), 64)
                self.assertEqual(resultado['histograma'][nivel], 64)

    def test_rejeita_imagens_fora_do_contrato_bgr_uint8(self):
        for imagem in [np.zeros((0, 0, 3), np.uint8),
                       np.zeros((2, 2), np.uint8),
                       np.zeros((2, 2, 3), np.float32)]:
            with self.subTest(shape=imagem.shape, dtype=imagem.dtype):
                with self.assertRaises(ValueError):
                    diagnosticar(imagem)


class GamaTests(unittest.TestCase):
    def test_formula_sentido_e_identidade(self):
        imagem = np.array([[[0, 64, 255]]], np.uint8)
        np.testing.assert_array_equal(ajustar_gama(imagem), imagem)
        np.testing.assert_array_equal(ajustar_gama(imagem, 2), [[[0, 127, 255]]])
        np.testing.assert_array_equal(ajustar_gama(imagem, 0.5), [[[0, 16, 255]]])

    def test_preserva_ordem_e_intervalo_sem_alterar_entrada(self):
        imagem = np.repeat(np.arange(256, dtype=np.uint8)[None, :, None], 3, axis=2)
        original = imagem.copy()
        for gamma in (0.02, 0.5, 2, 10):
            resultado = ajustar_gama(imagem, gamma)
            self.assertEqual(resultado.dtype, np.uint8)
            self.assertEqual(resultado.shape, imagem.shape)
            self.assertTrue(np.all(np.diff(resultado[0, :, 0].astype(int)) >= 0))
        np.testing.assert_array_equal(imagem, original)

    def test_rejeita_gama_invalido(self):
        imagem = np.zeros((2, 2, 3), np.uint8)
        for gamma in (0, -1, float('nan'), float('inf')):
            with self.subTest(gamma=gamma), self.assertRaises(ValueError):
                ajustar_gama(imagem, gamma)


class OtimizacaoTests(unittest.TestCase):
    def test_correcao_nao_amplifica_pequenas_diferencas_de_cor(self):
        niveis = np.linspace(225, 250, 64).astype(np.uint8)
        imagem = np.stack((niveis - 3, niveis, niveis + 3), axis=1)[None, :, :]
        imagem = np.repeat(imagem, 64, axis=0)
        corrigida, _ = otimizar(imagem)
        antes = cv2.cvtColor(imagem, cv2.COLOR_BGR2YCrCb)[:, :, 1:].astype(int)
        depois = cv2.cvtColor(corrigida, cv2.COLOR_BGR2YCrCb)[:, :, 1:].astype(int)
        self.assertLessEqual(np.max(np.abs(depois - antes)), 3)

    def test_preserva_imagem_normal_exatamente(self):
        imagem = np.arange(100, 196, dtype=np.uint8).reshape(4, 8, 3)
        corrigida, info = otimizar(imagem)
        np.testing.assert_array_equal(corrigida, imagem)
        self.assertEqual(info['gamma'], 1)
        self.assertFalse(info['clahe'])

    def test_extremos_absolutos_nao_inventam_detalhes(self):
        for nivel in (0, 255):
            imagem = np.full((8, 8, 3), nivel, np.uint8)
            corrigida, info = otimizar(imagem)
            np.testing.assert_array_equal(corrigida, imagem)
            self.assertFalse(info['clahe'])

    def test_corrige_exemplos_reais_na_direcao_certa(self):
        for nome, diagnostico in [('image-1.png', 'superexposta'),
                                  ('image-2.png', 'subexposta')]:
            with self.subTest(nome=nome):
                imagem = cv2.imread(str(RAIZ / 'imagens' / nome))
                self.assertIsNotNone(imagem)
                original = imagem.copy()
                corrigida, info = otimizar(imagem)
                self.assertEqual(info['antes']['diagnostico'], diagnostico)
                self.assertLess(abs(info['depois']['media'] - 128),
                                abs(info['antes']['media'] - 128))
                self.assertEqual(corrigida.shape, imagem.shape)
                self.assertEqual(corrigida.dtype, np.uint8)
                self.assertTrue(info['clahe'])
                if diagnostico == 'subexposta':
                    self.assertGreater(info['gamma'], 1)
                else:
                    self.assertLess(info['gamma'], 1)
                np.testing.assert_array_equal(imagem, original)


if __name__ == '__main__':
    unittest.main()
