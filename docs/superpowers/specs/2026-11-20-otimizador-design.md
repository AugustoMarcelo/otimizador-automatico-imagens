# Otimizador automático de imagens

Implementar o desafio da Rocketseat com Python, NumPy e OpenCV, usando as
duas imagens fornecidas: floresta subexposta e praia superexposta.

## Arquitetura e decisões

- `otimizador.py`: diagnóstico, LUT gama e processamento automático puro.
- `main.py`: CLI, leitura, gravação, comparação e relatório JSON.
- `imagens/`: arquivos originais, preservando seus nomes e bytes.
- `resultados/`: PNGs corrigidos, comparações e métricas geradas.
- `tests/`: testes com unittest, sem dependências extras.

Classificar pela média em cinza: abaixo de 100 é subexposta, acima de 200
é superexposta; inclusive entre esses valores, preservar integralmente.
Calcular também histograma de 256 níveis com OpenCV. Selecionar gama por
busca binária sobre o histograma para aproximar o brilho de 128, limitado
a [0.02, 10]. Implementar a LUT com float32, potência NumPy, clip e uint8.
Aplicar gama e CLAHE moderado no canal Y do YCrCb, para exposição e contraste
local, exceto em imagens constantes. Não prometer recuperar informação
que já foi perdida por saturação. A inspeção visual do primeiro pipeline,
que aplicava gama em BGR, revelou cores artificiais; a correção apenas de
luminância mantém Cr/Cb e evita amplificar diferenças pequenas entre canais.

## Alternativas consideradas

Gama fixo seria mais curto, porém ignora a severidade da exposição.
Equalização global isolada não exercita a correção gama exigida e pode
exagerar o contraste. Escolha técnica: gama adaptativo e CLAHE limitado.

## Interface e erros

`python main.py` processa os exemplos independentemente do diretório atual.
Arquivos posicionais permitem outras entradas; `--saida` define o destino.
Salvar original à esquerda e corrigida à direita, com legendas, sem GUI.
Imprimir diagnóstico, gama e médias antes/depois; salvar relatório JSON.
Falhas de leitura/gravação devem produzir mensagem em português e saída
não zero. Recusar nomes de saída em conflito e qualquer saída que
sobrescreva uma entrada. Não publicar em GitHub ou LinkedIn.

## Verificação

Testar limiares, sentido e monotonicidade da LUT, tipos, gama inválido,
imagens neutras e extremas, resultados nas duas imagens reais e CLI com
arquivos inválidos, colisões e execução em outro diretório. Inspecionar
visualmente as comparações geradas.
