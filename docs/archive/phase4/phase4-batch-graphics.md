# C121 — contexto gráfico com namespaces de arquivos separados

09/11/2026. Preparação offline e observação somente leitura, sem sessão gráfica
ou botões nesta rodada, conforme solicitação do usuário.

A revisão após a qualificação automática C120 encontrou uma colisão no harness
pendente: o nome `NAMES` representava seis arquivos do bundle, mas o contexto
gráfico esperava quatro bibliotecas do provider. O caminho errado falharia na
montagem do contexto local antes do despacho. Nenhum ciclo gráfico foi
executado com esse harness e isso não afeta os quinze recibos nativos C120.
As fontes e a prova C120 permanecem congeladas.

O adaptador próprio `phase4_batch_graphics.py` fornece ao executor os quatro
nomes do provider C116. O módulo de contrato C120 mantém sua lista de seis
arquivos para gerar/verificar o bundle; seus globais não são alterados. O
entrypoint para o futuro ciclo passa a ser `run-phase4-batch-graphics.py`.
Não usar o harness gráfico direto `run-phase4-batch-run.py` para esse ciclo.

O adaptador exige a prova pública C120, a análise nativa privada e seus checks,
fontes e bundle exatos, com todos os recibos de fechamento. Observação e
sessão recebem hashes explícitos desses pais; uma observação com vínculo
incorreto é recusada antes da preparação/despacho. Guard191, contador/UUID,
worker, provider, limites240/210/45s, load-only e coleta/cleanup são preservados.
Continua usando a preparação residente e ROM interna, sem uploads de inputs.

Oito testes offline em `batch-graphics/checks.kkoqulgn` passaram. Executam os
loops reais do código gerado com os quatro arquivos qualificados do provider,
verificam hashes/mapa e a ausência de nomes do bundle nesse mapa. Executam o
loop de upload com todos os leitores/transporte proibidos e zero inputs;
executam também as duas admissões de observação, com caso positivo e recusas
por análise/prova C120 divergentes. Não abrem a ROM local nem usam a rede.

Observação nativa `batch-graphics/observe.t97ip2u4`, mesmo boot83/IP13, passou
os dois recibos SSH0 de preflight/boot-evidence com guard191 e infraestrutura.
Ela apenas confere guard/identidade/infraestrutura, sem preparar
cápsula, copiar bundle, montar dados, iniciar UI ou executar run. Não publicar
`dist/phase4/batch-graphics` como confirmação gráfica antes do ciclo efetivo e
da coleta técnica/física/fechamento correspondentes.

Os adaptadores `analyze-phase4-batch-graphics.py` e
`finish-phase4-batch-graphics.py` também estão preparados, derivados das fontes
congeladas C109/C77 com admissão explícita da área C121, schema121 e UUID
observado. Parse/CLI help e recusa do estágio nativo não gráfico C120 passaram;
não foram usados para fabricar uma análise ou fechamento de sessão inexistente.
Análise completa de frames/áudio/timing e fechamento desses recibos só podem
ser qualificados quando uma sessão gráfica real for coletada.

Próximo: confirmar disponibilidade do usuário e estado atual; se boot/IP ou
fontes mudarem, criar observação nova. Depois uma única rodada
A/Start/direcional/Fn+L2/Fn+Start e medição seleção→primeiro frame, sem save,
Power, volume ou brilho. Não há ganho de abertura ou confirmação acústica nova
neste incremento. Original32, Deck, imagens e SDK permanecem preservados.
