import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np


RAIZ = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def executar(self, *argumentos, cwd=None):
        return subprocess.run(
            [sys.executable, str(RAIZ / 'main.py'), *map(str, argumentos)],
            cwd=cwd, capture_output=True, text=True, check=False,
        )

    def test_processa_exemplos_de_outro_diretorio_e_salva_comparacoes(self):
        with tempfile.TemporaryDirectory() as pasta:
            resultado = self.executar('--saida', pasta, cwd=pasta)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            relatorio = json.loads((Path(pasta) / 'relatorio.json').read_text())
            self.assertEqual(len(relatorio), 2)
            self.assertIn('subexposta', resultado.stdout)
            self.assertIn('superexposta', resultado.stdout)
            for item in relatorio:
                original = cv2.imread(item['entrada'])
                corrigida = cv2.imread(item['corrigida'])
                comparacao = cv2.imread(item['comparacao'])
                self.assertEqual(corrigida.shape, original.shape)
                h, w = original.shape[:2]
                self.assertEqual(comparacao.shape[1], w * 2)
                np.testing.assert_array_equal(comparacao[-h:, :w], original)
                np.testing.assert_array_equal(comparacao[-h:, w:], corrigida)

    def test_arquivo_normal_e_preservado(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta) / 'foto.png'
            cv2.imwrite(str(entrada), np.full((20, 20, 3), 140, np.uint8))
            conteudo = entrada.read_bytes()
            resultado = self.executar(entrada, '--saida', Path(pasta) / 'saida')
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(entrada.read_bytes(), conteudo)
            np.testing.assert_array_equal(
                cv2.imread(str(Path(pasta) / 'saida/foto_corrigida.png')),
                cv2.imread(str(entrada)),
            )

    def test_entrada_ausente_ou_corrompida_retorna_erro_legivel(self):
        with tempfile.TemporaryDirectory() as pasta:
            corrompida = Path(pasta) / 'corrompida.png'
            corrompida.write_text('não é uma imagem')
            for entrada in (corrompida, Path(pasta) / 'ausente.png'):
                with self.subTest(entrada=entrada):
                    resultado = self.executar(entrada, '--saida', Path(pasta) / 'saida')
                    self.assertNotEqual(resultado.returncode, 0)
                    self.assertIn('Erro:', resultado.stderr)
                    self.assertNotIn('Traceback', resultado.stderr)

    def test_recusa_colisao_de_nomes(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = []
            for nome in ('a', 'b'):
                diretorio = Path(pasta) / nome
                diretorio.mkdir()
                arquivo = diretorio / 'foto.png'
                cv2.imwrite(str(arquivo), np.full((8, 8, 3), 32, np.uint8))
                arquivos.append(arquivo)
            resultado = self.executar(*arquivos, '--saida', Path(pasta) / 'saida')
            self.assertNotEqual(resultado.returncode, 0)
            self.assertIn('Erro:', resultado.stderr)

    def test_recusa_sobrescrever_qualquer_entrada(self):
        with tempfile.TemporaryDirectory() as pasta:
            entradas = [Path(pasta) / nome for nome in ('foto.png', 'foto_corrigida.png')]
            for entrada in entradas:
                cv2.imwrite(str(entrada), np.full((8, 8, 3), 32, np.uint8))
            originais = [entrada.read_bytes() for entrada in entradas]
            resultado = self.executar(*entradas, '--saida', pasta)
            self.assertNotEqual(resultado.returncode, 0)
            self.assertIn('Erro:', resultado.stderr)
            self.assertEqual([entrada.read_bytes() for entrada in entradas], originais)

    def test_saida_invalida_retorna_erro(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'arquivo'
            destino.write_text('ocupado')
            resultado = self.executar('--saida', destino)
            self.assertNotEqual(resultado.returncode, 0)
            self.assertIn('Erro:', resultado.stderr)
            self.assertNotIn('Traceback', resultado.stderr)

    def test_recusa_saida_que_e_hardlink_de_entrada(self):
        for nome in ('foto_corrigida.png', 'relatorio.json'):
            with self.subTest(nome=nome), tempfile.TemporaryDirectory() as pasta:
                entrada = Path(pasta) / 'foto.png'
                cv2.imwrite(str(entrada), np.full((8, 8, 3), 30, np.uint8))
                original = entrada.read_bytes()
                destino = Path(pasta) / 'saida'
                destino.mkdir()
                (destino / nome).hardlink_to(entrada)
                resultado = self.executar(entrada, '--saida', destino)
                self.assertNotEqual(resultado.returncode, 0)
                self.assertIn('Erro:', resultado.stderr)
                self.assertEqual(entrada.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
