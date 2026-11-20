# Plano de implementação do otimizador

> Execução: implementar diretamente nesta sessão, tarefa a tarefa.

**Objetivo:** entregar o script do desafio com exemplos processados.
**Arquitetura:** módulo de processamento separado da CLI e operações em disco.
**Stack:** Python >= 3.10, NumPy, opencv-python e unittest da biblioteca padrão.
**Spec:** `docs/superpowers/specs/2026-11-20-otimizador-design.md`.

## Restrições globais

Somente NumPy/OpenCV como dependências externas. Manter originais intactos.
Média < 100: subexposta; média > 200: superexposta; demais: normal.
Gama NumPy com LUT uint8 e cv2.LUT. Comparação antes/depois salva em PNG.

## Pontos de revisão

Imagens constantes, limiares exatos, entradas corrompidas, colisões entre
nomes de saída e entradas, funcionamento sem interface gráfica.

## Tarefa 1: processamento

- [x] Criar testes de `diagnosticar`, `ajustar_gama` e `otimizar` em
  `tests/test_otimizador.py`; observar falha antes da implementação.
- [x] Implementar em `otimizador.py`: `diagnosticar(imagem) -> dict`,
  `ajustar_gama(imagem, gamma=1.0) -> ndarray`,
  `otimizar(imagem) -> tuple[ndarray, dict]`.
- [x] Confirmar preservação de normais, robustez nos extremos e melhoria
  da exposição nas imagens reais. Executar unittest.

## Tarefa 2: CLI e entrega

- [x] Criar testes de integração em `tests/test_cli.py`; observar falha.
- [x] Implementar `main.py`: entradas opcionais, `--saida`, PNG comparativo,
  relatório JSON, erros e proteção de originais.
- [x] Organizar exemplos em `imagens/`, adicionar requirements e gitignore.
- [x] Executar CLI e inspecionar comparações; documentar instalação,
  algoritmo, limitações, execução, testes e resultados em README.md.
- [x] Revisar código com deslop, rodar todos os testes e validar saídas.

## Registro

Repositório inicialmente inexistente, contendo somente duas imagens.
Implementação autorizada pelo pedido direto do usuário; não é necessário
criar worktree ou commits. Nenhuma publicação externa foi solicitada.

Verificação: 16 testes unittest, execução completa nas imagens reais e
inspeção visual das comparações. Revisão independente encontrou colisão
por hard link; reproduzida em teste antes da correção e resolvida com
verificação de identidade física dos arquivos antes de qualquer gravação.
Revisão deslop manteve apenas dois módulos focados e testes de comportamento.
