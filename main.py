"""Interface de linha de comando do otimizador automático de imagens."""

import argparse
import json
from pathlib import Path
import sys

import cv2
import numpy as np

from otimizador import otimizar


RAIZ = Path(__file__).resolve().parent


def criar_comparacao(original: np.ndarray, corrigida: np.ndarray) -> np.ndarray:
    """Monta [Original | Corrigida] sem redimensionar os pixels."""
    largura = original.shape[1]
    cabecalho = np.full((48, largura * 2, 3), 28, dtype=np.uint8)
    escala = min(0.65, largura / 250)
    for texto, x in [('Original', 0), ('Corrigida', largura)]:
        cv2.putText(cabecalho, texto, (x + 8, 31), cv2.FONT_HERSHEY_SIMPLEX,
                    escala, (245, 245, 245), 1, cv2.LINE_AA)
    return np.vstack((cabecalho, np.hstack((original, corrigida))))


def _planejar_saidas(entradas: list[Path], destino: Path) -> list[tuple[Path, Path]]:
    saidas = [
        (destino / f'{entrada.stem}_corrigida.png',
         destino / f'{entrada.stem}_comparacao.png')
        for entrada in entradas
    ]
    caminhos = [caminho.resolve() for par in saidas for caminho in par]
    caminhos.append((destino / 'relatorio.json').resolve())
    if len(caminhos) != len(set(caminhos)):
        raise ValueError('Entradas com nomes iguais gerariam saídas em conflito.')
    originais = {entrada.resolve() for entrada in entradas}
    if originais.intersection(caminhos):
        raise ValueError('O destino sobrescreveria uma imagem de entrada.')
    existentes = [entrada for entrada in originais if entrada.exists()]
    for caminho in caminhos:
        if caminho.exists() and any(caminho.samefile(entrada) for entrada in existentes):
            raise ValueError('Uma saída aponta para o mesmo arquivo físico de uma entrada.')
    return saidas


def _salvar_imagem(caminho: Path, imagem: np.ndarray) -> None:
    if not cv2.imwrite(str(caminho), imagem):
        raise OSError(f'Não foi possível salvar a imagem: {caminho}')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Corrige automaticamente a exposição e salva comparações antes/depois.',
    )
    parser.add_argument('imagens', nargs='*', type=Path,
                        help='Arquivos de entrada. Por padrão, usa os PNGs em imagens/.')
    parser.add_argument('--saida', type=Path, default=RAIZ / 'resultados',
                        help='Diretório de saída (padrão: resultados/ do projeto).')
    args = parser.parse_args(argv)

    try:
        entradas = args.imagens or sorted((RAIZ / 'imagens').glob('*.png'))
        if not entradas:
            raise ValueError('Nenhuma imagem encontrada. Informe arquivos de entrada.')
        destino = args.saida.resolve()
        saidas = _planejar_saidas(entradas, destino)
        destino.mkdir(parents=True, exist_ok=True)
        relatorio = []
        for entrada, (corrigida_path, comparacao_path) in zip(entradas, saidas):
            if not entrada.is_file():
                raise ValueError(f'Arquivo de entrada não encontrado: {entrada}')
            original = cv2.imread(str(entrada), cv2.IMREAD_COLOR)
            if original is None:
                raise ValueError(f'Não foi possível ler a imagem: {entrada}')
            corrigida, info = otimizar(original)
            _salvar_imagem(corrigida_path, corrigida)
            _salvar_imagem(comparacao_path, criar_comparacao(original, corrigida))
            relatorio.append({
                'entrada': str(entrada.resolve()),
                'corrigida': str(corrigida_path),
                'comparacao': str(comparacao_path),
                **info,
            })
            diagnostico = info['antes']['diagnostico']
            if diagnostico == 'normal':
                correcao = 'Nenhuma (exposição normal)'
            else:
                acao = 'Clareamento' if diagnostico == 'subexposta' else 'Escurecimento'
                correcao = f'{acao}, gama={info["gamma"]:.4f}'
                if info['clahe']:
                    correcao += ' + contraste local (CLAHE)'
            print(f'\n{entrada.name} — {diagnostico}')
            print(f'  Correção: {correcao}')
            print(f'  Brilho médio: {info["antes"]["media"]:.2f}'
                  f' -> {info["depois"]["media"]:.2f} / 255')
            print(f'  Comparação: {comparacao_path}')
        (destino / 'relatorio.json').write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n', encoding='utf-8',
        )
        print(f'\nRelatório: {destino / "relatorio.json"}')
    except (OSError, ValueError, cv2.error) as erro:
        print(f'Erro: {erro}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
